import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.candidates.candidate_service import CandidateService
from src.models.candidates import Candidates


class TestCandidateService:
    
    @pytest_asyncio.fixture
    async def mock_session(self):
        return AsyncMock(spec=AsyncSession)
    
    @pytest_asyncio.fixture
    def service(self, mock_session):
        return CandidateService(mock_session)
    
    @pytest.mark.asyncio
    async def test_get_candidates_without_filters(self, service, mock_session):
        mock_candidates = [MagicMock(spec=Candidates), MagicMock(spec=Candidates)]
        
        with patch.object(service.repository, 'get_all', AsyncMock(return_value=mock_candidates)):
            result = await service.get_candidates()
            
            service.repository.get_all.assert_called_once_with()
            assert result == mock_candidates
    
    @pytest.mark.asyncio
    async def test_get_candidates_with_filters(self, service, mock_session):
        mock_candidate = MagicMock(spec=Candidates)
        
        with patch.object(service.repository, 'get_all', AsyncMock(return_value=[mock_candidate])):
            result = await service.get_candidates(category="backend", exp_years=3)
            
            service.repository.get_all.assert_called_once_with(category="backend", exp_years=3)
            assert result == [mock_candidate]
    
    @pytest.mark.asyncio
    async def test_get_candidate_found(self, service, mock_session):
        candidate_id = "test-id-123"
        mock_candidate = MagicMock(spec=Candidates)
        
        with patch.object(service.repository, 'get_by_id', AsyncMock(return_value=mock_candidate)):
            result = await service.get_candidate(candidate_id)
            
            service.repository.get_by_id.assert_called_once_with(candidate_id)
            assert result == mock_candidate
    
    @pytest.mark.asyncio
    async def test_get_candidate_not_found(self, service, mock_session):
        candidate_id = "non-existent-id"
        
        with patch.object(service.repository, 'get_by_id', AsyncMock(return_value=None)):
            result = await service.get_candidate(candidate_id)
            
            service.repository.get_by_id.assert_called_once_with(candidate_id)
            assert result is None
    
    @pytest.mark.asyncio
    async def test_create_candidate_success(self, service, mock_session):
        candidate_data = {
            "category": "backend",
            "title": "Python Developer",
            "exp_years": 3,
            "key_skills": ["Python", "Django", "PostgreSQL"],
            "location": "Москва",
            "salary_min": 150000,
            "salary_max": 250000,
            "employment": "full_time",
            "remote": True,
            "summary": "Опытный Python разработчик с 3 годами опыта"
        }
        
        mock_created_candidate = MagicMock(spec=Candidates)
        
        with patch.object(service.repository, 'create', AsyncMock(return_value=mock_created_candidate)):
            result = await service.create_candidate(candidate_data)
            
            service.repository.create.assert_called_once()
            call_arg = service.repository.create.call_args[0][0]
            assert isinstance(call_arg, Candidates)
            assert call_arg.category == "backend"
            assert call_arg.title == "Python Developer"
            assert call_arg.exp_years == 3
            assert call_arg.key_skills == ["Python", "Django", "PostgreSQL"]
            assert call_arg.location == "Москва"
            assert call_arg.salary_min == 150000
            assert call_arg.salary_max == 250000
            assert call_arg.employment == "full_time"
            assert call_arg.remote is True
            assert call_arg.summary == "Опытный Python разработчик с 3 годами опыта"
            assert result == mock_created_candidate
    
    @pytest.mark.asyncio
    async def test_create_candidate_with_defaults(self, service, mock_session):
        candidate_data = {
            "category": "frontend",
            "exp_years": 2
        }
        
        mock_created_candidate = MagicMock(spec=Candidates)
        
        with patch.object(service.repository, 'create', AsyncMock(return_value=mock_created_candidate)):
            result = await service.create_candidate(candidate_data)
            
            service.repository.create.assert_called_once()
            call_arg = service.repository.create.call_args[0][0]
            assert isinstance(call_arg, Candidates)
            assert call_arg.title == "frontend"  
            assert call_arg.location == "Not specified"
            assert call_arg.summary is None
            assert result == mock_created_candidate
    
    @pytest.mark.asyncio
    async def test_create_candidate_with_long_summary(self, service, mock_session):
        long_summary = "A" * 600 
        candidate_data = {
            "category": "backend",
            "summary": long_summary
        }
        
        mock_created_candidate = MagicMock(spec=Candidates)
        
        with patch.object(service.repository, 'create', AsyncMock(return_value=mock_created_candidate)):
            result = await service.create_candidate(candidate_data)
            
            service.repository.create.assert_called_once()
            call_arg = service.repository.create.call_args[0][0]
            assert isinstance(call_arg, Candidates)
            assert len(call_arg.summary) == 500
            assert call_arg.summary == "A" * 500
            assert result == mock_created_candidate
    
    @pytest.mark.asyncio
    async def test_update_candidate_success(self, service, mock_session):
        candidate_id = "test-id-123"
        update_data = {"title": "Senior Developer", "exp_years": 5}
        
        mock_updated_candidate = MagicMock(spec=Candidates)
        
        with patch.object(service.repository, 'update', AsyncMock(return_value=mock_updated_candidate)):
            result = await service.update_candidate(candidate_id, update_data)
            
            service.repository.update.assert_called_once_with(candidate_id, update_data)
            assert result == mock_updated_candidate
    
    @pytest.mark.asyncio
    async def test_update_candidate_not_found(self, service, mock_session):
        candidate_id = "non-existent-id"
        update_data = {"title": "Senior Developer"}
        
        with patch.object(service.repository, 'update', AsyncMock(return_value=None)):
            result = await service.update_candidate(candidate_id, update_data)
            
            service.repository.update.assert_called_once_with(candidate_id, update_data)
            assert result is None
    
    @pytest.mark.asyncio
    async def test_delete_candidate_success(self, service, mock_session):
        candidate_id = "test-id-123"
        
        with patch.object(service.repository, 'delete', AsyncMock(return_value=True)):
            result = await service.delete_candidate(candidate_id)
            
            service.repository.delete.assert_called_once_with(candidate_id)
            assert result is True
    
    @pytest.mark.asyncio
    async def test_delete_candidate_not_found(self, service, mock_session):
        candidate_id = "non-existent-id"
        
        with patch.object(service.repository, 'delete', AsyncMock(return_value=False)):
            result = await service.delete_candidate(candidate_id)
            
            service.repository.delete.assert_called_once_with(candidate_id)
            assert result is False
    
    @pytest.mark.asyncio
    async def test_get_candidates_by_skill(self, service, mock_session):
        skill = "Python"
        mock_candidates = [MagicMock(spec=Candidates), MagicMock(spec=Candidates)]
        
        with patch.object(service.repository, 'get_all', AsyncMock(return_value=mock_candidates)):
            result = await service.get_candidates_by_skill(skill)
            
            service.repository.get_all.assert_called_once_with(key_skills=skill)
            assert result == mock_candidates
    
    @pytest.mark.asyncio
    async def test_get_candidates_by_category(self, service, mock_session):
        category = "backend"
        mock_candidates = [MagicMock(spec=Candidates), MagicMock(spec=Candidates)]
        
        with patch.object(service.repository, 'get_all', AsyncMock(return_value=mock_candidates)):
            result = await service.get_candidates_by_category(category)
            
            service.repository.get_all.assert_called_once_with(category=category)
            assert result == mock_candidates
    
    @pytest.mark.asyncio
    async def test_candidate_id_is_uuid(self, service, mock_session):
        candidate_data = {"category": "backend"}
        
        mock_created_candidate = MagicMock(spec=Candidates)
        
        with patch.object(service.repository, 'create', AsyncMock(return_value=mock_created_candidate)):
            await service.create_candidate(candidate_data)
            
            call_arg = service.repository.create.call_args[0][0]
            try:
                uuid.UUID(call_arg.id, version=4)
                is_valid_uuid = True
            except ValueError:
                is_valid_uuid = False
            
            assert is_valid_uuid, f"ID '{call_arg.id}' не является валидным UUID"