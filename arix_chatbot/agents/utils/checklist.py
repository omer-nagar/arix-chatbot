from typing import Dict, List, Iterator


class TaskStatus:
    TODO = "TODO"
    WAIT_HUMAN = "WAIT_HUMAN"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "COMPLETED"
    ERROR = "ERROR"


class Checklist:
    def __init__(self, tasks: List[str] = None):
        # use dict to preserve insertion order (guaranteed in Python 3.7+)
        self.tasks: Dict[str, str] = {
            task: TaskStatus.TODO for task in (tasks or [])
        }

    def all_completed(self) -> bool:
        return all(status == TaskStatus.DONE for status in self.tasks.values())

    def is_done(self, task_id: str) -> bool:
        return self.tasks.get(task_id) == TaskStatus.DONE

    def is_errors(self) -> bool:
        return any(status == TaskStatus.ERROR for status in self.tasks.values())

    def is_waiting_human(self) -> bool:
        return any(status == TaskStatus.WAIT_HUMAN for status in self.tasks.values())

    def set_status(self, task_id: str, status: str):
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found in checklist.")
        self.tasks[task_id] = status

    def get_state(self, task_id: str) -> str:
        return self.tasks.get(task_id)

    def set_todo(self, task_id: str):
        self.tasks[task_id] = TaskStatus.TODO

    def set_in_progress(self, task_id: str):
        self.tasks[task_id] = TaskStatus.IN_PROGRESS

    def set_done(self, task_id: str):
        self.tasks[task_id] = TaskStatus.DONE

    def summary(self) -> str:
        total = len(self.tasks)
        done = sum(s == TaskStatus.DONE for s in self.tasks.values())
        return f"{done}/{total} tasks completed"

    def todict(self) -> Dict:
        return self.tasks

    @staticmethod
    def fromdict(tasks):
        cl = Checklist()
        cl.tasks = tasks
        return cl

    def __iter__(self) -> Iterator:
        """Iterate over (task_id, status) pairs in insertion order."""
        return iter(self.tasks.items())

    def __repr__(self) -> str:
        return "\n".join(f"[{status}] {task}" for task, status in self.tasks.items())
