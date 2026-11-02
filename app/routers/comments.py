from fastapi import Depends, APIRouter, HTTPException, status
from app.core import security
from sqlalchemy import select
from app.models.models import  Comments
from app.database.db import get_db
from app.schemas import comments
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/comments",
                   tags=["comments"])

@router.patch("/{id}")
async def my_comments(id: int,
                      body: comments.CommentUpdate,
                      user_id: int = Depends(security.scan_token),
                      db: AsyncSession =  Depends(get_db)):
    """Мои комменты"""
    
    stmt = select(Comments).where(Comments.author_id == user_id, Comments.id == id)
    result = await db.execute(stmt)
    answer = result.scalars().one_or_none()

    if answer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="комментарий не найден"
        )
    if answer.body == body.body_update:
        return {"message": "Одинаковый текст, ничего не поменялось"}

    new_text = body.body_update.strip() if body.body_update else ""
    if not new_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ваше сообщение пустое",
        )

    answer.body = new_text
    await db.commit()
    await db.refresh(answer)

    return {"message": "Комментарий успешно обновлен"}

@router.delete("/{id}")
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

