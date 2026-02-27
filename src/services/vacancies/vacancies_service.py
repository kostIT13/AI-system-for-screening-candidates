from sqlalchemy.ext.asyncio import AsyncSession
from src.services.vacancies.repository import SQLAlchemyVacanciesRepository
from src.models.vacancies import Vacancies
from typing import List, Optional
import uuid


class VacancyService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = SQLAlchemyVacanciesRepository(db)

    async def get_vacancies(self, **filters) -> List[Vacancies]:
        return await self.repository.get_all(**filters)

    async def get_vacancy(self, vacancy_id: str) -> Optional[Vacancies]:
        return await self.repository.get_by_id(vacancy_id)

    async def create_vacancy(self, data: dict) -> Vacancies:
        vacancy = Vacancies(
            id=str(uuid.uuid4()),
            category=data.get('category', ''),
            title=data.get('title', data.get('category', '')),
            exp_years_min=data.get('exp_years_min'),
            exp_years_max=data.get('exp_years_max'),
            key_skills=data.get('key_skills'),
            location=data.get('location', 'Not specified'),
            salary_min=data.get('salary_min'),
            salary_max=data.get('salary_max'),
            employment=data.get('employment'),
            remote=data.get('remote'),
            summary=data.get('summary', '')[:500] if data.get('summary') else None,
            status=data.get('status', 'active')
        )
        return await self.repository.create(vacancy)

    async def update_vacancy(self, vacancy_id: str, data: dict) -> Optional[Vacancies]:
        return await self.repository.update(vacancy_id, data)

    async def delete_vacancy(self, vacancy_id: str) -> bool:
        return await self.repository.delete(vacancy_id)

    async def get_active_vacancies(self, category: Optional[str] = None) -> List[Vacancies]:
        filters = {'status': 'active'}
        if category:
            filters['category'] = category
        return await self.repository.get_all(**filters)

    async def close_vacancy(self, vacancy_id: str) -> Optional[Vacancies]:
        return await self.repository.update(vacancy_id, {'status': 'closed'})

    async def get_vacancies_by_skill(self, skill: str) -> List[Vacancies]:
        return await self.repository.get_all(key_skills=skill)