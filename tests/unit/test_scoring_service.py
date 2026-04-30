import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.scoring.scoring_service import ScoringService
from src.models.scoring import Scoring
from src.models.candidates import Candidates
from src.models.vacancies import Vacancies
import uuid
from datetime import datetime


class TestScoringService:

    @pytest_asyncio.fixture
    async def mock_session(self):
        return AsyncMock(spec=AsyncSession)

    @pytest_asyncio.fixture
    async def service(self, mock_session):
        return ScoringService(mock_session)

    @pytest_asyncio.fixture
    def mock_candidate(self):
        candidate = MagicMock(spec=Candidates)
        candidate.id = "candidate-123"
        candidate.title = "Senior Python Developer"
        candidate.category = "IT"
        candidate.skills = "Python, FastAPI, PostgreSQL"
        candidate.experience_years = 5
        candidate.salary_expectations = 150000
        candidate.location = "Москва"
        candidate.remote = "hybrid"
        return candidate

    @pytest_asyncio.fixture
    def mock_vacancy(self):
        vacancy = MagicMock(spec=Vacancies)
        vacancy.id = "vacancy-456"
        vacancy.title = "Python Backend Developer"
        vacancy.category = "IT"
        vacancy.required_skills = "Python, FastAPI, Docker"
        vacancy.min_experience = 3
        vacancy.salary_range = "120000-180000"
        vacancy.location = "Москва"
        vacancy.remote = True
        vacancy.is_active = True
        return vacancy

    @pytest_asyncio.fixture
    def mock_scoring(self):
        scoring = MagicMock(spec=Scoring)
        scoring.id = "scoring-789"
        scoring.candidate_id = "candidate-123"
        scoring.vacancy_id = "vacancy-456"
        scoring.match_score = 85.5
        scoring.confidence = 0.9
        scoring.analysis = {
            "skills_match": 90,
            "experience_match": 80,
            "salary_match": 70,
            "location_match": 100,
            "recommendation": "hire",
            "strengths": ["Опыт работы", "Навыки Python"],
            "weaknesses": ["Отсутствие Docker"],
            "method": "llm"
        }
        scoring.created_at = datetime.now()
        return scoring

    @pytest.mark.asyncio
    async def test_calculate_match_success(self, service, mock_session, mock_candidate, mock_vacancy, mock_scoring):
        candidate_id = "candidate-123"
        vacancy_id = "vacancy-456"
        
        with patch.object(service.candidate_service, 'get_candidate', AsyncMock(return_value=mock_candidate)), \
             patch.object(service.vacancy_service, 'get_vacancy', AsyncMock(return_value=mock_vacancy)), \
             patch.object(service.scoring_engine, 'calculate_match', AsyncMock(return_value=(85.5, 0.9, {"analysis": "data"}))), \
             patch.object(service.repository, 'create', AsyncMock(return_value=mock_scoring)):
            
            result = await service.calculate_match(candidate_id, vacancy_id)
            
            assert result == mock_scoring
            service.candidate_service.get_candidate.assert_called_once_with(candidate_id)
            service.vacancy_service.get_vacancy.assert_called_once_with(vacancy_id)
            service.scoring_engine.calculate_match.assert_called_once_with(mock_candidate, mock_vacancy)
            service.repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_calculate_match_candidate_not_found(self, service, mock_session):
        candidate_id = "candidate-123"
        vacancy_id = "vacancy-456"
        
        with patch.object(service.candidate_service, 'get_candidate', AsyncMock(return_value=None)):
            with pytest.raises(ValueError, match="Candidate or Vacancy not found"):
                await service.calculate_match(candidate_id, vacancy_id)

    @pytest.mark.asyncio
    async def test_calculate_match_vacancy_not_found(self, service, mock_session, mock_candidate):
        candidate_id = "candidate-123"
        vacancy_id = "vacancy-456"
        
        with patch.object(service.candidate_service, 'get_candidate', AsyncMock(return_value=mock_candidate)), \
             patch.object(service.vacancy_service, 'get_vacancy', AsyncMock(return_value=None)):
            
            with pytest.raises(ValueError, match="Candidate or Vacancy not found"):
                await service.calculate_match(candidate_id, vacancy_id)

    @pytest.mark.asyncio
    async def test_get_scoring_found(self, service, mock_session, mock_scoring):
        scoring_id = "scoring-789"
        
        with patch.object(service.repository, 'get_by_id', AsyncMock(return_value=mock_scoring)):
            result = await service.get_scoring(scoring_id)
            
            assert result == mock_scoring
            service.repository.get_by_id.assert_called_once_with(scoring_id)

    @pytest.mark.asyncio
    async def test_get_scoring_not_found(self, service, mock_session):
        scoring_id = "scoring-789"
        
        with patch.object(service.repository, 'get_by_id', AsyncMock(return_value=None)):
            result = await service.get_scoring(scoring_id)
            
            assert result is None
            service.repository.get_by_id.assert_called_once_with(scoring_id)

    @pytest.mark.asyncio
    async def test_get_candidate_scores(self, service, mock_session, mock_scoring):
        candidate_id = "candidate-123"
        mock_scores = [mock_scoring, mock_scoring]
        
        with patch.object(service.repository, 'get_by_candidate_id', AsyncMock(return_value=mock_scores)):
            result = await service.get_candidate_scores(candidate_id)
            
            assert result == mock_scores
            service.repository.get_by_candidate_id.assert_called_once_with(candidate_id)

    @pytest.mark.asyncio
    async def test_get_vacancy_scores(self, service, mock_session, mock_scoring):
        vacancy_id = "vacancy-456"
        mock_scores = [mock_scoring]
        
        with patch.object(service.repository, 'get_by_vacancy_id', AsyncMock(return_value=mock_scores)):
            result = await service.get_vacancy_scores(vacancy_id)
            
            assert result == mock_scores
            service.repository.get_by_vacancy_id.assert_called_once_with(vacancy_id)

    @pytest.mark.asyncio
    async def test_get_best_matches_for_candidate(self, service, mock_session, mock_scoring):
        candidate_id = "candidate-123"
        limit = 3
        mock_scores = [
            MagicMock(match_score=90.0),
            MagicMock(match_score=85.0),
            MagicMock(match_score=70.0),
            MagicMock(match_score=60.0),
        ]
        
        with patch.object(service.repository, 'get_by_candidate_id', AsyncMock(return_value=mock_scores)):
            result = await service.get_best_matches_for_candidate(candidate_id, limit)
            
            assert len(result) == limit
            assert result[0].match_score == 90.0
            assert result[1].match_score == 85.0
            assert result[2].match_score == 70.0
            service.repository.get_by_candidate_id.assert_called_once_with(candidate_id)

    @pytest.mark.asyncio
    async def test_get_best_candidates_for_vacancy(self, service, mock_session, mock_scoring):
        vacancy_id = "vacancy-456"
        limit = 2
        mock_scores = [
            MagicMock(match_score=95.0),
            MagicMock(match_score=80.0),
            MagicMock(match_score=75.0),
        ]
        
        with patch.object(service.repository, 'get_by_vacancy_id', AsyncMock(return_value=mock_scores)):
            result = await service.get_best_candidates_for_vacancy(vacancy_id, limit)
            
            assert len(result) == limit
            assert result[0].match_score == 95.0
            assert result[1].match_score == 80.0
            service.repository.get_by_vacancy_id.assert_called_once_with(vacancy_id)

    @pytest.mark.asyncio
    async def test_delete_scoring_success(self, service, mock_session):
        scoring_id = "scoring-789"
        
        with patch.object(service.repository, 'delete', AsyncMock(return_value=True)):
            result = await service.delete_scoring(scoring_id)
            
            assert result is True
            service.repository.delete.assert_called_once_with(scoring_id)

    @pytest.mark.asyncio
    async def test_delete_scoring_failure(self, service, mock_session):
        scoring_id = "scoring-789"
        
        with patch.object(service.repository, 'delete', AsyncMock(return_value=False)):
            result = await service.delete_scoring(scoring_id)
            
            assert result is False
            service.repository.delete.assert_called_once_with(scoring_id)

    @pytest.mark.asyncio
    async def test_batch_score_candidate_success(self, service, mock_session, mock_candidate):
        candidate_id = "candidate-123"
        mock_vacancies = [
            MagicMock(id="vacancy-1", is_active=True),
            MagicMock(id="vacancy-2", is_active=True),
        ]
        
        with patch.object(service.candidate_service, 'get_candidate', AsyncMock(return_value=mock_candidate)), \
             patch.object(service.vacancy_service, 'get_active_vacancies', AsyncMock(return_value=mock_vacancies)), \
             patch.object(service, 'calculate_match', AsyncMock(side_effect=[
                 MagicMock(id="scoring-1"),
                 MagicMock(id="scoring-2"),
             ])):
            
            result = await service.batch_score_candidate(candidate_id)
            
            assert len(result) == 2
            assert result[0].id == "scoring-1"
            assert result[1].id == "scoring-2"
            service.candidate_service.get_candidate.assert_called_once_with(candidate_id)
            service.vacancy_service.get_active_vacancies.assert_called_once()
            assert service.calculate_match.call_count == 2

    @pytest.mark.asyncio
    async def test_batch_score_candidate_not_found(self, service, mock_session):
        candidate_id = "candidate-123"
        
        with patch.object(service.candidate_service, 'get_candidate', AsyncMock(return_value=None)):
            with pytest.raises(ValueError, match="Candidate not found"):
                await service.batch_score_candidate(candidate_id)

    @pytest.mark.asyncio
    async def test_batch_score_candidate_with_error(self, service, mock_session, mock_candidate):
        candidate_id = "candidate-123"
        mock_vacancies = [
            MagicMock(id="vacancy-1", is_active=True),
            MagicMock(id="vacancy-2", is_active=True),
        ]
        
        with patch.object(service.candidate_service, 'get_candidate', AsyncMock(return_value=mock_candidate)), \
             patch.object(service.vacancy_service, 'get_active_vacancies', AsyncMock(return_value=mock_vacancies)), \
             patch.object(service, 'calculate_match', AsyncMock(side_effect=[
                 MagicMock(id="scoring-1"),
                 Exception("Ошибка расчёта"),
             ])):
            
            result = await service.batch_score_candidate(candidate_id)
            
            assert len(result) == 1
            assert result[0].id == "scoring-1"
            assert service.calculate_match.call_count == 2

    @pytest.mark.asyncio
    async def test_export_scores_to_csv_basic(self, service, mock_session, mock_scoring, mock_candidate, mock_vacancy):
        mock_scores = [mock_scoring]
        
        with patch.object(service.repository, 'get_all', AsyncMock(return_value=mock_scores)), \
             patch.object(service.candidate_service, 'get_candidate', AsyncMock(return_value=mock_candidate)), \
             patch.object(service.vacancy_service, 'get_vacancy', AsyncMock(return_value=mock_vacancy)):
            
            csv_output = await service.export_scores_to_csv()
            
            assert isinstance(csv_output, str)
            assert "scoring_id" in csv_output
            assert "candidate_id" in csv_output
            assert "vacancy_id" in csv_output
            assert "match_score" in csv_output
            service.repository.get_all.assert_called_once_with(limit=10000)

    @pytest.mark.asyncio
    async def test_export_scores_to_csv_with_filters(self, service, mock_session, mock_scoring):
        mock_scores = [mock_scoring]
        
        with patch.object(service.repository, 'get_all', AsyncMock(return_value=mock_scores)), \
             patch.object(service.candidate_service, 'get_candidate', AsyncMock(return_value=MagicMock())), \
             patch.object(service.vacancy_service, 'get_vacancy', AsyncMock(return_value=MagicMock())):
            
            csv_output = await service.export_scores_to_csv(
                candidate_id="candidate-123",
                vacancy_id="vacancy-456",
                min_score=70.0,
                limit=500
            )
            
            assert isinstance(csv_output, str)
            service.repository.get_all.assert_called_once_with(
                limit=500,
                candidate_id="candidate-123",
                vacancy_id="vacancy-456"
            )

    def test_get_recommendation_static_method(self):
        assert ScoringService.get_recommendation(85.0) == "hire"
        assert ScoringService.get_recommendation(100.0) == "hire"
        assert ScoringService.get_recommendation(80.0) == "hire"
        
        assert ScoringService.get_recommendation(79.9) == "consider"
        assert ScoringService.get_recommendation(50.0) == "consider"
        assert ScoringService.get_recommendation(65.0) == "consider"
        
        assert ScoringService.get_recommendation(49.9) == "reject"
        assert ScoringService.get_recommendation(30.0) == "reject"
        assert ScoringService.get_recommendation(0.0) == "reject"