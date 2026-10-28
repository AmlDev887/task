from pydantic import BaseModel,EmailStr

class EmailVerify(BaseModel):
    email:EmailStr
    code:int

class EmailForgot(BaseModel):
    email:EmailStr
    password:str
    is_verified:bool

class EmailReset(BaseModel):
    email:EmailStr
    code:str
    new_password:str