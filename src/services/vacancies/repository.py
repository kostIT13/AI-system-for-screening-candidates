from src.models.vacancies import Vacancies
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.vacancies.base import VacanciesRepository
from typing import List, Optional
from sqlalchemy import select


class SQLAlchemyVacanciesRepository(VacanciesRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self, **filters) -> List[Vacancies]:
        query = select(Vacancies)
        for field, value in filters.items():
            if hasattr(Vacancies, field):
                query = query.where(getattr(Vacancies, field) == value)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_by_id(self, vacancies_id: str) -> Optional[Vacancies]:
        query = select(Vacancies).where(Vacancies.id==vacancies_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def create(self, data: Vacancies) -> Optional[Vacancies]:
        self.session.add(data)
        await self.session.commit()
        await self.session.refresh(data)
        return data
    
    async def update(self, vacancies_id: str, data: dict) -> Optional[Vacancies]:
        vacancy = await self.get_by_id(vacancies_id)
        if not vacancy:
            return None 
        
        for field, value in data.items():
            if hasattr(vacancy, field):
                setattr(vacancy, field, value)
        await self.session.commit()
        await self.session.refresh(vacancy)
        return vacancy