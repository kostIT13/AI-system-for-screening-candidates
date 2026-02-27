from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db
from src.services.candidates.candidate_service import CandidateService


async def get_candidate_service(db: AsyncSession = get_db) -> CandidateService:
    return CandidateService(db)