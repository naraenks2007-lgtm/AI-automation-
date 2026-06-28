class Validator:
    VALID_ACTIONS = {
        "web_open": ["url"],
        "web_click": ["element_id"],
        "web_type": ["element_id", "text"],
        "web_press_key": ["key"],
        "web_go_back": [],
        "web_wait": ["seconds"],
        "desktop_open_app": ["command"],
        "desktop_type": ["text"],
        "desktop_press_key": ["key"],
        "desktop_hotkey": ["keys"],
        "desktop_wait": ["seconds"],
        "run_shell": ["command"],
        "read_file": ["filepath"],
        "write_file": ["filepath", "content"],
        "file_action": ["operation"],
        "finish": ["message"]
    }

    def validate_step(self, step):
        """Validates that a step contains a valid action and its required fields.
        
        Returns (is_valid, error_message/success_message).
        """
        if not isinstance(step, dict):
            return False, "Plan step must be a JSON dictionary object."
            
        if "action" not in step:
            return False, "Missing 'action' key in the plan step."
            
        action = step["action"]
        if action not in self.VALID_ACTIONS:
            return False, f"Unknown action '{action}'. Valid actions are: {list(self.VALID_ACTIONS.keys())}"
            
        # Check required fields
        required_fields = self.VALID_ACTIONS[action]
        for field in required_fields:
            if field not in step or step[field] is None:
                return False, f"Missing required parameter '{field}' for action '{action}'."
                
        # Specific type validations
        if action == "desktop_hotkey":
            if not isinstance(step["keys"], list):
                return False, "Parameter 'keys' must be a list of strings (e.g. ['ctrl', 's'])."
        
        if action in ("web_wait", "desktop_wait"):
            try:
                float(step["seconds"])
            except ValueError:
                return False, "Parameter 'seconds' must be a number."
                
        if action == "file_action":
            op = step.get("operation")
            valid_ops = ["copy", "move", "delete", "list", "create_directory"]
            if op not in valid_ops:
                return False, f"Invalid operation '{op}' for file_action. Allowed operations are: {valid_ops}"
            if op in ("copy", "move"):
                if "source" not in step or "destination" not in step:
                    return False, f"Operation '{op}' requires both 'source' and 'destination' paths."
            if op in ("delete", "list", "create_directory"):
                if "path" not in step:
                    return False, f"Operation '{op}' requires 'path' parameter."
        return True, "Valid action"