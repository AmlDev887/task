from fastapi import Depends, APIRouter
from datetime import datetime,timezone,timedelta
from app.database.db import get_db
from app.models.models import Users
from app.schemas.users import AddUser, UserLogin
from app.schemas import auth
from sqlalchemy.ext.asyncio import AsyncSession
from app.core import security
from app.config import settings
from app.database.db import get_db
import jwt

router = APIRouter(
    prefix="/user",
    tags=["user"]
)

def full_token(user_id):
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    access_token = jwt.encode({"user_id":str(user_id), "exp":expire, "type":"access"},settings.SECRET_KEY,algorithm="HS256")

    expire_1 = datetime.now(timezone.utc) + timedelta(days=7)
    refresh_token = jwt.encode({"user_id":str(user_id), "exp":expire_1, "type":"refresh"},settings.SECRET_KEY_2,algorithm="HS256")

    return {
        "access_token":access_token,
        "refresh_token":refresh_token,
        "token_type":"bearer"
    }

@router.post("/register",response_model = AddUser)
async def add(new_user: UserLogin, db: AsyncSession = Depends(get_db)):
    """Создание нового User"""
    
    data = new_user.model_dump()
    data["hashed_password"] = security.heshing_password(data["password"])
    del data["password"]

    answer = Users(**data)
    db.add(answer)
    await db.commit()
    await db.refresh(answer)

    result = email_code()

    return result

@router.post("/verify")
async def email_verify(email:auth.EmailVerify, 
                       db: AsyncSession = Depends(get_db)):
    

@router.get("/user_info",response_model = )
async def user_info(user:,
                    user_id:
                    db:AsyncSession = Depends(get_db)):

    

