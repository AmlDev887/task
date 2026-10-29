from fastapi import Depends, APIRouter, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from app.core import security
from sqlalchemy import select,insert
from sqlalchemy.orm import joinedload
from app.models.models import Projects, Users, ProjectMembers
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
              detail="Проект не найден"
         )
    new_owner = member.model_dump()
    for key,value in new_owner.items():
         setattr(answer,key,value)

    await db.commit()
    await db.refresh(answer)
    return {"message":"Добавлено"}