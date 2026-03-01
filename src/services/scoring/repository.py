from src.services.scoring.base import ScoringRepository
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from src.models.scoring import Scoring


class SQLAlchemyScoringRepository(ScoringRepository):
    def __init__(self, session: AsyncSession):
        self.session = session 

    async def get_all(self, **filters) -> List[Scoring]:
        query = select(Scoring)
        for field, value in filters.items():
            if value is not None and hasattr(Scoring, field):
                query = query.where(getattr(Scoring, field) == value)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_by_id(self, scoring_id: str) -> Optional[Scoring]:
        query = select(Scoring).where(Scoring.id==scoring_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_candidate_id(self, candidate_id: str) -> List[Scoring]:
        query = select(Scoring).where(Scoring.candidate_id==candidate_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def create(self, data: Scoring) -> Optional[Scoring]:
        self.session.add(data)
        await self.session.commit()
        await self.session.refresh(data)
        return data
    
    async def update(self, data: Scoring, scoring_id: str) -> Optional[Scoring]:
        scoring = await self.get_by_id(scoring_id)
        if not scoring:
            return None
        for field, value in data.items():
            if hasattr(scoring, field):
                setattr(scoring, field, value)
        await self.session.commit()
        await self.session.refresh(scoring)
        return scoring
    
    async def delete(self, scoring_id: str) -> bool:
        scoring = await self.get_by_id(scoring_id)
        if not scoring:
            return False 
        await self.session.delete(scoring)
        await self.session.commit()
        return True