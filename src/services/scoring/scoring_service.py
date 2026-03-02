from sqlalchemy.ext.asyncio import AsyncSession
from src.services.scoring.repository import SQLAlchemyScoringRepository
from src.services.candidates.candidate_service import CandidateService
from src.services.vacancies.vacancies_service import VacancyService
from src.services.ai.scoring_engine import ScoringEngine
from src.models.scoring import Scoring
from typing import List, Optional, Dict
import uuid
import csv
import io
from datetime import datetime


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

    async def export_scores_to_csv(
        self,
        candidate_id: Optional[str] = None,
        vacancy_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        min_score: Optional[float] = None,
        limit: int = 10000
    ) -> str:

        filters = {}
        if candidate_id:
            filters['candidate_id'] = candidate_id
        if vacancy_id:
            filters['vacancy_id'] = vacancy_id
        
        scores = await self.repository.get_all(limit=limit, **filters)
        
        if date_from or date_to or min_score is not None:
            filtered = []
            for s in scores:
                if date_from and s.created_at < date_from:
                    continue
                if date_to and s.created_at > date_to:
                    continue
                if min_score is not None and s.match_score < min_score:
                    continue
                filtered.append(s)
            scores = filtered
        
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
        
        writer.writerow([
            'scoring_id',
            'candidate_id',
            'candidate_title',
            'candidate_category',
            'vacancy_id',
            'vacancy_title',
            'vacancy_category',
            'match_score',
            'confidence',
            'skills_match',
            'experience_match',
            'salary_match',
            'location_match',
            'recommendation',
            'strengths',
            'weaknesses',
            'created_at',
            'method'
        ])
   
        for score in scores:
            candidate = await self.candidate_service.get_candidate(score.candidate_id)
            vacancy = await self.vacancy_service.get_vacancy(score.vacancy_id)
            
            analysis = score.analysis or {}
            
            writer.writerow([
                score.id,
                score.candidate_id,
                candidate.title if candidate else 'N/A',
                candidate.category if candidate else 'N/A',
                score.vacancy_id,
                vacancy.title if vacancy else 'N/A',
                vacancy.category if vacancy else 'N/A',
                score.match_score,
                score.confidence,
                analysis.get('skills_match', ''),
                analysis.get('experience_match', ''),
                analysis.get('salary_match', ''),
                analysis.get('location_match', ''),
                analysis.get('recommendation', self.get_recommendation(score.match_score)),
                '; '.join(analysis.get('strengths', [])),
                '; '.join(analysis.get('weaknesses', [])),
                score.created_at.isoformat(),
                analysis.get('method', 'unknown')
            ])
        
        return output.getvalue()

    @staticmethod
    def get_recommendation(match_score: float) -> str:
        if match_score >= 80:
            return "hire"
        elif match_score >= 50:
            return "consider"
        else:
            return "reject"