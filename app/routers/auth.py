from fastapi import Depends, APIRouter, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from datetime import datetime,timezone,timedelta
from app.database.db import get_db
from app.models.models import Users, EmailTokens
from app.schemas.users import AddUser, UserLogin,roles
from app.schemas import auth
from sqlalchemy.ext.asyncio import AsyncSession
from app.core import security
from app.core.config import settings
from sqlalchemy import select
from jwt.exceptions import InvalidTokenError, PyJWTError
from app.routers.tasks import get_email_task
from app.core import redis
from typing import Annotated
from app.routers.tasks import get_email_task
import secrets
import hashlib
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

def heshing(code):
    hash_object = hashlib.sha256(code.encode("utf-8"))
    hash = hash_object.hexdigest()
    return hash

@router.post("/register",response_model = AddUser)
async def add(new_user: UserLogin, db: AsyncSession = Depends(get_db)):
    """Создание нового User"""
    
    stmt = select(Users).where(Users.email == new_user.email)
    result = await db.execute(stmt)
    answer = result.scalars().one_or_none()
    if answer:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail = "Такой email существует"
        )   
    data = new_user.model_dump()

    data["hashed_password"] = security.heshing_password(data["password"])
    del data["password"]
    try:
        answer = Users(**data)
        db.add(answer)
        await db.flush()
        
        code = secrets.token_urlsafe(32)
        for_celery_code = heshing(code)

        email = EmailTokens(
            user_id = answer.id,
            token = for_celery_code,
            purpose = roles.EmailTokensEnum.VERIFY,
            expires_at = datetime.now(timezone.utc) + timedelta(hours = 24),
            used_at = None
        )
        db.add(email)
        
        await db.commit()
        await db.refresh(answer)
    
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail = 'Не удалось сохранить'
        )
    contex_data = {
        "username":new_user.full_name,
        "код подтверждения":code,
        "button_label":"Подтвердить почту"
    } 
    get_email_task.delay(
                        new_user, 
                        "код для подтверждения email", 
                        contex_data, 
                        template_name = "app/services/confirm.html"
                         )
    return answer

@router.get("/verify")
async def email_verify(verify:auth.EmailVerify,db: AsyncSession = Depends(get_db)):
    
    stmt = select(Users).where(Users.email == verify.email)
    result = await db.execute(stmt)
    user = result.scalars().one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    second = select(EmailTokens).where(EmailTokens.user_id == user.id) 
    regen = await db.execute(second)
    yummy = regen.scalars().one_or_none()

    if yummy is None:
         raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="email  не найден"
                )
    my_code = heshing(verify.code)
    if yummy.token != my_code or yummy.expires_at < datetime.now(timezone.utc) or yummy.used_at is None:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Неверный код"
        )
    
    user.is_verified = True
    await db.commit()
    await db.refresh(user) 

    templates_map = {

    }
    return {"message": "Email успешно подтверждён"}

@router.post("/login")
async def check_user(user:Annotated[OAuth2PasswordRequestForm,Depends()], db: AsyncSession = Depends(get_db)):
    """Проверка пользователя и создание токена"""
    
    stmt = select(Users).where(Users.email == user.username)
    result = await db.execute(stmt)
    answer = result.scalars().one_or_none()

    if answer and security.verify_password(user.password, answer.hashed_password) and answer.is_verified == True:
        return full_token(answer.id)
    
    if answer is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль."
        )
    raise HTTPException( status_code=status.HTTP_401_UNAUTHORIZED, 
                        detail="Неверный email или пароль.")

    
@router.post("/refresh")
async def refresh_token(token:Annotated[str,Depends(oauth2_scheme)]):
    """Создание нового токена провркой refresh-а"""
    black = await redis.redis_async.get(name=f"black_list:{token}")
    if black:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ваш токен отменен"
        )
    try:
        bayong = jwt.decode(
            token,
            settings.SECRET_KEY_2,
            algorithms=["HS256"]
        )
        if bayong.get("type") != "refresh":
             raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Требуется refresh-токен"
                        )
                
    except InvalidTokenError:    
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный токен"
        )

    return full_token(bayong["user_id"])


@router.post("/logout")
async def user_logout(user_id: int = Depends(security.scan_token),
                      refresh_token:str = Depends(oauth2_scheme),
                      db: AsyncSession = Depends(get_db)):
    """Дабвление токена в черный список"""
    
    stmt = select(Users).where(Users.id == user_id)
    result = await db.execute(stmt)
    answer = result.scalars().one_or_none()
    if answer is None:
        raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail = "Пользователь не найден"
            )
    if answer.role != (roles.OrderRoleUser.USER,
                       roles.OrderRoleUser.ADMIN):
        raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail = "Вам сюда нельзя"
            )       
    try:
        yohoo = jwt.decode(refresh_token, settings.SECRET_KEY_2, algorithms=["HS256"])
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный токен"
        )
    token_time = yohoo["exp"] - datetime.now(timezone.utc).timestamp()
    blacklist = await redis.redis_async.set(name = f"black_list:{refresh_token}",ex = token_time)

    return {"message":"Refresh token  добавлен в черный список"}     

@router.post("/forgot-password")
async def forgot_password(email:auth.EmailForgot, db: AsyncSession = Depends(get_db)):
    """Сообщения для изменения пароля"""
    
    stmt = select(Users).where(Users.email == email.email, Users.is_verified == True )
    result = await db.execute(stmt)

    forgot = result.scalars().one_or_none()
    if forgot is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail = "Пользователь не найден"
        )
    
    code = secrets.token_urlsafe(32)
    await redis.redis_async.set(name = f"reset:{code}",value = email.email, ex = 3600)
    get_email_task.delay(email.email,"Код для восстновлаения пароля",code)
    
    return {"message":"Код подтверждения отправлен"}

@router.post("/reset-password")
async def reset_password(reset:auth.EmailReset,db: AsyncSession = Depends(get_db)):
    """Подтверждение нового пароля"""
    
    redis_code = await redis.redis_async.get(name=f"reset:{reset.code}")
    
    if not redis_code:
        raise HTTPException(
            status_code=400,
            detail="Код истёк или не был запрошен"
        )
    if redis_code != reset.email:
        raise HTTPException(
                    status_code=400,
                    detail="неверный email"
                )
    stmt = select(Users).where(Users.email == reset.email,Users.is_verified == True )
    result = await db.execute(stmt)
    forgot = result.scalars().one_or_none()

    if forgot is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail = "Пользователь не найден"
            )
        
    forgot.hashed_password = security.heshing_password(reset.new_password)

    await db.commit()
    await db.refresh(forgot)
    await redis.redis_async.delete(name=f"reset:{reset.code}")
    
    return {"message":"Код успешно изменен"}
