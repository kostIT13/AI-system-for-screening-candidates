from sqlalchemy.ext.asyncio import AsyncSession
from src.services.scoring.repository import SQLAlchemyScoringRepository
from src.services.candidates.candidate_service import CandidateService
from src.services.vacancies.vacancies_service import VacancyService
from src.models.scoring import Scoring
from typing import List, Optional, Dict
import uuid
import json


class ScoringService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = SQLAlchemyScoringRepository(db)
        self.candidate_service = CandidateService(db)
        self.vacancy_service = VacancyService(db)

    async def calculate_match(
        self, 
        candidate_id: str, 
        vacancy_id: str,
        llm_response: Optional[str] = None,
        analysis: Optional[Dict] = None
    ) -> Scoring:
        candidate = await self.candidate_service.get_candidate(candidate_id)
        vacancy = await self.vacancy_service.get_vacancy(vacancy_id)
        
        if not candidate or not vacancy:
            raise ValueError("Candidate or Vacancy not found")
        
        match_score = analysis.get('match_score', 0) if analysis else 0
        confidence = analysis.get('confidence', 0.0) if analysis else 0.0
        
        scoring = Scoring(
            id=str(uuid.uuid4()),
            candidate_id=candidate_id,
            vacancy_id=vacancy_id,
            match_score=match_score,
            confidence=confidence,
            analysis=analysis,
            llm_raw_response=llm_response
        )
        
        return await self.repository.create(scoring)

    async def get_scoring(self, scoring_id: str) -> Optional[Scoring]:
        return await self.repository.get_by_id(scoring_id)

    async def get_candidate_scores(self, candidate_id: str) -> List[Scoring]:
        return await self.repository.get_by_candidate_id(candidate_id)

    async def get_vacancy_scores(self, vacancy_id: str) -> List[Scoring]:
        return await self.repository.get_by_vacancy_id(vacancy_id)

    async def get_best_matches_for_candidate(
        self, 
        candidate_id: str, 
        limit: int = 5
    ) -> List[Scoring]:
        scores = await self.repository.get_by_candidate_id(candidate_id)
        return sorted(scores, key=lambda x: x.match_score, reverse=True)[:limit]

    async def get_best_candidates_for_vacancy(
        self, 
        vacancy_id: str, 
        limit: int = 5
    ) -> List[Scoring]:
        scores = await self.repository.get_by_vacancy_id(vacancy_id)
        return sorted(scores, key=lambda x: x.match_score, reverse=True)[:limit]

    async def delete_scoring(self, scoring_id: str) -> bool:
        return await self.repository.delete(scoring_id)

    async def batch_score_candidate(self, candidate_id: str) -> List[Scoring]:
        candidate = await self.candidate_service.get_candidate(candidate_id)
        if not candidate:
            raise ValueError("Candidate not found")
        
        active_vacancies = await self.vacancy_service.get_active_vacancies()
        results = []
        
        for vacancy in active_vacancies:
            analysis = {'match_score': 0, 'confidence': 0.0}
            
            scoring = await self.calculate_match(
                candidate_id=candidate_id,
                vacancy_id=vacancy.id,
                analysis=analysis
            )
            results.append(scoring)
        
        return results

    async def batch_score_vacancy(self, vacancy_id: str) -> List[Scoring]:
        vacancy = await self.vacancy_service.get_vacancy(vacancy_id)
        if not vacancy:
            raise ValueError("Vacancy not found")
    
        all_candidates = await self.candidate_service.get_candidates(limit=1000)
        results = []
        
        for candidate in all_candidates:
            analysis = {'match_score': 0, 'confidence': 0.0}
            
            scoring = await self.calculate_match(
                candidate_id=candidate.id,
                vacancy_id=vacancy_id,
                analysis=analysis
            )
            results.append(scoring)
        
        return results