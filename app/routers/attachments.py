from fastapi import Depends, APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from app.database.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import ProjectMembers, Tasks, Attachments
from app.core import security   
from app.schemas import roles
from sqlalchemy import select

router = APIRouter(prefix="/attachments",
                   tags=["attachments"])

@router.get("/{id}")
async def get_file(id: int,
                   user_id: int = Depends(security.scan_token),
                   db: AsyncSession = Depends(get_db)):
    """Скачивание файла"""

    stmt = select(Attachments).where(Attachments.id == id)
    result = await db.execute(stmt)
    answer = result.scalars().one_or_none()

    if answer is None:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail = "Файл не найден"
        )
    stmt_1 = select(Tasks).where(Tasks.id == answer.task_id)
    result_1 = await db.execute(stmt_1)
    answer_1 = result_1.scalars().one_or_none()

    if answer_1 is None:   
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail = "Таск не найден"
        )
    
    pro_id = answer_1.project_id
    georg = select(ProjectMembers).where(ProjectMembers.project_id == pro_id,
                                            ProjectMembers.user_id == user_id)

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
    
    return FileResponse(
            path=answer.path,
            filename=answer.filename,
            media_type=answer.content_type
)