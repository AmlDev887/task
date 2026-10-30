from fastapi import Depends, APIRouter, HTTPException, status
from app.database.db import get_db
from app.schemas import tasks, history
from app.models.models import Projects, Users, ProjectMembers, Tasks, History
from sqlalchemy.ext.asyncio import AsyncSession
from app.core import security
from sqlalchemy import select
from typing import List
from schemas import roles

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"]
)

@router.get("/{id}",response_model=tasks.TaskResponse)
async def all_task(id: int, 
             db: AsyncSession = Depends(get_db)):
    """Получение одного таска"""
    
    stmt = select(Tasks).where(Tasks.id == id)
    result = await db.execute(stmt)
    answer = result.scalars().one_or_none()
    if answer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail = "Пользователь не найден"
        )
    return answer


@router.patch("/{id}")
async def update_task(id: int, 
                task: tasks.TaskUpdate,
                user_id: int = Depends(security.scan_token),
                db: AsyncSession = Depends(get_db)
                ):
 
    body = select(Tasks).where(Tasks.id == id )
    runner = await db.execute(body)
    answer = runner.scalars().one_or_none()
    if answer is None:
        raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail = "Таск не найден"
                )

    pro_id = answer.project_id
    georg = select(ProjectMembers).where(ProjectMembers.project_id == pro_id,
                                         ProjectMembers.user_id == user_id)

    wait = await db.execute(georg)
    rfag = wait.scalars().one_or_none()
    if rfag is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail = "Нужного проекта нет"
                )
    if rfag.role not in (roles.ProjectRole.EDITOR,
                     roles.ProjectRole.OWNER):
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detil = "Вам доступ не разрешен"
        )
    stmt = select(Tasks).where(Tasks.id == id)
    result = await db.execute(stmt)
    answer = result.scalars().one_or_none()

    if answer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail = "Пользователь не найден"
        )
    
    new_task = task.model_dump(exclude_unset = True)
 
    
    for key, value in new_task.items():   
        setattr(answer,key,value)

    db.commit()
    db.refresh(answer)       

@router.delete("/{id}")
async def task_delete(id: int, 
                db: AsyncSession = Depends(get_db),
                creator_id: int = Depends(security.scan_token)):
    """Мягкое удаление таска"""
 
    body = select(Tasks).where(Tasks.id == id )
    runner = await db.execute(body)
    answer = runner.scalars().one_or_none()
    if answer is None:
        raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail = "Таск не найден"
                )

    pro_id = answer.project_id
    georg = select(ProjectMembers).where(ProjectMembers.project_id == pro_id,
                                         ProjectMembers.user_id == creator_id)
    wait = await db.execute(georg)
    rfag = wait.scalars().one_or_none()
    if rfag is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail = "Нужного проекта нет"
                )
    if rfag.role not in (roles.ProjectRole.EDITOR,
                     roles.ProjectRole.OWNER):
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detil = "Вам доступ не разрешен"
        )
    stmt = select(Tasks).where(Tasks.id == id,Tasks.is_deleted == False)
    result = await db.execute(stmt)
    answer = result.scalars().one_or_none()
    
    if answer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail = "Таск не найдено "
        )
    
    answer.is_deleted = True
    db.commit()
    
    return {"message":"Удалено"}

@router.post("/{id}/restore", response_model = tasks.TaskScheme)
async def task_restore(id: int,
                 creator_id: int = Depends(security.scan_token), 
                 db: AsyncSession = Depends(get_db)):
    """Мягкое восстановление таска"""
    
    body = select(Tasks).where(Tasks.id == id )
    runner = await db.execute(body)
    answer = runner.scalars().one_or_none()
    if answer is None:
        raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail = "Таск не найден"
                )

    pro_id = answer.project_id
    georg = select(ProjectMembers).where(ProjectMembers.project_id == pro_id,
                                         ProjectMembers.user_id == creator_id)

    wait = await db.execute(georg)
    rfag = wait.scalars().one_or_none()
    if rfag is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail = "Нужного проекта нет"
                )
    if rfag.role not in (roles.ProjectRole.EDITOR,
                     roles.ProjectRole.OWNER):
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detil = "Вам доступ не разрешен"
        )
    stmt = select(Tasks).where(Tasks.id == id, Tasks.is_deleted == True)
    result = await db.execute(stmt)
    answer = result.scalars().one_or_none()

    if answer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail = "Таск не найден"
        )

    answer.is_deleted = False
    await db.commit()
    await db.refresh(answer)
    return answer
    
@router.delete("/{id}/hard")
async def task_delete(id:int,
                      db: AsyncSession = Depends(get_db)):
    """Удаление таска без возможности восстановить"""
    stmt = select(Tasks).where(Tasks.id == id)
    result = await db.execute(stmt)
    answer = result.scalars().one_or_none()
    
    if answer is None:   
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail = "Таск не найден"
        )

    await db.delete(answer)
    await db.commit()

    return {"message":"Удалено"}

@router.get("/{id}/history",response_model =List[history.HistorySchemeResponse])
async def tasks_history(id:int, db:AsyncSession = Depends(get_db)):
    """История тасков"""
    
    stmt = select(History).where(History.task_id == id)
    result = await db.execute(stmt)
    answer = result.scalars().all()
    if not answer:
         return []

    return answer

