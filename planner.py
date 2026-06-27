import json
from langchain_ollama import ChatOllama

class Planner:

    def __init__(self):

        self.llm = ChatOllama(
            model="qwen2.5:7b",
            temperature=0
        )

    def plan(self, task):

        prompt = f"""
You are an AI planner.

Convert the user's request into a JSON array.

Example

User:
Open YouTube and search Ollama

Output:

[
 {{
   "action":"open",
   "website":"youtube"
 }},
 {{
   "action":"search",
   "query":"ollama"
 }}
]

User:

{task}

Return ONLY JSON.
"""
        response = self.llm.invoke(prompt)

        #print("\n========== RAW AI RESPONSE ==========\n")
        #print(response.content)
        #print("\n====================================\n")

        return json.loads(response.content)