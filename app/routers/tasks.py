from fastapi import Depends, APIRouter, HTTPException, status, File, UploadFile, Query
from app.database.db import get_db
from app.schemas import tasks, history, comments
from app.models.models import Comments, ProjectMembers, Tasks, History, TaskTags, Attachments, Users
from sqlalchemy.ext.asyncio import AsyncSession
from app.core import security
from sqlalchemy import select, func
from typing import List,Annotated
from app.schemas import roles
from pathlib import Path
from datetime import datetime, timezone
from sqlalchemy.orm import joinedload, selectinload
from app.database.db import SessionLocal
import uuid
import re
from celery.schedules import crontab
from app.workers.celery_app import celery, get_email_task
import asyncio
from sqlalchemy.orm.exc import StaleDataError
import logging

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"]
)
logger = logging.getLogger(__name__)

@celery.task()
def get_status_task():
    async def _run():
        async with SessionLocal() as db:
            stmt = select(Users).where(Users.is_verified == True, Users.is_active == True)
            result = await db.execute(stmt)
            answer = result.scalars().all()

            for user in answer:
                hunter = select(Tasks).where(Tasks.assignee_id == user.id, Tasks.status != "DONE")
                gummy = await db.execute(hunter)
                unit = gummy.scalars().all()

                if not unit:
                    continue

                tasks_data = [
                    {
                        "title": task.title, 
                        "due_date": task.due_date.strftime("%d.%m.%Y %H:%M") if task.due_date else "Без срока", 
                        "status": task.status,  
                        "color": "#e74c3c" if (task.due_date and task.due_date < datetime.now(timezone.utc)) else "#555"
                    }
                    for task in unit
                ]

                get_email_task.delay(
                    recipient=user.email,
                    subject="Дневной дайджест тасков",
                    template_name="app/services/daily_digest.html",
                    context_data={
                        "username": user.username,
                        "tasks": tasks_data
                    }
                )
    asyncio.run(_run())

celery.conf.timezone = "Asia/Tashkent"

celery.conf.beat_schedule = {
     "send-daily-digest-every-morning":{
          "task":"app.routers.tasks.get_status_task",
          "schedule":crontab(hour=9, minute=0),
     }
}

@router.get("/search", response_model=tasks.PagedTasks)
async def list_tasks(
     f: Annotated[tasks.SearchResponse, Query()],                                                                                           
     p: Annotated[tasks.Page, Query()],
     sort: str = "-created_at", 
     user_id: int = Depends(security.scan_token), 
     db: AsyncSession = Depends(get_db)
):
    user_projects = select(ProjectMembers.project_id).where(
        ProjectMembers.user_id == user_id
    )
    base = create_schem(f).where(
        Tasks.project_id.in_(user_projects)
    )
    return await search_tasks(f, sort, p, db, base)
    
