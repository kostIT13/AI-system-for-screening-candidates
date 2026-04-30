import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.services.candidates.repository import SQLAlchemyCandidatesRepository
from src.models.candidates import Candidates


class TestSQLAlchemyCandidatesRepository:
    
    @pytest_asyncio.fixture
    async def mock_session(self):
        session = AsyncMock(spec=AsyncSession)
        session.execute = AsyncMock()
        session.add = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.delete = AsyncMock()
        return session
    
    @pytest_asyncio.fixture
    def repository(self, mock_session):
        return SQLAlchemyCandidatesRepository(mock_session)
    
    @pytest.mark.asyncio
    async def test_get_all_without_filters(self, repository, mock_session):
        mock_candidates = [MagicMock(spec=Candidates), MagicMock(spec=Candidates)]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_candidates
        mock_session.execute.return_value = mock_result
        
        result = await repository.get_all()
        
        mock_session.execute.assert_called_once()
        assert result == mock_candidates
    
    @pytest.mark.asyncio
    async def test_get_all_with_filters(self, repository, mock_session):
        mock_candidate = MagicMock(spec=Candidates)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_candidate]
        mock_session.execute.return_value = mock_result
        
        result = await repository.get_all(category="backend", exp_years=3)
        
        mock_session.execute.assert_called_once()
        assert result == [mock_candidate]
    
    @pytest.mark.asyncio
    async def test_get_by_id_found(self, repository, mock_session):
        candidate_id = "test-id-123"
        mock_candidate = MagicMock(spec=Candidates)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_candidate
        mock_session.execute.return_value = mock_result
        
        result = await repository.get_by_id(candidate_id)
        
        mock_session.execute.assert_called_once()
        assert result == mock_candidate
    
    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repository, mock_session):
        candidate_id = "non-existent-id"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        result = await repository.get_by_id(candidate_id)
        
        mock_session.execute.assert_called_once()
        assert result is None
    
    @pytest.mark.asyncio
    async def test_create_success(self, repository, mock_session):
        mock_candidate = MagicMock(spec=Candidates)
        
        result = await repository.create(mock_candidate)
        
        mock_session.add.assert_called_once_with(mock_candidate)
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(mock_candidate)
        assert result == mock_candidate
    
    @pytest.mark.asyncio
    async def test_update_success(self, repository, mock_session):
        candidate_id = "test-id-123"
        update_data = {"title": "Senior Developer", "exp_years": 5}
        
        mock_candidate = MagicMock(spec=Candidates)
        mock_candidate.id = candidate_id
        mock_candidate.title = "Junior Developer"
        mock_candidate.exp_years = 2
        
        with patch.object(repository, 'get_by_id', AsyncMock(return_value=mock_candidate)):
            result = await repository.update(candidate_id, update_data)
            
            assert result == mock_candidate
            assert mock_candidate.title == "Senior Developer"
            assert mock_candidate.exp_years == 5
            mock_session.commit.assert_called_once()
            mock_session.refresh.assert_called_once_with(mock_candidate)
    
    @pytest.mark.asyncio
    async def test_update_not_found(self, repository, mock_session):
        candidate_id = "non-existent-id"
        update_data = {"title": "Senior Developer"}
        
        with patch.object(repository, 'get_by_id', AsyncMock(return_value=None)):
            result = await repository.update(candidate_id, update_data)
            
            assert result is None
            mock_session.commit.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_delete_success(self, repository, mock_session):
        candidate_id = "test-id-123"
        mock_candidate = MagicMock(spec=Candidates)
        
        with patch.object(repository, 'get_by_id', AsyncMock(return_value=mock_candidate)):
            result = await repository.delete(candidate_id)
            
            assert result is True
            mock_session.delete.assert_called_once_with(mock_candidate)
            mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_not_found(self, repository, mock_session):
        candidate_id = "non-existent-id"
        
        with patch.object(repository, 'get_by_id', AsyncMock(return_value=None)):
            result = await repository.delete(candidate_id)
            
            assert result is False
            mock_session.delete.assert_not_called()
            mock_session.commit.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_all_with_invalid_filter(self, repository, mock_session):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result
        
        result = await repository.get_all(non_existent_field="value")
        
        mock_session.execute.assert_called_once()
        assert result == []