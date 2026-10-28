from pydantic import BaseModel,EmailStr

class EmailVerify(BaseModel):
    email:EmailStr
    code:int