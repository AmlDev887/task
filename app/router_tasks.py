from fastapi import Depends, HTTPException, FastAPI, status
from database.db import get_db
from datetime import datetime,timezone,timedelta
from schemas.schemas_task import TaskScheme, ProjectCreate, TaskResponse
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

    
@app.get("/projects/{id}/tasks", response_model=TaskResponse)
def task_get_response(id: int, 
                      db: Session = Depends(get_db),
                      creator_id: int = Depends(scan_token)):

    stmt = select(Tasks).options(joinedload(Tasks.user),
                                    joinedload(Tasks.task)).where(Tasks.id == id)
    
    result = db.execute(stmt).saclars().all()
    return result




    
