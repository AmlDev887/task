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
            detail = "Вам доступ не разрешен"
        )
    
    hunter = task.model_dump(exclude_unset=True)
    for key,new_value in hunter.items():
        old_value = getattr(answer,key,None)
        if old_value != new_value:
            history_update = History(
                use_id = user_id,
                task_id = id,
                field = key,
                old_value = old_value if old_value is not None else None,
                new_value = new_value  if new_value is not None else None
            )
            db.add(history_update)
            setattr(answer,key,new_value)

    if answer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail = "Пользователь не найден"
        )
    
    new_task = task.model_dump(exclude_unset = True)
 
    
    for key, value in new_task.items():   
        setattr(answer,key,value)

    await db.commit()
    await db.refresh(answer)       

@router.delete("/{id}")
async def task_delete(id: int, 
                      db: AsyncSession = Depends(get_db),
                     creator_id: int = Depends(security.scan_token)):
    """Мягкое удаление таска"""
    
    body = select(Tasks).where(Tasks.id == id,Tasks.is_deleted == False )
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
            detail = "Вам доступ не разрешен"
        )
    
    answer.is_deleted = True
    history_update = History(
                    use_id = creator_id,
                    task_id = id,
                    field = "is_deleted",
                    old_value = "False",
                    new_value = "True" )
    
    db.add(history_update)
    await db.commit()
    await db.refresh(answer)
    
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
            detail = "Вам доступ не разрешен"
        )

    if answer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail = "Таск не найден"
        )

    answer.is_deleted = False
    history_update = History(
                use_id = creator_id,
                task_id = id,
                field = "is_deleted",
                old_value = "True",
                new_value = "False" )
    
    db.add(history_update)
    await db.commit()
    await db.refresh(answer)
    return answer
    
@router.delete("/{id}/hard")
async def task_delete(id:int,
                      creator_id: int = Depends(security.scan_token),
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
            detail = "Вам доступ не разрешен"
        )

    await db.delete(answer)
    await db.commit()
    return {"message":"Удалено"}

@router.get("/{id}/history",response_model =List[history.HistorySchemeResponse])
async def tasks_history(id:int, 
                        creator_id: int = Depends(security.scan_token),
                        db:AsyncSession = Depends(get_db)):
    """История тасков"""
    stmt_1 = select(Tasks).where(Tasks.id == id)
    result_1 = await db.execute(stmt_1)
    answer_1 = result_1.scalars().one_or_none()

    if answer_1 is None:   
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
            detail = "Вам доступ не разрешен"
        )
    
    stmt = select(History).where(History.task_id == id)
    result = await db.execute(stmt)
    answer = result.scalars().all()
    if not answer:
         return []
    
    return answer

@router.post("/{id}/comments")
async def creat_coments(id: int,
                        comment: tasks.TaskCommentCreate,
                        db: AsyncSession = Depends(get_db):

    stmt = select(Tasks).where(Tasks.id == )

     
