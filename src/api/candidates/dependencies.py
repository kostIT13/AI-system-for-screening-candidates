from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db
from src.services.candidates.candidate_service import CandidateService
from typing import Annotated
from fastapi import Depends


async def get_candidate_service(db: AsyncSession = Depends(get_db)) -> CandidateService:
    return CandidateService(db)

CandidatesServiceDependency = Annotated[CandidateService, Depends(get_candidate_service)]
