from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List


class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


@dataclass
class User:
    id: int
    name: str


@dataclass
class Task:
    id: int
    title: str
    description: str
    priority: Priority
    deadline: datetime
    assigned_to: User | None = None
    completed: bool = False


@dataclass
class Project:
    id: int
    name: str
    tasks: List[Task] = field(default_factory=list)
