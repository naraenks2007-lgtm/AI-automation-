import sys
import time
from planner import Planner
from validator import Validator
from executor import Executor
from memory import Memory

def run_agent(task, model_name="qwen2.5:7b", callback=None, abort_event=None):
    """Programmatic agent runner that executes the task and sends step updates to callback."""
    print(f"Initializing Planner with model: {model_name}...")
    try:
        planner = Planner(model_name=model_name)
    except Exception as e:
        err_msg = f"Failed to initialize ChatOllama model '{model_name}': {e}. Is Ollama running?"
        print(err_msg)
        if callback:
            callback({
                "step": 0,
                "thoughts": "Ollama initialization error.",
                "action": "error",
                "result": err_msg
            })
        return
        
    validator = Validator()
    executor = Executor()
    memory = Memory()
    
    memory.set_task(task)
    max_steps = 25
    step_num = 1
    
    # Capture initial screenshot before doing anything
    executor.capture_screenshot()
    
    try:
        while step_num <= max_steps:
            # Check abort event
            if abort_event and abort_event.is_set():
                print("Abort event detected. Terminating execution loop.")
                if callback:
                    callback({
                        "step": step_num,
                        "thoughts": "Task execution aborted by user request.",
                        "action": "finish",
                        "result": "Execution stopped."
                    })
                break
                
            print(f"\n--- STEP {step_num} ---")
            
            # Gather state
            browser_state = executor.get_browser_state()
            desktop_state = executor.get_desktop_state()
            history = memory.get_history()
            
            # Plan next action
            step_plan = planner.plan_step(task, browser_state, desktop_state, history)
            thoughts = step_plan.get("thoughts", "No thoughts provided.")
            
            # Validate action
            is_valid, validation_msg = validator.validate_step(step_plan)
            if not is_valid:
                print(f"Validation Error: {validation_msg}")
                # Record error in memory history for self-correction
                memory.add_step(
                    thought=thoughts,
                    action=step_plan.get("action", "unknown"),
                    result=f"Action validation failed: {validation_msg}. Please correct the action schema."
                )
                if callback:
                    callback({
                        "step": step_num,
                        "thoughts": thoughts,
                        "action": step_plan.get("action", "unknown"),
                        "result": f"Action validation failed: {validation_msg}."
                    })
                step_num += 1
                continue
                
            action = step_plan["action"]
            
            # Execute action
            print(f"Action: {action}")
            result = executor.execute(step_plan)
            print(f"Result: {result}")
            
            # Record step outcome in memory
            memory.add_step(
                thought=thoughts,
                action=action,
                result=result
            )
            
            # Invoke callback with current step information
            if callback:
                callback({
                    "step": step_num,
                    "thoughts": thoughts,
                    "action": action,
                    "result": result
                })
            
            # Check if finished
            if action == "finish":
                break
                
            step_num += 1
            time.sleep(1.5)  # Buffer sleep between actions
            
        else:
            print("\nReached maximum step limit.")
            if callback:
                callback({
                    "step": step_num,
                    "thoughts": "Maximum execution steps reached.",
                    "action": "finish",
                    "result": "Max steps limit reached."
                })
                
    except KeyboardInterrupt:
        print("\nExecution interrupted by user.")
    except Exception as e:
        import traceback
        print("\nAn error occurred during execution:")
        traceback.print_exc()
        if callback:
            callback({
                "step": step_num,
                "thoughts": "An exception occurred.",
                "action": "error",
                "result": str(e)
            })
    finally:
        print("\nCleaning up resources...")
        executor.close()
        print("Done.")

def main():
    print("==================================================")
    print("      LOCAL AI WEB & DESKTOP AUTOMATION AGENT     ")
    print("==================================================")
    
    task = input("\nWhat task would you like me to do? ")
    if not task.strip():
        print("Empty task. Exiting.")
        sys.exit(0)
        
    def console_callback(data):
        print(f"  Step callback: {data['step']} | Action: {data['action']}")
        
    run_agent(task, model_name="qwen2.5:7b", callback=console_callback)

if __name__ == "__main__":
    main()