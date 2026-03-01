from typing import Dict, Tuple, Optional
from src.services.ai.llm_client import LLMClient
from src.services.ai.promts.promt import SYSTEM_PROMPT
from src.services.ai.promts.funcions_for_promts import create_matching_prompt
from src.models.candidates import Candidates
from src.models.vacancies import Vacancies
import logging

logger = logging.getLogger(__name__)


class ScoringEngine:
    def __init__(self):
        self.llm_client = LLMClient()
    
    @staticmethod
    def _candidate_to_dict(candidate: Candidates) -> Dict:
        return {
            'id': candidate.id,
            'title': candidate.title,
            'category': candidate.category,
            'exp_years': candidate.exp_years,
            'key_skills': candidate.key_skills or [],
            'location': candidate.location,
            'salary_min': candidate.salary_min,
            'salary_max': candidate.salary_max,
            'employment': candidate.employment,
            'remote': candidate.remote,
            'summary': candidate.summary
        }
    
    @staticmethod
    def _vacancy_to_dict(vacancy: Vacancies) -> Dict:
        return {
            'id': vacancy.id,
            'title': vacancy.title,
            'category': vacancy.category,
            'exp_years_min': vacancy.exp_years_min,
            'exp_years_max': vacancy.exp_years_max,
            'key_skills': vacancy.key_skills or [],
            'location': vacancy.location,
            'salary_min': vacancy.salary_min,
            'salary_max': vacancy.salary_max,
            'employment': vacancy.employment,
            'remote': vacancy.remote,
            'summary': vacancy.summary
        }
    
    
    async def calculate_match(
        self, 
        candidate: Candidates, 
        vacancy: Vacancies
    ) -> Tuple[float, float, Dict]:
        
        candidate_dict = self._candidate_to_dict(candidate)
        vacancy_dict = self._vacancy_to_dict(vacancy)
        
        prompt = create_matching_prompt(candidate_dict, vacancy_dict)
        
        try:
            response = await self.llm_client.generate_json_response(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT
            )
            
            match_score = float(response.get('match_score', 0))
            confidence = float(response.get('confidence', 0.0))
            analysis = response.get('analysis', {})
            
            match_score = max(0, min(100, match_score))
            confidence = max(0.0, min(1.0, confidence))
            
            logger.debug(
                f"Scoring: candidate={candidate.id[:8]}..., "
                f"vacancy={vacancy.id[:8]}..., "
                f"score={match_score}, confidence={confidence}"
            )
            
            return match_score, confidence, analysis
            
        except Exception as e:
            logger.warning(f"LLM scoring failed, using fallback: {e}")
            match_score, confidence = self._fallback_scoring(candidate, vacancy)
            return match_score, confidence, {
                'error': str(e),
                'fallback': True,
                'skills_match': 'Расчёт через fallback-алгоритм'
            }
    
    
    @staticmethod
    def _fallback_scoring(
        candidate: Candidates, 
        vacancy: Vacancies
    ) -> Tuple[float, float]:
        
        score = 0.0
        
        candidate_skills = set(candidate.key_skills or [])
        vacancy_skills = set(vacancy.key_skills or [])
        
        if vacancy_skills:
            skills_overlap = len(candidate_skills & vacancy_skills)
            skills_score = (skills_overlap / len(vacancy_skills)) * 40
            score += skills_score
        
        if candidate.exp_years and vacancy.exp_years_min:
            if vacancy.exp_years_max:
                if vacancy.exp_years_min <= candidate.exp_years <= vacancy.exp_years_max:
                    score += 25
                elif candidate.exp_years >= vacancy.exp_years_min * 0.8:
                    score += 15 
                else:
                    score += 5
            else:
                if candidate.exp_years >= vacancy.exp_years_min:
                    score += 25
                elif candidate.exp_years >= vacancy.exp_years_min * 0.7:
                    score += 15
                else:
                    score += 5
        
        if vacancy.salary_min and vacancy.salary_max:
            candidate_expected = candidate.salary_min or candidate.salary_max or 0
            if vacancy.salary_min <= candidate_expected <= vacancy.salary_max:
                score += 15
            elif candidate_expected <= vacancy.salary_max * 1.3:
                score += 10
            else:
                score += 5
        
        if candidate.location == vacancy.location:
            score += 10
        elif vacancy.remote == 'Да' or candidate.remote == 'Да':
            score += 10
        elif 'Регионы' in str(candidate.location) or 'Регионы' in str(vacancy.location):
            score += 5
        
        if candidate.employment == vacancy.employment:
            score += 10
        elif vacancy.employment == 'Полная':
            score += 5 
        
        confidence = 0.65
        
        return round(score, 2), confidence
    
    
    @staticmethod
    def get_recommendation(match_score: float) -> str:
        if match_score >= 80:
            return "hire"
        elif match_score >= 50:
            return "consider"
        else:
            return "reject"
    
    @staticmethod
    def format_analysis_for_display(analysis: Dict) -> str:
   
        lines = []
        
        if analysis.get('skills_match'):
            lines.append(f"Навыки: {analysis['skills_match']}")
        if analysis.get('experience_match'):
            lines.append(f"Опыт: {analysis['experience_match']}")
        if analysis.get('salary_match'):
            lines.append(f"Зарплата: {analysis['salary_match']}")
        if analysis.get('location_match'):
            lines.append(f"Локация: {analysis['location_match']}")
        
        if analysis.get('strengths'):
            lines.append(f"Сильные стороны: {', '.join(analysis['strengths'])}")
        if analysis.get('weaknesses'):
            lines.append(f"Слабые стороны: {', '.join(analysis['weaknesses'])}")
        
        if analysis.get('recommendation'):
            rec = analysis['recommendation'].upper()
            lines.append(f"Рекомендация: {rec}")
        
        return "\n".join(lines) if lines else "Анализ недоступен"