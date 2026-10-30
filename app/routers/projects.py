from fastapi import Depends, APIRouter, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from app.core import security
from sqlalchemy import select,func, insert
from sqlalchemy.orm import joinedload
from app.models.models import Projects, Users, ProjectMembers, Tasks
from app.database.db import get_db
from app.schemas import projects
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from schemas import roles
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
    if answer.role != "admin":
         raise HTTPException(
                    status_code = status.HTTP_403_FORBIDDEN,
                    detail = "Вам запрещен доступ"
                )
    
    result = project.model_dump()
    answer = Projects(**result)
    
    db.add(answer)
    await db.commit()
    await db.refresh(answer)

@router.get("/",response_model=List[projects.ProjectResponse])
async def project_info(page: int = 1,       
                       size: int = 20,
                       db: AsyncSession = Depends(get_db)):
     offset = (page - 1) * size
     stmt = select(Projects).order_by(Projects.id.asc()).offset(offset).limit(size)
     result = await db.execute(stmt)

     answer = result.scalars().all()

     return answer

@router.get("/{id}",response_model=projects.ProjectResponse)
async def project_get(id: int, 
                      db: AsyncSession = Depends(get_db)):
    """Вывод проекта"""
    stmt = select(Projects).where(Projects.id == id)
    result = await db.execute(stmt)
    answer = result.scalars().one_or_none()
    if answer is None:
         raise HTTPException(
              status_code=status.HTTP_404_NOT_FOUND,
              detail="Такого проекта"
         )
    return {"message": "Проект найден"}

@router.patch("/{id}")
async def project_update(id:int,
                         update:projects.ProjectCreate,
                         user_id:int = Depends(security.scan_token),
                         db: AsyncSession = Depends(get_db)):
    """Обновление проекта"""
    user = select(ProjectMembers).options(joinedload(ProjectMembers.project),                                   
                                              joinedload(ProjectMembers.user)).where(ProjectMembers.user_id == user_id, ProjectMembers.project_id == id)
    runner = await db.execute(user)
    budy = runner.scalars().one_or_none()
    
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
    for_iterate = update.model_dump()
    for key,value in  for_iterate.items():
         setattr(answer,key,value)

    db.add(answer)
    await db.commit()
    await db.refresh(answer)

    return {"message":"изменения применены"}

@router.delete("/{id}")
async def project_delete(id:int,
                         user_id:int = Depends(security.scan_token),
                         db: AsyncSession = Depends(get_db)):
    """Обновление проекта"""
    user = select(ProjectMembers).options(joinedload(ProjectMembers.project),                                   
                                          joinedload(ProjectMembers.user)).where(ProjectMembers.user_id == user_id, 
                                                                                 ProjectMembers.project_id == id)
    runner = await db.execute(user)
    budy = runner.scalars().one_or_none()
    
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
    if budy.role != roles.ProjectRole.OWNER:
            raise HTTPException(
                 status_code=status.HTTP_403_FORBIDDEN,
                 detail = "Доступ не разрешен вы не (Admin)"
            )
    
    new_member = ProjectMembers(
    project_id=id,
    user_id=int(member.user_id),
    role=member.owner_id
)

    db.add(new_member)
    await db.commit()
    await db.refresh(new_member)

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
    if budy.role != roles.ProjectRole.OWNER:
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
async def status(id:int,
                 db: AsyncSession = Depends(get_db)):
    """Вывод статуса"""
    
    stmt = select(Tasks.status,func.count()).where(Tasks.project_id == id).group_by(Tasks.status)
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
    if answer.role != (
                        roles.ProjectRole.OWNER,
                        roles.ProjectRole.EDITOR
                    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail = "Доступ не разрешен вы не (Editor,Owner)"
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
    
    return task

@router.get("/{id}/tasks",response_model=List[projects.ProjectTaskResponse])
async def task_response(id:int,
                        db: AsyncSession = Depends(get_db)):
    """Вывод всех тасков конкреотного проекта"""
    project = select(Projects).where(Projects.id == id)
    vudy = await db.execute(project)
    runner = vudy.scalars().one_or_none()
    if runner is None:
         raise HTTPException(
                     status_code=status.HTTP_404_NOT_FOUND,
                     detail="Проект не найден"
             )
    stmt = select(Tasks).where(Tasks.project_id == id)
    result = await db.execute(stmt)
    answer = result.scalars().all()
    if not answer:
        return []
    return answer