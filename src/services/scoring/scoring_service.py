from sqlalchemy.ext.asyncio import AsyncSession
from src.services.scoring.repository import SQLAlchemyScoringRepository
from src.services.candidates.candidate_service import CandidateService
from src.services.vacancies.vacancies_service import VacancyService
from src.services.ai.scoring_engine import ScoringEngine
from src.models.scoring import Scoring
from typing import List, Optional, Dict
import uuid


class ScoringService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = SQLAlchemyScoringRepository(db)
        self.candidate_service = CandidateService(db)
        self.vacancy_service = VacancyService(db)
        self.scoring_engine = ScoringEngine()

    async def calculate_match(
        self, 
        candidate_id: str, 
        vacancy_id: str
    ) -> Scoring:
        candidate = await self.candidate_service.get_candidate(candidate_id)
        vacancy = await self.vacancy_service.get_vacancy(vacancy_id)
        
        if not candidate or not vacancy:
            raise ValueError("Candidate or Vacancy not found")
        
        match_score, confidence, analysis = await self.scoring_engine.calculate_match(
            candidate, vacancy
        )
        
        scoring = Scoring(
            id=str(uuid.uuid4()),
            candidate_id=candidate_id,
            vacancy_id=vacancy_id,
            match_score=match_score,
            confidence=confidence,
            analysis=analysis,
            llm_raw_response=None
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
            try:
                scoring = await self.calculate_match(
                    candidate_id=candidate_id,
                    vacancy_id=vacancy.id
                )
                results.append(scoring)
            except Exception as e:
                print(f"Error scoring vacancy {vacancy.id}: {e}")
                continue
        
        return results

    async def batch_score_vacancy(self, vacancy_id: str) -> List[Scoring]:
        """Массовый скоринг вакансии по всем кандидатам"""
        vacancy = await self.vacancy_service.get_vacancy(vacancy_id)
        if not vacancy:
            raise ValueError("Vacancy not found")
        
        all_candidates = await self.candidate_service.get_candidates(limit=1000)
        results = []
        
        for candidate in all_candidates:
            try:
                scoring = await self.calculate_match(
                    candidate_id=candidate.id,
                    vacancy_id=vacancy_id
                )
                results.append(scoring)
            except Exception as e:
                print(f"Error scoring candidate {candidate.id}: {e}")
                continue
        
        return results