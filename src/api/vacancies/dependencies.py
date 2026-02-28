from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from src.core.database import get_db
from src.services.vacancies.vacancies_service import VacancyService
from typing import Annotated


async def get_vacancy_service(db: AsyncSession = Depends(get_db)) -> VacancyService:
    return VacancyService(get_db)


VacancyServiceDependency = Annotated[VacancyService, Depends(get_vacancy_service)]