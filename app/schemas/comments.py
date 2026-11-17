from pydantic import BaseModel,ConfigDict,EmailStr
from app.schemas import roles
from datetime import date,datetime
from typing import List
class CommentCreate(BaseModel):

    task_id: int
    author_id:int
    body:str

class CommentUpdate(BaseModel):

    body: str | None 
class CommentScheme(BaseModel):
    id: int
    task_id: int
    author_id: int
    body: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CommentResponse(BaseModel):
    title: str
    description: str | None
    status: roles.TaskStatus
    priority: roles.TaskPriority
    due_date: date | None
    completed_at: datetime | None
    is_deleted: bool
    version: int

    comments: list[CommentScheme]

    model_config = ConfigDict(from_attributes=True)

class CommentsResponse(BaseModel):
    
    id: int | None
    body: str | None
    task_name: str | None
    receipt: str | None
    email: list[EmailStr] | None = None

class CommenstSearchResponse(BaseModel):
    body: list[dict]