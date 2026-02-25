from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from typing import Annotated, AsyncGenerator
from fastapi import Depends
from src.core.config import DATABASE_URL
import os 
import logging


logger = logging.getLogger(__name__)

engine = create_async_engine(DATABASE_URL, echo=True)

async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()  
            logger.debug("Транзакция зафиксирована")
        except Exception as e:
            await session.rollback()
            logger.error(f"Ошибка транзакции: {e}", exc_info=True)
            raise
        finally:
            await session.close()
    
SessionDep = Annotated[AsyncSession, Depends(get_db)]