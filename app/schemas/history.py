from pydantic import BaseModel, ConfigDict
from app.schemas import tasks

class HistorySchemeResponse(BaseModel):

    id: int
    user_name: str
    task_name: str
    field: str
    old_value: str
    new_value: str

    model_config = ConfigDict(from_attributes=True)
