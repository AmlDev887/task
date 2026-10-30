from pydantic import BaseModel, Field, ConfigDict, field_validator
from app.schemas import roles
from datetime import date
from typing import Optional

class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=225)
    owner_id:int

class ProjectResponse(BaseModel):
    name:str
    description:str 
    owner_id:int

class CreateOwner(BaseModel):
    user_id:str
    owner_id:roles.ProjectRole

class ProjectOwnerDelete(BaseModel):
    member_id: int

class ProjectTask(BaseModel):
    project_id: int
    status:dict[str,int]

class ProjectTaskUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid",str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=225)
    status: roles.TaskStatus = roles.TaskStatus.TODO
    priority: roles.TaskPriority = roles.TaskPriority.MEDIUM
    due_date: date
    project_id: int = Field(gt=0)
    assignee_id: Optional[int] = Field(default=None, gt=0)

    @field_validator("title")
    @classmethod
    def validate(cls, value: str):
        if not value:
            raise ValueError("Название задачи не может быть пустым")
        return value

    @field_validator("description")
    @classmethod
    def validate_description(cls,value: Optional[str]):
        if value is not None:
            return value or None
        return value

class ProjectTaskResponse(BaseModel):
    title: str
    description: str | None
    status: str
    priority: str
    due_date: date | None
    project_id: int
    assignee_id: int | None
    