@router.get("/{id}",response_model=tasks.TaskResponse)
async def get_task(id: int, 
                   user_id: int = Depends(security.scan_token),
                   db: AsyncSession = Depends(get_db)):
    """Получение одного таска"""
    
    stmt = select(Tasks).where(Tasks.id == id, Tasks.deleted_at.is_(None))
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
                task: Annotated[tasks.TaskUpdate, Query()],
                user_id: int = Depends(security.scan_token),
                db: AsyncSession = Depends(get_db)
                ):
    """Измененение таска"""

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

    if task.version != answer.version:
        raise HTTPException(
             status_code=status.HTTP_409_CONFLICT,
             detail = "Версии не совпали"
        )
    old_assignee_id = answer.assignee_id
    old_status = answer.status
    pro_id = answer.project_id
    
    if task.assignee_id is not None:
        georg_ass = select(ProjectMembers).where(ProjectMembers.project_id == pro_id,
                                            ProjectMembers.user_id == task.assignee_id)
        ahaha = await db.execute(georg_ass)
        rfag = ahaha.scalars().one_or_none()    
    
        if rfag is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail = "Пользователь (приниматель) не нашлось")

    kimmi = select(Users).where(Users.id == task.assignee_id, Users.is_active == True)
    grok = await db.execute(kimmi)
    claude = grok.scalars().one_or_none()
    if claude is None:
        raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Нельзя назначить задачу неактивному пользователю"
            )
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
    order = {
    roles.TaskStatus.TODO: 1,
    roles.TaskStatus.IN_PROGRESS: 2,
    roles.TaskStatus.REVIEW: 3,
    roles.TaskStatus.DONE: 4,
    roles.TaskStatus.CANCELLED: 5
    }
    
    hunter = task.model_dump(exclude_unset=True)  
    if not hunter:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нет данных для обновления"
        )
    if "status" in  hunter:
            new_status = task.status
            if task_status_one != roles.TaskStatus.DONE and task.status == roles.TaskStatus.DONE:
                answer.completed_at = datetime.now(timezone.utc)
    
    hunter.pop("version", None) 
    if task.status:
        if order[new_status] < order[answer.status]:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Нельзя менять статус в таком порядке"
            )
    
    try:
        for key,new_value in hunter.items():
            
            old_value = getattr(answer,key,None)
            if old_value != new_value:
                history_update = History(
                    user_id = user_id,
                    task_id = id,
                    field = key,
                    old_value = old_value.value if hasattr(old_value, "value") else str(old_value) if old_value is not None else None,
                    new_value = new_value.value if hasattr(new_value, "value") else str(new_value) if new_value is not None else None
                )
                db.add(history_update)
                setattr(answer,key,new_value)

        await db.commit()
        await db.refresh(answer)       
    
    except StaleDataError :
        await db.rollback()
        raise HTTPException(
              status_code = status.HTTP_409_CONFLICT
         )
    try:
        if task.assignee_id is not None and task.assignee_id != old_assignee_id:
            user_stmt = select(Users).where(Users.id == task.assignee_id)
            user_res = await db.execute(user_stmt)
            assignee_user = user_res.scalars().one_or_none()
            
            if assignee_user:
                get_email_task.delay(
                    recipient=assignee_user.email,
                    subject=f"Вам назначена задача: {answer.title}",
                    template_name="app/services/task_notification.html",
                    context_data={
                        "username": assignee_user.full_name,
                        "task_title": answer.title,
                        "intro_text": "Вам была назначена новая задача.",
                        "action_url": f"https://my-app.com/projects/{answer.project_id}/tasks/{answer.id}"
                    }
                )
        if "status" in hunter and hunter["status"] != old_status:
        
            if answer.creator_id and answer.creator_id != user_id:
                creator_stmt = select(Users).where(Users.id == answer.creator_id)
                creator_res = await db.execute(creator_stmt)
                creator_user = creator_res.scalars().one_or_none()
                
                if creator_user:
                    get_email_task.delay(
                        recipient=creator_user.email,
                        subject=f"Статус задачи изменен: {answer.title}",
                        template_name="app/services/task_notification.html",
                        context_data={
                            "username": creator_user.full_name,
                            "task_title": answer.title,
                            "intro_text": f"Статус задачи изменился на: <b>{answer.status}</b>",
                            "action_url": f"https://my-app.com/projects/{answer.project_id}/tasks/{answer.id}"
                        }
                    )
    except Exception as ex:
         logger.error(f"Ошибка отправки уведомления: {ex}")
   
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
                    user_id = creator_id,
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
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail = "Участник не найден в проекте"
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
                user_id = creator_id,
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

