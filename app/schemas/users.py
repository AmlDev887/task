from pydantic import BaseModel, Field, EmailStr, ConfigDict, field_validator
from app.schemas import roles
from typing import List
class AddUser(BaseModel):
    id:int
    email:EmailStr
    full_name:str

    model_config = ConfigDict(from_attributes=True)
    
class UserLogin(BaseModel):
    email: EmailStr
    full_name: str  = Field(min_length=2, max_length=60)
    password: str = Field(min_length=8)

    @field_validator("password")
    @classmethod
    def scanner_password(cls,value):
        """Проверка пароля на присутвие букв и цифр"""
        
        if not any(char.isalpha() for char in value):
            raise ValueError("В пароле должна быть хотя бы одна буква")
        if not any(char.isdigit() for char in value):
            raise ValueError("В пароле должна быть хотя бы одна цифра")
        
        return value 

class User(BaseModel):
    email:EmailStr
    full_name:str
    hashed_password:str
    is_verified:bool
#------------------User Response GET----------------------------------


class UserProjectResponse(BaseModel):
    name:str
    description:str

    model_config = ConfigDict(from_attributes=True)

class UserProjectMembers(BaseModel):
    role:roles.ProjectRole
    project:UserProjectResponse

    model_config = ConfigDict(from_attributes=True)
    
class UserResponse(BaseModel):
    id:int
    email:EmailStr | None = None
    full_name:str
    role:roles.OrderRoleUser
    is_active:bool
    is_verified:bool
    project_member:List[UserProjectMembers]

    model_config = ConfigDict(from_attributes=True)

class UserUpdate(BaseModel):
    old_password: str | None = None
    new_password: str | None = None
    email: EmailStr | None = None
    full_name: str | None = None
    