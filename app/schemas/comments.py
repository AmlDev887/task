from pydantic import BaseModel,ConfigDict,EmailStr
from typing import Optional
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
    id: int
    title: str
    created_at: Optional[datetime] = None
    description: str | None = None
    status: roles.TaskStatus
    priority: roles.TaskPriority
    due_date: date | None = None
    completed_at: datetime | None = None
    is_deleted: bool
    version: int
    
    comment: list[CommentScheme]

    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore" 
    )

class CommentsResponse(BaseModel):
    
    id: int | None
    body: str | None
    task_name: str | None
    receipt: str | None
    email: list[EmailStr] | None = None

class CommenstSearchResponse(BaseModel):
    body: list[dict]