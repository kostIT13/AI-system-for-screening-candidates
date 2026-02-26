from src.services.candidates.base import CandidatesRepository
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from src.models.candidates import Candidates
from sqlalchemy import select


class SQLAlchemyCandidatesRepository(CandidatesRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self, **filters) -> List[Candidates]:
        query = select(Candidates)
        for field, value in filters.items():
            if hasattr(Candidates, field):
                query = query.where(getattr(Candidates, field) == value)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_by_id(self, candidate_id: str) -> Optional[Candidates]:
        query = select(Candidates).where(Candidates.id==candidate_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def create(self, data: Candidates) -> Optional[Candidates]:
        self.session.add(data)
        await self.session.commit()
        await self.session.refresh(data)
        return data
    
    async def update(self, candidate_id: str, data: dict) -> Optional[Candidates]:
        candidate = await self.get_by_id(candidate_id)
        if not candidate:
            return None 
        
        for field, value in data.items():
            if hasattr(candidate, field):
                setattr(candidate, field, value)
        await self.session.commit()
        await self.session.refresh(candidate)
        return candidate
    
    async def delete(self, candidate_id: str) -> bool:
        candidate = await self.get_by_id(candidate_id)
        if not candidate:
            return False
        await self.session.delete(candidate)
        await self.session.commit()
        return True
