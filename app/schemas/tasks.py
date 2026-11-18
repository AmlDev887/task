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

class UserShortResponse(BaseModel):
    id: int
    full_name: str

    model_config = ConfigDict(from_attributes=True)


class ProjectShortResponse(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)

class TaskResponse(BaseModel):
   
    id: int
    title: str
    description: str | None
    status: roles.TaskStatus
    priority: roles.TaskPriority
    due_date: date | None
    project_id: int
    creator_id: int
    assignee_id: int | None
    completed_at: datetime | None
    version: int

    creator: UserShortResponse
    assignee: Optional[UserShortResponse]
    project: ProjectShortResponse
    
    model_config = ConfigDict(from_attributes=True)

#------------------- PATCH REQUEST TASKS ------------------------

class TaskUpdate(BaseModel):

    version: int
    assignee_id:Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[date] = None
    status: roles.TaskStatus | None = None
    priority: roles.TaskPriority | None = None


class TaskCommentCreate(BaseModel):
    body:str

class SearchResponse(BaseModel):
    
    search: Optional[str] = None
    status: Optional[roles.TaskStatus] = None
    priority:Optional[roles.TaskPriority] = None
    project_id:Optional[int] = None
    assignee_id:Optional[int] = None
    deadline_from:Optional[datetime] = None
    deadline_to:Optional[datetime] = None
    sort_by: Optional[roles.TaskSortBy] = None
    order: Optional[roles.SortOrder] = roles.SortOrder.ASC

class Page(BaseModel):
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)


class PagedTasks(BaseModel):
    items: list[TaskResponse]  # Сюда попадет список задач (по твоей схеме TaskResponse)
    total: int                 # Всего найдено задач в базе
    page: int                  # Текущая страница
    size: int                  # Размер страницы
    pages: int                 # Всего страниц
    
    model_config = ConfigDict(from_attributes=True)