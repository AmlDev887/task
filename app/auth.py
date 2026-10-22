from pwdlib import PasswordHash
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Annotated
from fastapi import Depends, HTTPException, FastAPI, status
from database.db import get_db
from sqlalchemy import Session,select,insert
from database.models import Users
from datetime import datetime,timezone,timedelta
from app.schemas import UserLogin,RefreshToken
from jwt.exceptions import InvalidTokenError
import jwt

SECRET_KEY = 'akaza_xanpasu'
SECRET_KEY_2 = 'akaza_xanpasu_2'

app = FastAPI()
password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl = "token")

def full_token(user_id):
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    access_token = jwt.encode({"user_id":str(user_id), "exp":expire, "type":"access"},SECRET_KEY,algorithm="HS256")

    expire_1 = datetime.now(timezone.utc) + timedelta(days=7)
    refresh_token = jwt.encode({"user_id":str(user_id), "exp":expire_1, "type":"access"},SECRET_KEY_2,algorithm="HS256")

    return {
        "access_token":access_token,
        "refresh_token":refresh_token,
        "token_type":"bearear"
    }
def verify_password(plain_password, hashed_password):
    """Проверяем пароль совпдает ли он с паролем в хэше"""
    
    return password_hash.hash(plain_password, hashed_password)

def heshing_password(password):
    """Хешируем пароль"""
    
    return password_hash.hash(password)

def scan_token(token:Annotated[str,Depends(oauth2_scheme)]):
    """Проверка токена"""
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный токен,пройдиет авторизацию",
        )
    return payload

@app.post("/token")
def check_user(user:Annotated[OAuth2PasswordRequestForm,Depends()], db: Session = Depends(get_db)):
    """Проверка пользователя и создание токена"""
    
    stmt = select(Users).where(user.username == Users.full_name)
    result = (db.execute(stmt)).scalar_one_or_none()
    
    if result and verify_password(user.password, result.hashed_password):
        return full_token(result.id)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    raise HTTPException( status_code=status.HTTP_401_UNAUTHORIZED, 
                        detail="Неверное имя пользователя или пароль")

@app.post("/add_user")
def add(new_user: UserLogin, db: Session = Depends(get_db)):
    """Создание нового User"""
    
    data = new_user.model_dump()
    data["hashed_password"] = heshing_password(data["password"])
    del data["password"]

    answer = Users(**data)
    db.add(answer)
    db.commit()
    db.refresh(answer)

    return answer

@app.post("/refresh_token")
def refresh_token(token:Annotated[str,Depends(oauth2_scheme)]):
    """Создание нового токена провркой refresh-а"""
    try:
        bayong = jwt.decode(
            token,
            SECRET_KEY_2,
            algorithms=["HS256"]
        )
    except InvalidTokenError:    
        return "Неверный токен"

    return full_token(bayong["user_id"])




    

