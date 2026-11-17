from pydantic import BaseModel,EmailStr

class EmailVerify(BaseModel):
    email:EmailStr
    code:str

class EmailForgot(BaseModel):
    email:EmailStr
    password:str


class EmailReset(BaseModel):
    email:EmailStr
    code:str
    new_password:str

class RefreshToken(BaseModel):

    refresh_token: str