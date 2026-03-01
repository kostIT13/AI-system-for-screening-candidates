from abc import ABC, abstractmethod
from src.models.scoring import Scoring
from typing import List, Optional

class ScoringRepository(ABC):
    
    @abstractmethod
    async def get_all(self, **filters) -> List[Scoring]:
        return NotImplemented
    
    @abstractmethod
    async def get_by_id(self, scoring_id: str) -> Optional[Scoring]:
        raise NotImplementedError
    
    @abstractmethod
    async def get_by_candidate_id(self, candidate_id: str) -> List[Scoring]:
        return NotImplementedError
    
    @abstractmethod
    async def create(self, data: Scoring) -> Optional[Scoring]:
        raise NotImplementedError
    
    @abstractmethod
    async def update(self, scoring_id: str, data: dict) -> Optional[Scoring]:
        raise NotImplementedError
    
    @abstractmethod
    async def delete(self, scoring_id: str) -> bool:
        raise NotImplementedError
    