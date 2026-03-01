from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db 
from fastapi import Depends
from src.services.scoring.scoring_service import ScoringService
from typing import Annotated


async def get_scoring_service(db: AsyncSession = Depends(get_db)):
    return ScoringService(db)

ScoringServiceDependency = Annotated[ScoringService, Depends(get_scoring_service)]