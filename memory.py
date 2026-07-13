class Memory:
    def __init__(self):
        self.task = ""
        self.history = []

    def set_task(self, task):
        self.task = task
        self.history = []

    def add_step(self, thought, action, result):
        self.history.append({
            "thought": thought,
            "action": action,
            "result": result
        })

    def get_history(self):
        return self.history

    def get_last_action(self):
        if self.history:
            return self.history[-1]["action"]
        return None
