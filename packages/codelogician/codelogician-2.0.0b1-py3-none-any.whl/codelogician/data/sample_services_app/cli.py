from datetime import datetime, timedelta
from .models import User, Project, Priority
from .storage import InMemoryStorage
from .services import TaskService


def run_cli():
    storage = InMemoryStorage()
    service = TaskService(storage)

    # Setup demo data
    user = User(id=1, name="Alice")
    project = Project(id=1, name="Sample Project")
    storage.add_user(user)
    storage.add_project(project)

    # Add a few tasks
    service.create_task(
        1, "Finish report", "Complete the quarterly report",
        Priority.HIGH, datetime.now() + timedelta(days=1),
        project_id=1, user_id=1
    )
    service.create_task(
        2, "Email client", "Send update to client",
        Priority.MEDIUM, datetime.now() - timedelta(days=2),
        project_id=1, user_id=1
    )

    print("== All Tasks ==")
    for t in storage.tasks.values():
        print(f"- {t.title} (priority: {t.priority.name}, deadline: {t.deadline}, completed: {t.completed})")

    print("\n== Overdue Tasks ==")
    for t in service.overdue_tasks():
        print(f"- {t.title} (deadline: {t.deadline})")

    print("\n== High Priority Tasks ==")
    for t in service.high_priority_tasks():
        print(f"- {t.title}")
