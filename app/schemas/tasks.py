from pydantic import BaseModel, Field, ConfigDict
from app.schemas import roles
from datetime import date
from typing import Optional
from datetime import datetime

class TaskScheme(BaseModel):
    title:str
    description:Optional[str] = None
    status: roles.TaskStatus = roles.TaskStatus.TODO
    priority: roles.TaskPriority = roles.TaskPriority.LOW
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
    project: ProjectTask
    title:str
    description:Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

#------------------- PATCH REQUEST TASKS ------------------------

class TaskUpdate(BaseModel):

    assignee_id:Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[date] = None
    assignee_id: Optional[int] = None
    status: Optional[str] = None
    priority: Optional[str] = None


class TaskCommentCreate(BaseModel):

    task_id: int
    body:str

class SearchResponse(BaseModel):
    
    search: Optional[str] = None
    status: Optional[roles.TaskStatus] = None
    priority:Optional[roles.TaskPriority] = None
    project_id:Optional[int] = None
    assignee_id:Optional[int] = None
    deadline_from:Optional[datetime] = None
    deadline_to:Optional[datetime] = None

