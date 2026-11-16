from pydantic import BaseModel, Field

class RefreshToken(BaseModel):
    refresh_token : str
    token_type: str
