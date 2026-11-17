from fastapi import Depends, APIRouter, HTTPException, status, Query
from app.core import security
from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload
from app.models.models import  Comments,Users
from app.database.db import get_db
from app.schemas import comments
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import re

router = APIRouter(prefix="/comments",
                   tags=["comments"])

@router.get("/", response_model = List[comments.CommentsResponse])
async def get_comments(user_id: int = Depends(security.scan_token),
                       limit: int = Query(20, ge=1, le=100),
                       offset: int = Query(0, ge=0),
                       db: AsyncSession =  Depends(get_db)):
    """Вывод всех комментов"""
    
    stmt = select(Comments).options(joinedload(Comments.task)).where(Comments.author_id == user_id).limit(limit).offset(offset)
    result = await db.execute(stmt)
    answer = result.scalars().all()

    all_comment = []

    if not answer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail = "У вас нет комментариев"
        ) 
    EMAIL_PATTERN = r"(?i)(?<![\w.+-])[a-z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)+"
    
    for a in answer:
        email = set(re.findall(EMAIL_PATTERN, a.body))
        user = []
        for e in email:
            send = select(Users).where(Users.email == e)
            kimmi = await db.execute(send)
            grok = kimmi.scalars().one_or_none()
            if grok:
                user.append(grok)
        
        commentary = {
            "id": a.id,
            "body" : a.body,
            "task_name" : a.task.title,
            "receipt": user[0].full_name if user else None,
            "email": [u.email for u in user]
        }

        all_comment.append(commentary)

    return all_comment

@router.patch("/{id}")
async def my_comments(id: int,
                      body: comments.CommentUpdate,
                      user_id: int = Depends(security.scan_token),
                      db: AsyncSession =  Depends(get_db)):
    """Изменение коммента"""
    
    stmt = select(Comments).where(Comments.author_id == user_id, Comments.id == id)
    result = await db.execute(stmt)
    answer = result.scalars().one_or_none()

    if answer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="комментарий не найден"
        )
    if answer.body == body.body:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail = "Запись сущесвтует"
        )

    new_text = body.body.strip() if body.body else ""
    if not new_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ваше сообщение пустое",
        )

    answer.body = new_text
    await db.commit()
    await db.refresh(answer)

    return {"message": "Комментарий успешно обновлен"}

@router.delete("/{id}",status_code=status.HTTP_204_NO_CONTENT)
async def comment_delete(id: int,
                         user_id: int = Depends(security.scan_token),
                         db: AsyncSession =  Depends(get_db)):
    """Удаление коммента"""

    stmt = select(Comments).where(Comments.author_id == user_id, Comments.id == id)
    result = await db.execute(stmt)
    answer = result.scalars().one_or_none()

    if answer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="комментарий не найден"
        )
    await db.delete(answer)
    await db.commit()

    return {"message":"Коммент удален"}

@router.get("/search", response_model=comments.CommenstSearchResponse)
async def search_comments(text: str = Query(..., description="Текст для поиска"),
                user_id: int = Depends(security.scan_token),
                page: int = Query(1, ge=1),
                size: int = Query(20, ge=1, le=100),
                db: AsyncSession =  Depends(get_db)):
    """Поиск комментариев по введенному текста"""
    
    offset = (page - 1)* size
    safe = text.replace("\\", "\\\\").replace("%", r"\%").replace("_", r"\_")
    
    if not safe.split():
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail="пустое поле поиска"
        )

    stmt = select(Comments).where(Comments.author_id == user_id, Comments.body.ilike(f"%{safe}%", escape="\\")).order_by(Comments.id.asc()).limit(size).offset(offset)
    result = await db.execute(stmt)
    answer = result.scalars().all()

    if not answer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail = "У вас нет комменатриев"
        )
    comm = []
    for a in answer:
        comm.append({"id":a.id,
                     "body":a.body})
    
    return {
            "body":comm
        }