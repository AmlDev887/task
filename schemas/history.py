from pydantic import BaseModel, Field, EmailStr, ConfigDict
from database.roles import TaskStatus,TaskPriority, OrderRoleUser
from datetime import datetime,date
from typing import Optional

class TaskRestore(BaseModel):

    