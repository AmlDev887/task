from app.config import settings
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
)

engine = create_async_engine(settings.ASYNC_DATABASE_URI, echo=False)

SessionLocal = async_sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

async def get_db():
    async with SessionLocal() as db:
        yield db







