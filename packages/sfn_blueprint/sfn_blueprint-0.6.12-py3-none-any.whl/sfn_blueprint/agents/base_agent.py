class SFNAgent:
    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role

    def execute_task(self, task):
        raise NotImplementedError("Subclasses must implement execute_task method")