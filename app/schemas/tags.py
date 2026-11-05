from pydantic import BaseModel
from typing import Optional
class CreateTag(BaseModel):
    
    name:str
    color:str

class ResponseTag(BaseModel):

    name:str
    color:str

class UpdateTag(BaseModel):
    id:int
    name:Optional[str] = None 
    color:Optional[str] = None
    