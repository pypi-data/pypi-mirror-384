from typing import Dict
from .models import User, Project, Task


class InMemoryStorage:
    def __init__(self):
        self.users: Dict[int, User] = {}
        self.projects: Dict[int, Project] = {}
        self.tasks: Dict[int, Task] = {}

    def add_user(self, user: User):
        self.users[user.id] = user

    def add_project(self, project: Project):
        self.projects[project.id] = project

    def add_task(self, task: Task, project_id: int):
        self.tasks[task.id] = task
        if project_id in self.projects:
            self.projects[project_id].tasks.append(task)
