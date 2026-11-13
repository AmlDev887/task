from fastapi import Depends, APIRouter, HTTPException, status
from app.core import security
from sqlalchemy import select,func
from sqlalchemy.orm import joinedload
from app.models.models import Projects, Users, ProjectMembers, Tasks
from app.database.db import get_db
from app.schemas import projects
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.schemas import roles
from datetime import date
from tasks import get_email_task

router = APIRouter(prefix="/projects",
                   tags=["projects"])

@router.post("/")
async def create_project(project: projects.ProjectCreate,
                         user_id: int = Depends(security.scan_token),
                         db: AsyncSession = Depends(get_db)):
    """Создание проекта"""
    stmt = select(Users).where(Users.id == user_id)
    result = await db.execute(stmt)
    answer = result.scalars().one_or_none()

    if answer is None:
          raise HTTPException(
                     status_code = status.HTTP_404_NOT_FOUND,
                     detail = "Пользователь не найден"
                 )
    if answer.role not in (roles.OrderRoleUser.ADMIN,
                       roles.OrderRoleUser.USER):
         
        raise HTTPException(
                    status_code = status.HTTP_403_FORBIDDEN,
                    detail = "Вам запрещен доступ"
                )
    
    result = project.model_dump()
    result["owner_id"] = user_id
    answer = Projects(**result)
    
    db.add(answer)
    await db.commit()
    await db.refresh(answer)

    return {"message":"Проект создан"}

@router.get("/",response_model=List[projects.ProjectResponse])
async def project_info(page: int = 1,       
                       size: int = 20,
                       user_id: int = Depends(security.scan_token),
                       db: AsyncSession = Depends(get_db)):

    
    offset = (page - 1) * size
    stmt = select(Projects).where(Projects.owner_id == user_id).order_by(Projects.id.asc()).offset(offset).limit(size)
    
    result = await db.execute(stmt)
    answer = result.scalars().all()

    return answer

@router.get("/{id}",response_model=projects.ProjectResponse)
async def project_get(id: int, 
                      user_id: int = Depends(security.scan_token),
                      db: AsyncSession = Depends(get_db)):
    """Вывод проекта"""
    
    stmt = select(Projects).where(Projects.id == id, Projects.owner_id == user_id)
    result = await db.execute(stmt)
    answer = result.scalars().one_or_none()
   
    if answer is None:
         raise HTTPException(
              status_code=status.HTTP_404_NOT_FOUND,
              detail="Такого проекта нет"
         )
    return answer

@router.patch("/{id}")
async def project_update(id:int,
                         update:projects.ProjectUpdate,
                         user_id:int = Depends(security.scan_token),
                         db: AsyncSession = Depends(get_db)):
    """Обновление проекта"""
    user = select(ProjectMembers).options(joinedload(ProjectMembers.project),                                   
                                              joinedload(ProjectMembers.user)).where(ProjectMembers.user_id == user_id, ProjectMembers.project_id == id)
    runner = await db.execute(user)
    budy = runner.scalars().one_or_none()
    if budy is None:
        raise HTTPException(
             status_code=status.HTTP_404_NOT_FOUND,
             detail = "Проект не найдено"
        )
    if budy.role == roles.ProjectRole.VIEWER:
        raise HTTPException(
             status_code=status.HTTP_403_FORBIDDEN,
             detail = "Доступ не разрешен"
        )
    stmt = select(Projects).where(Projects.id == id)
    result = await db.execute(stmt)
    answer = result.scalars().one_or_none()

    if answer is None:
         raise HTTPException(
                      status_code=status.HTTP_404_NOT_FOUND,
                      detail="Такого проекта"
                 )
    for_iterate = update.model_dump(exclude_unset=True)

    for key,value in for_iterate.items():
         setattr(answer,key,value)

    await db.commit()
    await db.refresh(answer)

    
    return {"message":"изменения применены"}

