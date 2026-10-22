from pydantic import BaseModel, Field, EmailStr

class UserLogin(BaseModel):
    email: EmailStr | None = None
    full_name: str  = Field(min_length=2, max_length=60)
    password: str = Field(min_length=8)

class RefreshToken(BaseModel):
    refresh_token : str
    token_type: str
