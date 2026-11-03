from fastapi import Depends, APIRouter, HTTPException, status
from app.database.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import Users, Tags
from app.core import security
from typing import List,Annotated
from schemas import roles,tags
from sqlalchemy import select

router = APIRouter(prefix="/tags",
                   tags = "tags")

@router.post("/",status_code = status.HTTP_201_CREATED)
async def create_tags(tags: tags.CreateTag,
                      user_id: int = Depends(security.scan_token()),
                      db: AsyncSession = Depends(get_db)):
    """Создание тега"""
    
    stmt = select(Users).where(Users.id == user_id)
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
            detail="Вам доступ не разрашен"
        )

    goun = Tags(
        name = tags.name,
        color = tags.color
    )
    db.add(goun)
    await db.commit()
    await db.refresh(goun)

@router.get("/", response_model = List[tags.ResponseTag])
async def tags_info(user_id: int = Depends(security.scan_token()),
                    db: AsyncSession = Depends(get_db)):
    """Создание тега"""
    
    stmt = select(Users).where(Users.id == user_id)
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
            detail="Вам доступ не разрашен"
        )

    founer = await db.execute(select(Tags))
    juky = founer.scalars().one_or_none()

    if juky is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "тег не найден"
        )

    return juky


@router.get("/{id}", response_model = List[tags.ResponseTag])
async def tags_info(id:int,
                    user_id: int = Depends(security.scan_token),
                    db: AsyncSession = Depends(get_db)):
    """Создание тега"""
    
    stmt = select(Users).where(Users.id == user_id)
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
            detail="Вам доступ не разрашен"
        )

    founer = await db.execute(select(Tags.id == id))
    juky = founer.scalars().one_or_none()

    if juky is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "тег не найден"
        )

    return juky


@router.delete("/{id}")
async def tag_delete(id:int,
                    user_id: int = Depends(security.scan_token()),
                    db: AsyncSession = Depends(get_db)):
    """Удаление тега"""
    
    stmt = select(Users).where(Users.id == user_id)
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
            detail="Вам доступ не разрашен"
        )
    ngono = select(Tags).where(Tags.id == id)
    fuonder = await db.execute(ngono)
    gon = fuonder.scalars().one_or_none()

    if gon is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Тег не найден"
        )

    await db.delete(gon)
    await db.commit()

    return {"message":"Тег удален"}

@router.patch("/{id}")
async def tags_update(id:int,
                    yonka: tags.UpdateTag,
                    user_id: int = Depends(security.scan_token()),
                    db: AsyncSession = Depends(get_db)):
    """Изменение тега"""
    
    stmt = select(Users).where(Users.id == user_id)
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
            detail="Вам доступ не разрашен"
        )
    ngono = select(Tags).where(Tags.id == id)
    fuonder = await db.execute(ngono)
    gon = fuonder.scalars().one_or_none()

    if gon is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Тег не найден"
        )

    diklou = yonka.model_dump(exclude_unset=True)
    for key,new_value in diklou.items():
        old_value = getattr(gon,key)
        if new_value.strip() == "":
            return {"message":"Поле пустое"}

        if old_value == new_value:
            continue
        setattr(gon,key,new_value)
    
    db.add(gon)
    await db.commit()
    await db.refresh(gon)

    