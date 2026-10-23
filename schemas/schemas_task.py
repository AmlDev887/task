from pydantic import BaseModel, Field, EmailStr, ConfigDict
from database.roles import TaskStatus,TaskPriority, OrderRoleUser
from datetime import datetime,date
from typing import Optional

class TaskScheme(BaseModel):
    title:str
    description:Optional[str] = None
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.LOW
    due_date: date | None = None
    assignee_id: int | None = None

class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=225)


#------------------GET  запрос TASK---------------------------------
class UsersTasks(BaseModel):
    id: int
    full_name: str

    model_config = ConfigDict(from_attributes=True)

class ProjectTask(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)

class TaskResponse(BaseModel):
    user:UsersTasks 
    project: ProjectTask
    title:str
    description:Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

#------------------- PATCH REQUEST TASKS ------------------------

class TaskUpdate(BaseModel):
    id: int
    title: str
    description: str
    
    