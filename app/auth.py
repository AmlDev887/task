from pwdlib import PasswordHash
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Annotated
from fastapi import Depends, HTTPException, FastAPI, status
from app.database.db import get_db
from sqlalchemy import Session,select,insert
from app.database.models import Users
from datetime import datetime,timezone,timedelta
from app.schemas import UserLogin,RefreshToken
from jwt.exceptions import InvalidTokenError
import jwt

SECRET_KEY = 'akaza_xanpasu'
SECRET_KEY_2 = 'akaza_xanpasu_2'

app = FastAPI()
password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl = "token")


def verify_password(plain_password, hashed_password):
    """Проверяем пароль совпдает ли он с паролем в хэше"""
    
    return password_hash.hash(plain_password, hashed_password)

def heshing_password(password):
    """Хешируем пароль"""
    
    return password_hash.hash(password)


def create_access_token(user):
    """Создание access токена"""
    
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    access_token = jwt.encode({"user_id":str(user.id), "exp":expire, "type":"access"},SECRET_KEY,algorithm="HS256")
    return access_token

def create_refresh_token(user):
    """Создание refresh токена"""
    
    expire_1 = datetime.now(timezone.utc) + timedelta(days=7)
    refresh_token = jwt.encode({"user_id":str(user.id), "exp":expire_1, "type":"access"},SECRET_KEY_2,algorithm="HS256")
    return refresh_token

def scan_token(token):
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
def check_user(user: UserLogin, db: Session = Depends(get_db)):
    """Проверка пользователя и создание токена"""
    
    stmt = select(Users).where(user.username == Users.full_name)
    result = (db.execute(stmt)).scalar_one_or_none()
    
    if result and verify_password(user.password, result.hashed_password):
        token = create_refresh_token(result)
        return token
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
@app.post("/add_user")
def add(new_user: UserLogin, db: Session = Depends(get_db)):
    """Создание нового User"""
    
    data = new_user.model_dump()
    data["hashed_password"] = heshing_password(data["password"])
    
    del data["password"]
    stmt = insert(Users).values()
    answer = db.execute(stmt)

    db.add(answer)
    db.commit()
    db.refresh(answer)




    