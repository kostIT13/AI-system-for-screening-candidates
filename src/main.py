from fastapi import FastAPI
import logging
import os
from src.core.logging_settings import setup_logging
from contextlib import asynccontextmanager
from src.core.database import engine
from src.api.candidates.endpoints import router as candidates_router
from src.api.vacancies.endpoints import router as vacancies_router
from src.api.scoring.endpoints import router as scoring_router


setup_logging(level=os.getenv("LOG_LEVEL", "INFO"))

logger = logging.getLogger(__name__)

app = FastAPI(titel="AI Candidate Screening")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Приложение запущено")
    
    try:
        async with engine.connect() as conn:
            await conn.execute(lambda c: c.execute("SELECT 1"))
        logger.info("БД доступна")
    except Exception as e:
        logger.error(f"Ошибка подключения к БД: {e}")
    
    yield
    
    logger.info("Остановка...")
    await engine.dispose() 
    logger.info("Готово")


app.include_router(router=candidates_router)
app.include_router(router=vacancies_router)
app.include_router(router=scoring_router)

