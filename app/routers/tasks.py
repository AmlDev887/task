from fastapi import Depends, APIRouter, HTTPException, status, File, UploadFile
from app.database.db import get_db
from app.schemas import tasks, history, comments
from app.models.models import Comments, ProjectMembers, Tasks, History, TaskTags, Attachments, Users
from sqlalchemy.ext.asyncio import AsyncSession
from app.core import security
from sqlalchemy import select
from typing import List,Annotated
from app.schemas import roles
from pathlib import Path
from datetime import datetime, timezone
from sqlalchemy.orm import joinedload, selectinload
from workers.celery_app import get_email_user
import uuid
import re

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"]
)

@router.get("/{id}",response_model=tasks.TaskResponse)
async def all_task(id: int, 
                   user_id: int = Depends(security.scan_token),
                   db: AsyncSession = Depends(get_db)):
    """Получение одного таска"""
    
    stmt = select(Tasks).where(Tasks.id == id, Tasks.deleted_at is None)
    result = await db.execute(stmt)
    answer = result.scalars().one_or_none()
    if answer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail = "Пользователь не найден"
        )

    user = select(ProjectMembers).where(ProjectMembers.project_id == answer.project_id, 
                                        ProjectMembers.user_id == user_id)
    gummy = await db.execute(user)
    yohoo = gummy.scalars().one_or_none()

    if yohoo is None:
          raise HTTPException(
                     status_code=status.HTTP_404_NOT_FOUND,
                     detail = "Пользователь не найден"
                 )
    
    from_join = select(Tasks).options(joinedload(Tasks.creator),
                                      joinedload(Tasks.assignee),
                                      joinedload(Tasks.project),
                                      selectinload(Tasks.tasktags).joinedload(TaskTags.tag),
                                      selectinload(Tasks.comment),
                                      selectinload(Tasks.history),
                                      selectinload(Tasks.attachments)).where(Tasks.id == id)
    kimi_ki = await db.execute(from_join)
    groking_grok = kimi_ki.scalars().one_or_none()
    
    if groking_grok is None:
        raise HTTPException(
             status_code = status.HTTP_404_NOT_FOUND,
             detail = "Таск не найден"
        )
    
    return groking_grok

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
    task_status_one = answer.status
    if answer.deleted_at is not None:
                raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail = "Таск не найден"
            )
    if task.assignee_id is not None:
        pro_id = answer.project_id
        georg_ass = select(ProjectMembers).where(ProjectMembers.project_id == pro_id,
                                            ProjectMembers.user_id == task.assignee_id)
        ahaha = await db.execute(georg_ass)
        rfag = ahaha.scalars().one_or_none()    
        
        if rfag is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail = "Пользователь (приниматель) не нашлось")
    
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
    if task_status_one != roles.TaskStatus.DONE and task.status == roles.TaskStatus.DONE:
         answer.completed_at = datetime.now(timezone.utc)

    
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

    await db.commit()
    await db.refresh(answer)       

    return answer

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
    answer.deleted_at = datetime.now(timezone.utc)
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
    if answer.deleted_at is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Задача не удалена"
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


    answer.is_deleted = False
    answer.deleted_at = None
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
async def task_hard_delete(id:int,
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
    hunny = select(Users).where(Users.id == creator_id)
    gunno = await db.execute(hunny)
    nojo = gunno.scalars().one_or_none()
    
    if nojo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail = "Пользователь не найден"
        )
    if nojo.role != roles.OrderRoleUser.ADMIN:
        raise HTTPException(
             status_code=status.HTTP_403_FORBIDDEN,
             detail="Доступ не разрашен"
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
    
    pro_id = answer_1.project_id
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
async def creat_coments(
        id: int,
        comment: tasks.TaskCommentCreate,
        author_id: int = Depends(security.scan_token),
        db: AsyncSession = Depends(get_db),
    ):
    """Создание коммента"""
    stmt = select(Tasks).where(Tasks.id == id)
    result = await db.execute(stmt)
    answer = result.scalars().one_or_none()

    if answer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Таск не найден"
        )

    pro_id = answer.project_id
    georg = select(ProjectMembers).where(
        ProjectMembers.project_id == pro_id, ProjectMembers.user_id == author_id
    )

    wait = await db.execute(georg)
    rfag = wait.scalars().one_or_none()

    if rfag is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Нужного проекта нет"
        )
    if rfag.role not in (roles.ProjectRole.EDITOR, roles.ProjectRole.OWNER, roles.ProjectRole.VIEWER):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Вам доступ не разрешен"
        )

    comments = Comments(task_id=id, author_id=author_id, body=comment.body)
    user = select(Users).where(Users.id == author_id)
    yuhu = await db.execute(user)
    ronaldo = yuhu.scalars().one_or_none()
    
    if ronaldo is None:
        raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, 
        detail="Отправтель не найден")
        
    EMAIL_PATTERN = r"(?i)(?<![\w.+-])[a-z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)+"
    email = re.findall(EMAIL_PATTERN, comment.body)
    for e in email:
        get_email_user.delay(ronaldo.email, e, comment.body)
    
    db.add(comments)
    await db.commit()
    await db.refresh(comments)

    return {"message": "Коммент создан"}

