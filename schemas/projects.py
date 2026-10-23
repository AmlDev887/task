from pydantic import BaseModel, Field, EmailStr, ConfigDict
from database.roles import TaskStatus,TaskPriority, OrderRoleUser
from datetime import datetime,date
from typing import Optional

class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=225)