from fastapi import Depends, HTTPException, FastAPI, status
from database.db import get_db
from datetime import datetime,timezone,timedelta
from schemas import tasks, history, users
from sqlalchemy import select, insert
from sqlalchemy.orm import Session, joinedload
from models.models import Tasks, Projects, History
from app.auth import scan_token
from typing import List
app = FastAPI()


@app.post("/projects/{id}/tasks", status_code = status.HTTP_201_CREATED) 
def create_task(task: tasks.TaskScheme, id: int,
                db: Session = Depends(get_db),
                user_id: int = Depends(scan_token)):
    
    """Создание таска"""

    stmt = select(Projects).where(id == Projects.id)
    result = db.execute(stmt).scalar_one_or_none()
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    new_task = Tasks(
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        due_date=task.due_date,
        project_id=id,
        creator_id=1, 
        assignee_id=task.assignee_id
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return "Сохранено"

    
@app.get("/projects/{id}/tasks", response_model=list[tasks.TaskResponse])
def task_get_response(id: int, 
                      db: Session = Depends(get_db),
                      creator_id: int = Depends(scan_token)):
    """Получение всех тасков"""

    stmt = select(Tasks).options(joinedload(Tasks.user),
                                    joinedload(Tasks.task)).where(Tasks.id == id)
    
    result = db.execute(stmt).saclars().all()
    return result

@app.get("/tasks/{id}",response_model=tasks.TaskScheme)
def all_task(id: int, 
             db: Session = Depends(get_db)):
    """Получение одного таска"""
    stmt = select(Tasks).where(Tasks.id == id)
    result = db.execute(stmt).scalars().one_or_none()
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            details = "Пользователь не найден"
        )
    return result


@app.patch("/tasks/{id}")
def update_task(id: int, 
                task: tasks.TaskUpdate,
                db: Session = Depends(get_db)
                ):
    
    stmt = select(Tasks).where(Tasks.id == id)
    result = db.execute(stmt).scalars().one_or_none()
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail = "Пользователь не найден"
        )
    
    new_task = task.model_dump(exclude_unset = True)
 
    
    for key, value in new_task.items():   
        setattr(result,key,value)

    db.commit()
    db.refresh(result)       

    return result


@app.delete("/tasks/{id}")
def task_delete(id: int, 
                db: Session = Depends(get_db),
                creator_id: int = Depends(scan_token)):
    
    stmt = select(Tasks).where(Tasks.id == id)
    result = db.execute(stmt).scalars().one_or_none()
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail = "Таск не найдено "
        )
    result.is_deleted = True
    db.commit()
    
    return "Удалено!"

@app.patch("/tasks/{id}/history", response_model = tasks.TaskScheme)
def task_restore(id: int,
                 creator_id: int = Depends(scan_token), 
                 db: Session = Depends(get_db)):
    
    stmt = select(Tasks).where(Tasks.id == id, Tasks.is_deleted == True)
    result = db.execute(stmt).scalars().one_or_none()
    if result:
        result.is_deleted = False
        db.commit()
        db.refresh(result)
        return result
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail = "Не найдено"
    )

@app.get("/tasks/{id}/history ",respone_model = List[history.HistorySchemeResponse])
def get_task_history(id: int, db: Session = Depends(get_db)):
    stmt = select(History).options(joinedload(History.user_id),
                                   joinedload(History.task_id)).where(History.id == id)
    
    result = db.execute(stmt).scalars().all()
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail = "История пуста"
        )

    return result