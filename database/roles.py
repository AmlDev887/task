from enum import Enum

class OrderRoleUser(Enum):
    ADMIN = "admin"
    USER = "user"

class TaskStatus(Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class EmailTokensEnum(Enum):
    VERIFY = "verify"
    RESET = "reset"