@router.delete("/{id}",status_code=status.HTTP_204_NO_CONTENT)
async def project_delete(id:int,
                         user_id:int = Depends(security.scan_token),
                         db: AsyncSession = Depends(get_db)):
    """Удаление проекта"""
    user = select(ProjectMembers).options(joinedload(ProjectMembers.project),                                   
                                          joinedload(ProjectMembers.user)).where(ProjectMembers.user_id == user_id, 
                                                                                 ProjectMembers.project_id == id)
    runner = await db.execute(user)
    budy = runner.scalars().one_or_none()
    if budy is None:
            raise HTTPException(
                 status_code=status.HTTP_404_NOT_FOUND,
                 detail = "Проект не найдено"
            )
    
    if budy.role != roles.ProjectRole.OWNER:
        raise HTTPException(
             status_code=status.HTTP_403_FORBIDDEN,
             detail = "Доступ не разрешен вы не (Admin)"
        )
    stmt = select(Projects).where(Projects.id == id)
    result = await db.execute(stmt)
    answer = result.scalars().one_or_none()

    if answer is None:
         raise HTTPException(
                      status_code=status.HTTP_404_NOT_FOUND,
                      detail="Такого проекта"
                 )
    await db.delete(answer)
    await db.commit()

    return {"message":"Проект удален"}

@router.post("/{id}/members")
async def member_user(id:int,
                      member:projects.CreateOwner,
                      user_id:int = Depends(security.scan_token),
                      db: AsyncSession = Depends(get_db)):
    """Добавление пользователя в проект"""
    user_query = select(ProjectMembers).options(
        joinedload(ProjectMembers.project),
        joinedload(ProjectMembers.user)
    ).where(ProjectMembers.user_id == user_id, ProjectMembers.project_id == id)
    
    runner = await db.execute(user_query)
    budy = runner.scalars().one_or_none()
    
    if budy is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Проект не найден или вы не участник"
        )
    if budy.role != roles.ProjectRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ не разрешен: вы не владелец (Owner)"
        )
    
    target_user_id = int(member.user_id)

    target_user_stmt = select(Users).where(Users.id == target_user_id)
    target_user_res = await db.execute(target_user_stmt)
    target_user = target_user_res.scalars().one_or_none()

    if target_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь для добавления не найден"
        )

    existing_member_stmt = select(ProjectMembers).where(
        ProjectMembers.project_id == id,
        ProjectMembers.user_id == target_user_id
    )
    existing_res = await db.execute(existing_member_stmt)
    if existing_res.scalars().one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь уже состоит в этом проекте"
        )

    new_member = ProjectMembers(
        project_id=id,
        user_id=target_user_id,
        role=member.role
    )

    db.add(new_member)
    await db.commit()
    await db.refresh(new_member)
    
    get_email_task.delay(
        
        recipient=target_user.email,
        subject="Вас добавили в проект!",
        template_name="email/task_notification.html",
        context_data={
            "username": target_user.username,
            "task_title": budy.project.title if budy.project else "Рабочий проект",
            "intro_text": f"Вы были добавлены в проект с ролью: <b>{member.role}</b>",
            "action_url": f"https://my-app.com/projects/{id}"
        }
    )
    return {"message": "Пользователь добавлен в проект"}

@router.delete("/{id}/members")
async def member_user(id:int,
                      owner:projects.ProjectOwnerDelete,
                      user_id:int = Depends(security.scan_token),
                      db: AsyncSession = Depends(get_db)):
    
    user = select(ProjectMembers).options(
            joinedload(ProjectMembers.project),
            joinedload(ProjectMembers.user)
        ).where(ProjectMembers.user_id == user_id, ProjectMembers.project_id == id)
        
    runner = await db.execute(user)
    budy = runner.scalars().one_or_none()
    if budy is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Проект не найден"
        )
    if budy.role not in roles.ProjectRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail = "Доступ не разрешен вы не (Admin)"
                )
    stmt = select(ProjectMembers).options(
                joinedload(ProjectMembers.project),
                joinedload(ProjectMembers.user)
            ).where(ProjectMembers.project_id == id,ProjectMembers.user_id == owner.member_id)
    result = await db.execute(stmt)
    answer = result.scalars().one_or_none()
            
    await db.delete(answer)
    await db.commit()

