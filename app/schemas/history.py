from pydantic import BaseModel, ConfigDict
from app.schemas import tasks

class HistorySchemeResponse(BaseModel):
    user_id: tasks.UsersTasks
    task_id: tasks.TaskUpdate
    field: str
    old_value: str
    new_value: str

    modelconfig = ConfigDict(from_attributes=True)
