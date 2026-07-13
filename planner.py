import json
import re
from langchain_ollama import ChatOllama
from prompts import SYSTEM_PROMPT, get_planner_prompt

def clean_json_backslashes(content):
    r"""Escapes single backslashes in Windows paths (like C:\Users) while keeping standard escapes."""
    fixed = []
    i = 0
    while i < len(content):
        if content[i] == '\\':
            if i + 1 < len(content):
                next_char = content[i+1]
                if next_char in ('\\', '"'):
                    fixed.append('\\' + next_char)
                    i += 2
                    continue
            fixed.append('\\\\')
            i += 1
        else:
            fixed.append(content[i])
            i += 1
    return "".join(fixed)

class Planner:
    def __init__(self, model_name="qwen2.5:7b"):
        self.llm = ChatOllama(
            model=model_name,
            temperature=0
        )

    def plan_step(self, task, browser_state, desktop_state, history):
        """Generates the next action for the agent to execute."""
        system_msg = SYSTEM_PROMPT
        user_msg = get_planner_prompt(task, browser_state, desktop_state, history)
        
        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg}
        ]
        
        try:
            response = self.llm.invoke(messages)
            content = response.content.strip()
            
            # Clean markdown code blocks if the model outputs them
            cleaned_content = content
            if "```" in content:
                # Try to extract the JSON block
                match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
                if match:
                    cleaned_content = match.group(1).strip()
                else:
                    cleaned_content = content.replace("```json", "").replace("```", "").strip()
            
            # Clean single backslashes from Windows paths inside the JSON string
            cleaned_content = clean_json_backslashes(cleaned_content)
            
            # Parse JSON
            try:
                plan = json.loads(cleaned_content)
                if isinstance(plan, dict) and isinstance(plan.get("action"), dict):
                    nested = plan["action"]
                    for k, v in nested.items():
                        plan[k] = v
                return plan
            except json.JSONDecodeError as e:
                # Attempt to salvage substring JSON
                start = cleaned_content.find('{')
                end = cleaned_content.rfind('}')
                if start != -1 and end != -1:
                    try:
                        plan = json.loads(cleaned_content[start:end+1])
                        if isinstance(plan, dict) and isinstance(plan.get("action"), dict):
                            nested = plan["action"]
                            for k, v in nested.items():
                                plan[k] = v
                        return plan
                    except json.JSONDecodeError:
                        pass
                
                return {
                    "thoughts": f"Failed to parse LLM JSON: {e}. Raw content: {content}",
                    "action": "finish",
                    "message": f"LLM output error: {content}"
                }
        except Exception as e:
            return {
                "thoughts": f"LLM call failed: {e}",
                "action": "finish",
                "message": f"LLM execution failed: {str(e)}"
            }