from fastapi import Depends, APIRouter, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from app.routers import auth
from app.core import security
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from app.models import models
from app.database.db import get_db
from app.schemas import users
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/users",
                   tags=["users"])

@router.get("/me",response_model=users.UserResponse)
async def user_info(user_id: int = Depends(security.scan_token),db: AsyncSession = Depends(get_db)):
    """Вывожим пользователя"""
    stmt = select(models.Users).options(joinedload(models.Users.project)).where(models.Users.id == user_id)
    result = await db.execute(stmt)
    answer = result.unique().scalars().one_or_none()

    if answer is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Пользователь не найден.Пройдите авторизацию если не прошли"
        )
    if answer.role != "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail = "Вам доступ запрещен"
        )
    return answer

@router.patch("/me")
async def 
    
