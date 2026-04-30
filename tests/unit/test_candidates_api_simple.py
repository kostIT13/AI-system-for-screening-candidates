import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException, status
from src.api.candidates.endpoints import get_candidates, get_candidate, create_candidate, update_candidate, delete_candidate
from src.api.candidates.schemas import CandidateCreate, CandidateUpdate


class TestCandidatesAPISimple:
    
    @pytest_asyncio.fixture
    async def mock_service(self):
        return AsyncMock()
    
    @pytest.mark.asyncio
    async def test_get_candidates_success(self, mock_service):
        mock_candidates = [MagicMock(), MagicMock()]
        mock_service.get_candidates.return_value = mock_candidates
        
        result = await get_candidates(
            service=mock_service,
            skip=0,
            limit=10,
            category=None,
            location=None
        )
        
        mock_service.get_candidates.assert_called_once_with(skip=0, limit=10)
        assert result == mock_candidates
    
    @pytest.mark.asyncio
    async def test_get_candidate_success(self, mock_service):
        candidate_id = "test-id-123"
        mock_candidate = MagicMock()
        mock_service.get_candidate.return_value = mock_candidate
        
        result = await get_candidate(candidate_id, mock_service)
        
        mock_service.get_candidate.assert_called_once_with(candidate_id)
        assert result == mock_candidate
    
    @pytest.mark.asyncio
    async def test_get_candidate_not_found(self, mock_service):
        candidate_id = "non-existent-id"
        mock_service.get_candidate.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            await get_candidate(candidate_id, mock_service)
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "Candidate not found"
        mock_service.get_candidate.assert_called_once_with(candidate_id)
    
    @pytest.mark.asyncio
    async def test_create_candidate_success(self, mock_service):
        candidate_create_data = CandidateCreate(
            category="backend",
            title="Python Developer",
            exp_years=3,
            key_skills=["Python", "Django"],
            location="Москва",
            salary_min=150000,
            salary_max=250000,
            employment="full_time",
            remote="true",
            summary="Опытный разработчик"
        )
        
        mock_created_candidate = MagicMock()
        mock_service.create_candidate.return_value = mock_created_candidate
        
        result = await create_candidate(candidate_create_data, mock_service)
        
        mock_service.create_candidate.assert_called_once_with(
            candidate_create_data.model_dump()
        )
        assert result == mock_created_candidate
    
    @pytest.mark.asyncio
    async def test_update_candidate_success(self, mock_service):
        candidate_id = "test-id-123"
        candidate_update_data = CandidateUpdate(
            title="Senior Python Developer",
            exp_years=5,
            salary_min=200000
        )
        
        mock_updated_candidate = MagicMock()
        mock_service.update_candidate.return_value = mock_updated_candidate
        
        result = await update_candidate(candidate_id, candidate_update_data, mock_service)
        
        mock_service.update_candidate.assert_called_once_with(
            candidate_id,
            candidate_update_data.model_dump(exclude_unset=True)
        )
        assert result == mock_updated_candidate
    
    @pytest.mark.asyncio
    async def test_delete_candidate_success(self, mock_service):
        candidate_id = "test-id-123"
        mock_service.delete_candidate.return_value = True
        
        result = await delete_candidate(candidate_id, mock_service)
        
        mock_service.delete_candidate.assert_called_once_with(candidate_id)
        assert result is None
    
    def test_candidate_create_schema_validation(self):
        valid_data = {
            "category": "backend",
            "title": "Python Developer",
            "exp_years": 3,
            "key_skills": ["Python", "Django"],
            "location": "Москва",
            "salary_min": 150000,
            "salary_max": 250000,
            "employment": "full_time",
            "remote": "true",
            "summary": "Опытный разработчик"
        }
        
        candidate = CandidateCreate(**valid_data)
        assert candidate.category == "backend"
        assert candidate.title == "Python Developer"
        assert candidate.exp_years == 3
        assert candidate.key_skills == ["Python", "Django"]
        assert candidate.location == "Москва"
        assert candidate.salary_min == 150000
        assert candidate.salary_max == 250000
        assert candidate.employment == "full_time"
        assert candidate.remote == "true"
        assert candidate.summary == "Опытный разработчик"