from pydantic import BaseModel, Field, EmailStr

class AddUser(BaseModel):
    id:int
    email:EmailStr
    full_name:str

class UserLogin(BaseModel):
    email: EmailStr | None = None
    full_name: str  = Field(min_length=2, max_length=60)
    password: str = Field(min_length=8)

class User(BaseModel):
    email:EmailStr
    full_name:str
    hashed_password:str
    is_verified:bool