@router.get("/{id}/comments",response_model = comments.CommentResponse)
async def get_task_comments(id: int,
                      user_id: int = Depends(security.scan_token),
                      db: AsyncSession = Depends(get_db)):
    """Вывод комменатриев по аайди таска""" 
    
    stmt = select(Tasks).options(selectinload(Tasks.comment)).where(Tasks.id == id,Tasks.deleted_at.is_(None))
    result = await db.execute(stmt)
    answer = result.scalars().one_or_none()
    if answer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Таск не найден")
    
    pro_id = answer.project_id
    georg = select(ProjectMembers).where(
        ProjectMembers.project_id == pro_id, 
        ProjectMembers.user_id == user_id
    )
    wait = await db.execute(georg)
    rfag = wait.scalars().one_or_none()

    if rfag is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Нужного проекта нет"
        )
    if rfag.role not in (roles.ProjectRole.EDITOR, 
                         roles.ProjectRole.OWNER, 
                         roles.ProjectRole.VIEWER):
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Вам доступ не разрешен"
        )     
    return answer
#-------------------------- Tags -----------------------------------------

@router.post("/{id}/tags/{tag_id}")
async def create_tag(id: int, 
                     tag_id: int,
                     user_id: int = Depends(security.scan_token),
                     db: AsyncSession = Depends(get_db)):
    """Присваивание тега к таску"""

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
                                         ProjectMembers.user_id == user_id)

    wait = await db.execute(georg)
    rfag = wait.scalars().one_or_none()

    if rfag is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Нужного проекта нет"
        )
    if rfag.role not in (roles.ProjectRole.EDITOR, roles.ProjectRole.OWNER):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Вам доступ не разрешен"
        )

    tags = TaskTags(
         task_id = id,
         tags_id = tag_id
    )
    db.add(tags)
    await db.commit()
    await db.refresh(tags)

    return {"message":"Тег присвоен таску"}

@router.delete("/s/{id}/tags/{tag_id}")
async def tag_delete(id: int, 
                     tag_id: int,
                     user_id: int = Depends(security.scan_token),
                     db: AsyncSession = Depends(get_db)):
    """Удаление таска"""

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
                                         ProjectMembers.user_id == user_id)

    wait = await db.execute(georg)
    rfag = wait.scalars().one_or_none()

    if rfag is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Нужного проекта нет"
        )
    if rfag.role not in (roles.ProjectRole.EDITOR, roles.ProjectRole.OWNER):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Вам доступ не разрешен"
        )

    search = select(TaskTags).where(TaskTags.task_id == id, TaskTags.tags_id == tag_id)
    gunger = await db.execute(search)
    loki = gunger.scalars().one_or_none()
    
    if loki is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Тег не найден"
        )
    await db.delete(loki)
    await db.commit()

    return {"message":"Тег удален"}

@router.post("/{id}/attachments")
async def task_attech(id: int,
                      fayl: Annotated[UploadFile,File()],
                      user_id: int = Depends(security.scan_token),
                      db: AsyncSession = Depends(get_db)):
    """Добавление файла"""

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
                                            ProjectMembers.user_id == user_id)

    wait = await db.execute(georg)
    rfag = wait.scalars().one_or_none()

    if rfag is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Нужного проекта нет"
        )
    if rfag.role not in (roles.ProjectRole.EDITOR, roles.ProjectRole.OWNER):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Вам доступ не разрешен"
        )
    UPLOAD_DIR = Path("TASK_MENEJER")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    unique_name = f"{uuid.uuid4()}_{fayl.filename}"
    file_path = UPLOAD_DIR / unique_name

    if fayl.size > 5 * 1024 * 1024:
         return {"message":"Файл не омжет быть больше 100 MB"}
    if fayl.size == 0:
         raise HTTPException(
              status_code=status.HTTP_413_CONTENT_TOO_LARGE,
              detail = "Пустой файл"
         )
    
    with open(file_path, "wb") as button:
        while shoko := await fayl.read(1024*1024):
             button.write(shoko)

    attachment = Attachments(
        task_id = id,
        filename = fayl.filename,
        size = fayl.size,
        content_type = fayl.content_type,
        path = str(file_path),
        uploaded_by = user_id
    )

    db.add(attachment)
    await db.commit()
    await db.refresh(attachment)

    return {"message":"Файл загружен"}
