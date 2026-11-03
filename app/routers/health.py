from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from redis.exceptions import RedisError

from app.database.db import get_db
from core.redis import redis_async

router = APIRouter(
    prefix="/health",
    tags=["health"]
)


@router.get("/")
async def scanner_db(db: AsyncSession = Depends(get_db)):
    db_st = "OK"
    redis_st = "OK"

    try:
        await db.execute(select(1))
    except SQLAlchemyError:
        db_st = "error"

    try:
        response = await redis_async.ping()
        if not response:
            redis_st = "error"
    
    except RedisError:
        redis_st = "error"

    healthy = db_st == "OK" and redis_st == "OK"

    return {
        "status": "healthy" if healthy else "unhealthy",
        "postgresql": db_st,
        "redis": redis_st
    }