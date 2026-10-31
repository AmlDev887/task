from pydantic import BaseModel, Field, ConfigDict
from app.schemas.roles import TaskStatus,TaskPriority
from datetime import date
from typing import Optional

class TaskScheme(BaseModel):
    title:str
    description:Optional[str] = None
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.LOW
    due_date: date | None = None
    assignee_id: int | None = None

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
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None


class TaskCommentCreate(BaseModel):

    task_id: int
    author_id:int
    body:str
    