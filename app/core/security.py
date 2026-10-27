from pwdlib import PasswordHash
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Annotated
from datetime import datetime,timezone,timedelta
from jwt.exceptions import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException, APIRouter, status
from sqlalchemy import select
from app.models.models import Users
from app.config import settings
from app.database.db import get_db
import jwt

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl = "/auth/token")

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

async def verify_password(plain_password, hashed_password):
    """Проверяем пароль совпдает ли он с паролем в хэше"""
    
    return password_hash.verify(plain_password, hashed_password)

async def heshing_password(password):
    """Хешируем пароль"""
    
    return password_hash.hash(password)

async def scan_token(token:Annotated[str,Depends(oauth2_scheme)]):
    """Проверка токена"""
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")
        if payload.get("type") != "access":
             raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Требуется access-токен"
            )
    
        user_id = payload.get("user_id")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="В токене отсутствует user_id"
            )

        return int(user_id)
       
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный токен,пройдиет авторизацию",
        )
    return user_id

async def full_token(user_id):
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    access_token = jwt.encode({"user_id":str(user_id), "exp":expire, "type":"access"},settings.SECRET_KEY,algorithm="HS256")

    expire_1 = datetime.now(timezone.utc) + timedelta(days=7)
    refresh_token = jwt.encode({"user_id":str(user_id), "exp":expire_1, "type":"refresh"},settings.SECRET_KEY_2,algorithm="HS256")

    return {
        "access_token":access_token,
        "refresh_token":refresh_token,
        "token_type":"bearer"
    }

@router.post("/token")
async def check_user(user:Annotated[OAuth2PasswordRequestForm,Depends()], db: AsyncSession = Depends(get_db)):
    """Проверка пользователя и создание токена"""
    
    stmt = select(Users).where(user.username == Users.email)
    result = await (db.execute(stmt)).scalar_one_or_none()
    
    if result and verify_password(user.password, result.hashed_password):
        return full_token(result.id)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден"
        )
    raise HTTPException( status_code=status.HTTP_401_UNAUTHORIZED, 
                        detail="Неверное имя пользователя или пароль")


@router.post("/refresh_token")
async def refresh_token(token:Annotated[str,Depends(oauth2_scheme)]):
    """Создание нового токена провркой refresh-а"""
    try:
        bayong = jwt.decode(
            token,
            settings.SECRET_KEY_2,
            algorithms=["HS256"]
        )
        if bayong.get("type") != "refresh":
             raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Требуется access-токен"
                        )
                
    except InvalidTokenError:    
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный токен"
        )

    return full_token(bayong["user_id"])

