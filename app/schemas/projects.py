from pydantic import BaseModel, Field

class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=225)
    owner_id:int

class ProjectResponse(BaseModel):
    name:str
    description:str 
    owner_id:int

class CreateOwner(BaseModel):
    user_id:int