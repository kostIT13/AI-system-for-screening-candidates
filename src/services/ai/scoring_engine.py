from typing import Dict, Tuple, Optional
from src.services.ai.llm_client import LLMClient
from src.services.ai.prompts.promt import SYSTEM_PROMPT
from src.services.ai.prompts.funcions_for_promts import create_matching_prompt
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

            analysis = response.get('analysis', {}) or {}
            parse_failed = str(analysis.get("error", "")).lower() == "json parse failed"

            # Some local models return score/confidence inside analysis block.
            raw_match_score = response.get('match_score', analysis.get('match_score', 0))
            raw_confidence = response.get('confidence', analysis.get('confidence', 0.0))

            try:
                match_score = float(raw_match_score)
            except (TypeError, ValueError):
                match_score = 0.0
            try:
                confidence = float(raw_confidence)
            except (TypeError, ValueError):
                confidence = 0.0

            # If model output can't be parsed as JSON, do deterministic fallback
            # instead of storing constant 50/0.5 from the client-level default.
            if parse_failed:
                fallback_score, fallback_confidence = self._fallback_scoring(candidate, vacancy)
                match_score = fallback_score
                confidence = fallback_confidence
                analysis["fallback"] = True
                analysis["fallback_reason"] = "json_parse_failed"

            analysis = self._normalize_analysis(analysis, candidate, vacancy)
            
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
            fallback_analysis = {
                'error': str(e),
                'fallback': True,
                'skills_match': 'Расчёт через fallback-алгоритм'
            }
            return match_score, confidence, self._normalize_analysis(fallback_analysis, candidate, vacancy)

    @staticmethod
    def _normalize_analysis(analysis: Dict, candidate: Candidates, vacancy: Vacancies) -> Dict:
        """Guarantee factual consistency for experience/salary/location details."""
        safe_analysis = dict(analysis or {})

        candidate_skills = {str(s).strip() for s in (candidate.key_skills or []) if str(s).strip()}
        vacancy_skills = {str(s).strip() for s in (vacancy.key_skills or []) if str(s).strip()}
        overlap = sorted(candidate_skills & vacancy_skills, key=str.lower)
        missing = sorted(vacancy_skills - candidate_skills, key=str.lower)
        if not vacancy_skills:
            skills_text = "В вакансии не указаны ключевые навыки."
        else:
            overlap_text = ", ".join(overlap) if overlap else "нет совпадений"
            missing_text = ", ".join(missing) if missing else "нет"
            skills_text = (
                f"Совпавшие навыки ({len(overlap)}/{len(vacancy_skills)}): {overlap_text}. "
                f"Недостающие навыки: {missing_text}."
            )
        safe_analysis["skills_match"] = skills_text

        candidate_exp = candidate.exp_years
        min_exp = vacancy.exp_years_min
        max_exp = vacancy.exp_years_max

        if candidate_exp is None or min_exp is None:
            exp_text = "Недостаточно данных для проверки опыта."
        elif candidate_exp < min_exp:
            if max_exp is None:
                exp_text = (
                    f"Опыт кандидата {candidate_exp} лет ниже требования вакансии (от {min_exp} лет)."
                )
            else:
                exp_text = (
                    f"Опыт кандидата {candidate_exp} лет ниже диапазона вакансии ({min_exp}-{max_exp} лет)."
                )
        elif max_exp is None or candidate_exp <= max_exp:
            if max_exp is None:
                exp_text = (
                    f"Опыт кандидата {candidate_exp} лет соответствует требованию вакансии (от {min_exp} лет)."
                )
            else:
                exp_text = (
                    f"Опыт кандидата {candidate_exp} лет находится в диапазоне вакансии ({min_exp}-{max_exp} лет)."
                )
        else:
            exp_text = (
                f"Опыт кандидата {candidate_exp} лет выше верхней границы ({max_exp} лет), "
                "но это допустимо как overqualified-профиль."
            )
        safe_analysis["experience_match"] = exp_text

        c_min, c_max = candidate.salary_min, candidate.salary_max
        v_min, v_max = vacancy.salary_min, vacancy.salary_max
        if v_min is None and v_max is None:
            salary_text = "В вакансии не указана зарплатная вилка."
        elif c_min is None and c_max is None:
            salary_text = "У кандидата не указаны зарплатные ожидания."
        else:
            cand_from = c_min if c_min is not None else c_max
            cand_to = c_max if c_max is not None else c_min
            vac_from = v_min if v_min is not None else v_max
            vac_to = v_max if v_max is not None else v_min
            overlaps = cand_from is not None and cand_to is not None and vac_from is not None and vac_to is not None and not (cand_to < vac_from or cand_from > vac_to)
            salary_text = (
                f"Ожидания кандидата ({cand_from}-{cand_to} руб.) "
                f"{'пересекаются' if overlaps else 'не пересекаются'} "
                f"с вилкой вакансии ({vac_from}-{vac_to} руб.)."
            )
        safe_analysis["salary_match"] = salary_text

        same_location = bool(candidate.location and vacancy.location and candidate.location == vacancy.location)
        remote_candidate = str(candidate.remote or "").strip().lower() in {"да", "yes", "true", "1", "remote", "гибрид"}
        remote_vacancy = str(vacancy.remote or "").strip().lower() in {"да", "yes", "true", "1", "remote", "гибрид"}
        if same_location:
            location_text = f"Локация совпадает: {candidate.location}."
        elif remote_candidate or remote_vacancy:
            location_text = "Локация отличается, но удалённый/гибридный формат допускает совместимость."
        else:
            location_text = f"Локация не совпадает ({candidate.location} vs {vacancy.location})."
        safe_analysis["location_match"] = location_text

        safe_analysis.setdefault("strengths", [])
        safe_analysis.setdefault("weaknesses", [])
        return safe_analysis
    
    
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