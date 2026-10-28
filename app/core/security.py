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