@router.get("/{id}/stats", response_model = projects.ProjectTask)
async def project_stats(id:int,
                        user_id: int = Depends(security.scan_token),
                        db: AsyncSession = Depends(get_db)):
    """Вывод статуса"""
    yohoo = select(ProjectMembers).where(ProjectMembers.project_id == id , ProjectMembers.user_id == user_id)
    bang = await db.execute(yohoo)
    hunny = bang.scalars().one_or_none()
    
    if hunny is None:
        raise HTTPException(
             status_code=status.HTTP_404_NOT_FOUND,
             detail = "Пользователь или проект не найден"
        )
    if hunny.role not in  (roles.ProjectRole.VIEWER,
                     roles.ProjectRole.EDITOR,
                     roles.ProjectRole.OWNER):
        
        raise HTTPException(
             status_code = status.HTTP_403_FORBIDDEN,
             detail="Вам сюда нельзя"
        )
    stmt = select(Tasks.status,func.count()).where(Tasks.project_id == id, Tasks.is_deleted == False ).group_by(Tasks.status)
    result = await db.execute(stmt)
    answer = result.all()

    return {
         "status":{row[0]: row[1] for row in answer},
         "project_id":id
    }

@router.post("/{id}/tasks",status_code=status.HTTP_201_CREATED)
async def create_task(id:int,
                      update:projects.ProjectTaskUpdate,
                      user_id: int = Depends(security.scan_token),
                      db: AsyncSession = Depends(get_db)):
    """Создание нового таска"""
    
    stmt = select(ProjectMembers).where(ProjectMembers.user_id == user_id,
                                        ProjectMembers.project_id == id)
    result = await db.execute(stmt)
    answer = result.scalars().one_or_none()
    
    if answer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Проект не найден"
    )
    if answer.role not in (
                        roles.ProjectRole.OWNER,
                        roles.ProjectRole.EDITOR
                    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail = "Доступ не разрешен вы не (Editor,Owner)"
        )
    if update.due_date < date.today():
        raise HTTPException(
            status_code=400,
            detail="Дата окаончания не может быть меньше текущей даты"
        )
    if update.assignee_id:
        dunny = await db.execute(select(ProjectMembers).where(ProjectMembers.project_id == id, 
                                                            ProjectMembers.user_id == update.assignee_id
                                                                ))
        funny = dunny.scalars().one_or_none()
        if funny is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail = "Пользователь не состоит в проекте"
            )
    
    task = Tasks(
        title= update.title,
        description=update.description,
        status= update.status,
        priority=update.priority,
        due_date=update.due_date,
        project_id=id,
        creator_id=user_id,
        assignee_id=update.assignee_id
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    if update.assignee_id:
        assignee_stmt = select(Users).where(Users.id == update.assignee_id)
        assignee_result = await db.execute(assignee_stmt)
        assignee_user = assignee_result.scalars().one_or_none()

        if assignee_user:
            get_email_task.delay(
                recipient=assignee_user.email,
                subject=f"Новая задача в проекте: {update.title}",
                template_name="email/task_notification.html",
                context_data={
                    "username": assignee_user.username,
                    "task_title": update.title,
                    "task_description": update.description,
                    "priority": update.priority,
                    "due_date": str(update.due_date),
                    "action_url": f"https://my-app.com/projects/{id}/tasks/{task.id}"
                }
            )
    return {"message":"Таск создан"}

@router.get("/{id}/tasks",response_model=List[projects.ProjectTaskResponse])
async def task_response(id:int,
                        user_id: int = Depends(security.scan_token),
                        db: AsyncSession = Depends(get_db)):
    """Вывод всех тасков конкреотного проекта"""
    stmt = select(ProjectMembers).where(
        ProjectMembers.project_id == id,
        ProjectMembers.user_id == user_id
    )
    result = await db.execute(stmt)
    member = result.scalars().one_or_none()

    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Проект не найден"
        )

    stmt = select(Tasks).where(
        Tasks.project_id == id,
        Tasks.deleted_at.is_(None)
    )
    result = await db.execute(stmt)
    tasks = result.scalars().all()

    return tasks
