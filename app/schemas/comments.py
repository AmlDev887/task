from pydantic import BaseModel

class CommentCreate(BaseModel):

    task_id: int
    author_id:int
    body:str

class CommentUpdate(BaseModel):

    body_update: str