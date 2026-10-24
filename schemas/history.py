from pydantic import BaseModel, Field, EmailStr, ConfigDict
from database.roles import TaskStatus,TaskPriority, OrderRoleUser
from datetime import datetime,date
from typing import Optional
from schemas import tasks

class HistorySchemeResponse(BaseModel):
    user_id: tasks.UsersTasks
    task_id: tasks.TaskUpdate
    field: str
    old_value: str
    new_value: str

    modelconfig = ConfigDict(from_attributes=True)
