from pydantic import BaseModel, ConfigDict
from app.schemas import tasks
from typing import Optional, Union

class HistorySchemeResponse(BaseModel):

    id: int
    user_name: str
    task_name: str
    field: str
    old_value: Optional[Union[str, int, float, bool]] = None
    new_value: Optional[Union[str, int, float, bool]] = None

    model_config = ConfigDict(from_attributes=True)
