from fastapi import Depends, HTTPException, FastAPI, status
from database.db import get_db
from datetime import datetime,timezone,timedelta
from schemas.tasks import TaskScheme, ProjectCreate, TaskResponse, TaskUpdate
from sqlalchemy import select, insert
from sqlalchemy.orm import Session, joinedload
from models.models import Tasks, Projects
from app.auth import scan_token

app = FastAPI()


@app.post("/projects/{id}/tasks", status_code = status.HTTP_201_CREATED) 
def create_task(task: TaskScheme, id: int,
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

    
@app.get("/projects/{id}/tasks", response_model=list[TaskResponse])
def task_get_response(id: int, 
                      db: Session = Depends(get_db),
                      creator_id: int = Depends(scan_token)):
    """Получение всех тасков"""

    stmt = select(Tasks).options(joinedload(Tasks.user),
                                    joinedload(Tasks.task)).where(Tasks.id == id)
    
    result = db.execute(stmt).saclars().all()
    return result

@app.get("/tasks/{id}",response_model=TaskScheme)
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
                task: TaskUpdate,
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


@app.