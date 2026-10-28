from fastapi import Depends, APIRouter, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from datetime import datetime,timezone,timedelta
from app.database.db import get_db
from app.models.models import Users
from app.schemas.users import AddUser, UserLogin
from app.schemas import auth
from sqlalchemy.ext.asyncio import AsyncSession
from app.core import security
from app.config import settings
from sqlalchemy import select
from celery_app import get_email_code
from jwt.exceptions import InvalidTokenError
from app.core import redis
from typing import Annotated
import jwt

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl = "/auth/token")

def full_token(user_id):
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    access_token = jwt.encode({"user_id":str(user_id), "exp":expire, "type":"access"},settings.SECRET_KEY,algorithm="HS256")

    expire_1 = datetime.now(timezone.utc) + timedelta(days=7)
    refresh_token = jwt.encode({"user_id":str(user_id), "exp":expire_1, "type":"refresh"},settings.SECRET_KEY_2,algorithm="HS256")

    return {
        "access_token":access_token,
        "refresh_token":refresh_token,
        "token_type":"bearer"
    }

@router.post("/register",response_model = AddUser)
async def add(new_user: UserLogin, db: AsyncSession = Depends(get_db)):
    """Создание нового User"""
    
    data = new_user.model_dump()
    data["hashed_password"] = security.heshing_password(data["password"])
    del data["password"]

    answer = Users(**data)
    db.add(answer)
    await db.commit()
    await db.refresh(answer)

    get_email_code.delay(new_user.email)
    return {"message": "Пользователь создан. Код подтверждения отправлен на email"}


@router.get("/verify")
async def email_verify(email:auth.EmailVerify,db: AsyncSession = Depends(get_db)):
    
    email_code = await redis.redis_async.get(name = email.email)
    if not email_code:
        return {"error":"Код устарел или не запрашивался.Хапросите код заново"}

    if email_code != email.code:
        return {"error":"Неверный код"}
    
    stmt = select(Users).where(Users.email == email.email)
    result = await db.execute(stmt)

    user = result.scalars().one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    user.is_verified = True
        
    await db.commit()
    await db.refresh(user)
    await redis.redis_async.delete(email.email)

    return {"message": "Email успешно подтверждён"}

@router.post("/login")
async def check_user(user:Annotated[OAuth2PasswordRequestForm,Depends()], db: AsyncSession = Depends(get_db)):
    """Проверка пользователя и создание токена"""
    
    stmt = select(Users).where(user.username == Users.email,user.is_verified == True)
    result = await (db.execute(stmt)).scalar_one_or_none()
    
    if result and security.verify_password(user.password, result.hashed_password):
        return full_token(result.id)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден"
        )
    raise HTTPException( status_code=status.HTTP_401_UNAUTHORIZED, 
                        detail="Неверное имя пользователя или пароль")


@router.post("/refresh")
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


@router.post("/logout/{id}")
async def  



@router.post("/forgot-password")
async def forgot_password(email:auth.EmailForgot, db: AsyncSession = Depends(get_db)):
    """Сообщения для изменения пароля"""
    
    stmt = select(Users).where(Users.email == email.email,Users.is_verified == True )
    result = await db.execute(stmt)

    forgot = result.scalars().one_or_none()
    if forgot is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail = "Пользователь не найден"
        )
    
    get_email_code.delay(email.email)
    return {"message":"Код подтверждения отправлен"}

@router.post("/reset-password")
async def reset_password(email:auth.EmailReset,db: AsyncSession = Depends(get_db)):
    """Подтверждение нового пароля"""
    
    redis_code = await redis.redis_async.get(name = email.email)
    if not redis_code:
        raise HTTPException(
            status_code=400,
            detail="Код истёк или не был запрошен"
        )
    if redis_code != email.code:
        return {"error":"Неверный код подтверждения"}
    
    stmt = select(Users).where(Users.email == email.email,Users.is_verified == True )
    result = await db.execute(stmt)
    forgot = result.scalars().one_or_none()

    if forgot is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail = "Пользователь не найден"
            )
        
    forgot.hashed_password = security.heshing_password(email.new_password)

    await db.commit()
    await db.refresh(forgot)
    await redis.redis_async.delete(name = email.email)
    return {"message":"Код успешно изменен"}

