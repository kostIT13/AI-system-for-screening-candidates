import logging
import os
from dotenv import load_dotenv
from typing import Optional
import sys
from src.core.logging_settings import setup_logging
from src.core.settings_llm import get_llm_settings


load_dotenv()

setup_logging(level=os.getenv("LOG_LEVEL", "INFO"))

logger = logging.getLogger(__name__)

DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    POSTGRES_USER = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_DB = os.getenv("POSTGRES_DB")

    if not all([POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB]):
        logger.error("Отсутсвуют переменные окружения")
        raise ValueError("Отсутствуют необходимые переменные окружения для подключения к БД")

    DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:5432/{POSTGRES_DB}"

if not DATABASE_URL:
    logger.error("Ошибка конфигурации")
    raise ValueError(f"Ошибка конфигурации: DATABASE_URL содержит None -> {DATABASE_URL}")


logger.info("Подключение к БД настроено")

llm_settings = get_llm_settings()
logger.info(f"LLM настроен: model={llm_settings.OPENROUTER_MODEL}")

__all__ = ["DATABASE_URL", "llm_settings", "logger"]
