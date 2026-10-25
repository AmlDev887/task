from pydantic import BaseModel, Field, EmailStr, ConfigDict
from database.roles import TaskStatus,TaskPriority, OrderRoleUser
from datetime import datetime,date
from typing import Optional


class AddUser(BaseModel):
    id:int
    email:EmailStr
    full_name:str
    