from abc import ABC, abstractmethod
from typing import Optional, List
from src.models.vacancies import Vacancies

class VacanciesRepository(ABC):

    @abstractmethod
    async def get_all(self, **filters) -> List[Vacancies]:
        raise NotImplementedError
    
    @abstractmethod
    async def get_by_id(self, vacancy_id: str) -> Optional[Vacancies]:
        raise NotImplementedError
    
    @abstractmethod
    async def create(self, data: Vacancies) -> Optional[Vacancies]:
        raise NotImplementedError
    
    @abstractmethod
    async def update(self, vacancy_id: str, data: dict) -> Optional[Vacancies]:
        raise NotImplementedError
    
    @abstractmethod
    async def delete(self, vacancy_id: str) -> bool:
        raise NotImplementedError