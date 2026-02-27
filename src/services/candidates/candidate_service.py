from sqlalchemy.ext.asyncio import AsyncSession
from src.services.candidates.repository import SQLAlchemyCandidatesRepository
from src.models.candidates import Candidates
from typing import List, Optional
import uuid


class CandidateService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = SQLAlchemyCandidatesRepository(db)

    async def get_candidates(self, **filters) -> List[Candidates]:
        return await self.repository.get_all(**filters)

    async def get_candidate(self, candidate_id: str) -> Optional[Candidates]:
        return await self.repository.get_by_id(candidate_id)

    async def create_candidate(self, data: dict) -> Candidates:
        candidate = Candidates(
            id=str(uuid.uuid4()),
            category=data.get('category', ''),
            title=data.get('title', data.get('category', '')),
            exp_years=data.get('exp_years'),
            key_skills=data.get('key_skills'),
            location=data.get('location', 'Not specified'),
            salary_min=data.get('salary_min'),
            salary_max=data.get('salary_max'),
            employment=data.get('employment'),
            remote=data.get('remote'),
            summary=data.get('summary', '')[:500] if data.get('summary') else None
        )
        return await self.repository.create(candidate)

    async def update_candidate(self, candidate_id: str, data: dict) -> Optional[Candidates]:
        return await self.repository.update(candidate_id, data)

    async def delete_candidate(self, candidate_id: str) -> bool:
        return await self.repository.delete(candidate_id)

    async def get_candidates_by_skill(self, skill: str) -> List[Candidates]:
        return await self.repository.get_all(key_skills=skill)

    async def get_candidates_by_category(self, category: str) -> List[Candidates]:
        return await self.repository.get_all(category=category)