@router.get("/{id}/history",response_model = history.HistorySchemeResponse)
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
    
    stmt = select(History).options(joinedload(History.task),
                                   joinedload(History.user)).where(History.task_id == id)
    result = await db.execute(stmt)
    answer = result.scalars().all()
    
    if not answer:
         return []
    
    pump = [
        "id","user","task","field","old_value","new_value"
    ]

    pump = [
        "id", "user", "task", "field", "old_value", "new_value"
    ]

    for_response = []
    for a in answer:
        context = {}
        for key in pump:
            # Проверяем, есть ли такой атрибут у объекта
            if not hasattr(a, key):
                continue
                
            value = getattr(a, key)
            
            
            if key == "user" and value is not None:
                context["user_name"] = value.full_name 
            elif key == "task" and value is not None:
                context["task_name"] = value.title
            else:
                context[key] = value

        for_response.append(context)

    return for_response

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
    email = set(re.findall(EMAIL_PATTERN, comment.body))
   
    db.add(comments)
    await db.commit()
    await db.refresh(comments)

    for e in email:
        get_email_task.delay(
                            recipient=e, 
                            subject="Вас упомянули", 
                            body=comment.body
                            )
    
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

@router.delete("/{id}/tags/{tag_id}")
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
        raise HTTPException(
             status_code=status.HTTP_413_CONTENT_TOO_LARGE,
             detail = "Привысили допустимый объекм файла"
        )
    if fayl.size == 0:
        fayl.unlink()
        raise HTTPException(
              status_code=status.HTTP_400_BAD_REQUEST,
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


#-------------------------Работа файлами фильтр и пагинация файлов----------------------------------
SORTABLE = {
    "created_at": Tasks.created_at,
    "due_date": Tasks.due_date,
    "priority": Tasks.priority,
    "title": Tasks.title,
}

def create_schem(tasks):
    """Фильтрация пагианция поиска данных"""
    
    query = select(Tasks).where(Tasks.is_deleted == False)
    if tasks.search is not None:
        safe = tasks.search.replace("\\", "\\\\").replace("%", r"\%").replace("_", r"\_")
        query = query.where(Tasks.title.ilike(f"%{safe}%", escape = "\\"))

    if tasks.status is not None:
        query = query.where(Tasks.status == tasks.status)

    if tasks.priority is not None:
        query = query.where(Tasks.priority == tasks.priority)

    if tasks.project_id is not None:
        query = query.where(Tasks.project_id == tasks.project_id)

    if tasks.assignee_id is not None:
        query = query.where(Tasks.assignee_id == tasks.assignee_id)

    if tasks.deadline_from is not None:
        query = query.where(Tasks.due_date >= tasks.deadline_from)

    if tasks.deadline_to is not None:
        query = query.where(Tasks.due_date <= tasks.deadline_to)

    return query

def sort_scanner(stmt, sort: str = "created_at"):
    """проверяем и создаем нужный запрос для поиска по определнному полю"""
    if not sort:
        return stmt.order_by(Tasks.id)
    
    for plan in filter(None,(s.strip() for s in sort.split(","))):
        desc = plan.startswith("-")
        juck = SORTABLE.get(plan.lstrip("-"))

        if juck is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail = f"Нельзя сортировать по {plan}"
            )
        stmt = stmt.order_by(
             juck.desc().nulls_last() if desc else juck.asc().nulls_last()
        )
    return stmt.order_by(Tasks.id)

async def search_tasks(gon: tasks.SearchResponse,
                 sort:str, 
                 p: tasks.Page,
                 db: AsyncSession,
                 base= None):
    """Главная функция для работы поиска,сортировки и фильтрации"""
    
    if base is None:
        base = create_schem(gon)
    
    count_stmt = select(func.count(Tasks.id)).select_from(base.order_by(None).subquery())
    total_count = await db.scalar(count_stmt) or 0

    result_stmt = sort_scanner(base, sort).limit(p.size).offset((p.page - 1) * p.size)
    rows = (await db.scalars(result_stmt)).all()


    pages_count = -(-total_count // p.size) if p.size > 0 and total_count > 0 else 0

    return tasks.PagedTasks(
    items=rows,
    total=total_count,
    page=p.page,
    size=p.size,
    pages=pages_count,  
)

