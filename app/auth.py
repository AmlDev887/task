from pwdlib import PasswordHash
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Annotated
from fastapi import Depends, HTTPException, FastAPI, status
from app.database.db import get_db
from sqlalchemy import Session,select
from app.database.models import Users
from datetime import datetime,timezone,timedelta
import jwt

SECRET_KEY = 'akaza_xanpasu'
SECRET_KEY_2 = 'akaza_xanpasu_2'
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15

app = FastAPI()
password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl = "token")

# def get_user(username,password):
#     stmt = select(Users).where(username == Users.full_name)
#     user = Session.execute(stmt).scalars_one_or_none()
#     if user and password_hash.verify(password,user.hashed_password): 
#         return user
#     return None

def authenticate(username: str, password: str,db: Session = Depends(get_db)):
    stmt = select(Users).where(username == Users.full_name)
    user = db.execute(stmt).scalars_one_or_none()
    if user and password_hash.verify(password,user.hashed_password): 
        return user
    return None

    
@app.post("/token")
async def my_token(why: Annotated[OAuth2PasswordRequestForm,Depends(oauth2_scheme)]):
    user = authenticate(why.username, why.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Вы не авторизованы",
             headers={"WWW-Authenticate": "Bearer"}
        )
    expire = datetime.now(timezone.utc) + timedelta(minutes = ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = jwt.encode({"user_id":str(user.id), "exp":expire, "type":"access"}, SECRET_KEY, algorithm=ALGORITHM)

    expire_2 = datetime.now(timezone.utc) + timedelta(days = 7)
    refresh_token = jwt.encode({"user_id":str(user.id), "exp":expire_2, "type":"refresh"}, SECRET_KEY_2, algorithm=ALGORITHM)
    return{
        "access_token":access_token,
        "refresh_token":refresh_token,
        "token_type":"bearear"
    }







