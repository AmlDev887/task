from pydantic import BaseModel, Field, EmailStr, ConfigDict
from app.schemas import roles
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
#------------------User Response GET----------------------------------
class UserProjectResponse(BaseModel):
    name:set
    description:str

    odel_config = ConfigDict(from_attributes=True)

class UserResponse(BaseModel):
    email:EmailStr
    full_name:str
    role:roles.OrderRoleUser
    is_active:bool
    is_verified:bool
    project:UserProjectResponse

    model_config = ConfigDict(from_attributes=True)

    