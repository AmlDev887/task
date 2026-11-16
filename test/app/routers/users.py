from fastapi import Depends, APIRouter, HTTPException, status
from app.core import security
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from app.models import models
from app.database.db import get_db
from app.schemas import users,roles
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

router = APIRouter(prefix="/users",
                   tags=["users"])

@router.get("/me",response_model=users.UserResponse)
async def user_info(user_id: int = Depends(security.scan_token),db: AsyncSession = Depends(get_db)):
    """Выводим пользователя"""
    
    stmt = select(models.Users).options(joinedload(models.Users.project)).where(models.Users.id == user_id)
    result = await db.execute(stmt)
    answer = result.unique().scalars().one_or_none()

    if answer is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Пользователь не найден.Пройдите авторизацию если не прошли"
        )
    if answer.role != (roles.OrderRoleUser.USER,
                       roles.OrderRoleUser.ADMIN):
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail = "Вам доступ запрещен"
        )
    return answer


@router.patch("/me")
async def user_update(update: users.UserUpdate,
                      user_id: int = Depends(security.scan_token),
                      db: AsyncSession = Depends(get_db)):
    """Ввод изменений на профиль пользователя"""
    
    stmt = select(models.Users).where(models.Users.id == user_id)
    result = await db.execute(stmt)
    answer = result.scalars().one_or_none()

    if answer is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Пользователь не найден"
        )
    if update.old_password and update.new_password:
        if not security.verify_password(update.old_password,answer.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail = "Неверный пароль"
        )
    answer.hashed_password = security.heshing_password(update.new_password) if update.old_password and update.new_password else answer.hashed_password
    answer.email = update.email if update.email else answer.email
    answer.full_name = update.full_name if update.full_name else answer.full_name

    await db.commit()
    await db.refresh(answer)

    return {"message": "Извенения применены"}

@router.get("/",response_model = List[users.UserResponse])
async def user(user_id: int = Depends(security.scan_token),
               page: int = 1,       
               size: int = 20,
               db: AsyncSession = Depends(get_db)):
    """Получение всех пользователей"""
    
    stmt = select(models.Users).where(models.Users.id == user_id)
    result = await db.execute(stmt)
    answer = result.scalars().one_or_none()

    if answer is None:
          raise HTTPException(
                     status_code = status.HTTP_404_NOT_FOUND,
                     detail = "Пользователь не найден"
                 )
    if answer.role != roles.OrderRoleUser.ADMIN:
         raise HTTPException(
                    status_code = status.HTTP_403_FORBIDDEN,
                    detail = "Вам запрещен доступ"
                )
    
    offset = (page - 1) * size
    
    stmt_2 = select(models.Users).order_by(models.Users.id.asc()).offset(offset).limit(size)
    result_2 = await db.execute(stmt_2)
    answer_2 = result_2.scalars().all()

    return answer_2

