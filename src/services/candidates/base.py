from abc import ABC, abstractmethod
from typing import Optional, List
from src.models.candidates import Candidates

class CandidatesRepository(ABC):

    @abstractmethod
    async def get_all(self, **filters) -> List[Candidates]:
        raise NotImplementedError
    
    @abstractmethod
    async def get_by_id(self, candidate_id: str) -> Optional[Candidates]:
        raise NotImplementedError
    
    @abstractmethod
    async def create(self, data: Candidates) -> Optional[Candidates]:
        raise NotImplementedError
    
    @abstractmethod
    async def update(self, candidate_id: str, data: dict) -> Optional[Candidates]:
        raise NotImplementedError
    
    @abstractmethod
    async def delete(self, candidate_id: str) -> bool:
        raise NotImplementedError