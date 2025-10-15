from datetime import datetime
from typing import List
from .models import Task, User, Project, Priority
from .storage import InMemoryStorage


class TaskService:
    def __init__(self, storage: InMemoryStorage):
        self.storage = storage

    def create_task(
        self, task_id: int, title: str, desc: str,
        priority: Priority, deadline: datetime,
        project_id: int, user_id: int | None = None
    ) -> Task:
        user = self.storage.users.get(user_id) if user_id else None
        task = Task(
            id=task_id,
            title=title,
            description=desc,
            priority=priority,
            deadline=deadline,
            assigned_to=user,
        )
        self.storage.add_task(task, project_id)
        return task

    def mark_completed(self, task_id: int):
        if task_id not in self.storage.tasks:
            raise ValueError("Task not found")
        self.storage.tasks[task_id].completed = True

    def overdue_tasks(self) -> List[Task]:
        now = datetime.now()
        return [
            t for t in self.storage.tasks.values()
            if not t.completed and t.deadline < now
        ]

    def tasks_for_user(self, user_id: int) -> List[Task]:
        return [t for t in self.storage.tasks.values()
                if t.assigned_to and t.assigned_to.id == user_id]

    def high_priority_tasks(self) -> List[Task]:
        return [t for t in self.storage.tasks.values()
                if t.priority == Priority.HIGH and not t.completed]
