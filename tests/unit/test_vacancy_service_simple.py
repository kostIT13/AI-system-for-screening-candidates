import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.vacancies.vacancies_service import VacancyService
from src.models.vacancies import Vacancies


class TestVacancyServiceSimple:
    
    @pytest_asyncio.fixture
    async def mock_session(self):
        return AsyncMock(spec=AsyncSession)
    
    @pytest_asyncio.fixture
    def service(self, mock_session):
        return VacancyService(mock_session)
    
    @pytest.mark.asyncio
    async def test_get_vacancies_without_filters(self, service, mock_session):
        mock_vacancies = [MagicMock(spec=Vacancies), MagicMock(spec=Vacancies)]
        
        with patch.object(service.repository, 'get_all', AsyncMock(return_value=mock_vacancies)):
            result = await service.get_vacancies()
            
            service.repository.get_all.assert_called_once_with()
            assert result == mock_vacancies
    
    @pytest.mark.asyncio
    async def test_get_vacancy_found(self, service, mock_session):
        vacancy_id = "vacancy-id-123"
        mock_vacancy = MagicMock(spec=Vacancies)
        
        with patch.object(service.repository, 'get_by_id', AsyncMock(return_value=mock_vacancy)):
            result = await service.get_vacancy(vacancy_id)
            
            service.repository.get_by_id.assert_called_once_with(vacancy_id)
            assert result == mock_vacancy
    
    @pytest.mark.asyncio
    async def test_create_vacancy_success(self, service, mock_session):
        vacancy_data = {
            "category": "backend",
            "title": "Senior Python Developer",
            "exp_years_min": 3,
            "exp_years_max": 7,
            "key_skills": ["Python", "FastAPI", "PostgreSQL"],
            "location": "Москва",
            "salary_min": 200000,
            "salary_max": 350000,
            "employment": "full_time",
            "remote": "true",
            "summary": "Ищем опытного разработчика",
            "status": "active"
        }
        
        mock_created_vacancy = MagicMock(spec=Vacancies)
        
        with patch.object(service.repository, 'create', AsyncMock(return_value=mock_created_vacancy)):
            result = await service.create_vacancy(vacancy_data)
            
            service.repository.create.assert_called_once()
            call_arg = service.repository.create.call_args[0][0]
            assert isinstance(call_arg, Vacancies)
            assert call_arg.category == "backend"
            assert call_arg.title == "Senior Python Developer"
            assert call_arg.exp_years_min == 3
            assert call_arg.exp_years_max == 7
            assert call_arg.key_skills == ["Python", "FastAPI", "PostgreSQL"]
            assert call_arg.location == "Москва"
            assert call_arg.salary_min == 200000
            assert call_arg.salary_max == 350000
            assert call_arg.employment == "full_time"
            assert call_arg.remote == "true"
            assert call_arg.summary == "Ищем опытного разработчика"
            assert call_arg.status == "active"
            assert result == mock_created_vacancy
    
    @pytest.mark.asyncio
    async def test_update_vacancy_success(self, service, mock_session):
        vacancy_id = "vacancy-id-123"
        update_data = {"title": "Lead Developer", "salary_min": 250000}
        
        mock_updated_vacancy = MagicMock(spec=Vacancies)
        
        with patch.object(service.repository, 'update', AsyncMock(return_value=mock_updated_vacancy)):
            result = await service.update_vacancy(vacancy_id, update_data)
            
            service.repository.update.assert_called_once_with(vacancy_id, update_data)
            assert result == mock_updated_vacancy
    
    @pytest.mark.asyncio
    async def test_delete_vacancy_success(self, service, mock_session):
        vacancy_id = "vacancy-id-123"
        
        with patch.object(service.repository, 'delete', AsyncMock(return_value=True)):
            result = await service.delete_vacancy(vacancy_id)
            
            service.repository.delete.assert_called_once_with(vacancy_id)
            assert result is True
    
    @pytest.mark.asyncio
    async def test_get_active_vacancies(self, service, mock_session):
        mock_vacancies = [MagicMock(spec=Vacancies)]
        
        with patch.object(service.repository, 'get_all', AsyncMock(return_value=mock_vacancies)):
            result = await service.get_active_vacancies()
            
            service.repository.get_all.assert_called_once_with(status='active')
            assert result == mock_vacancies
    
    @pytest.mark.asyncio
    async def test_close_vacancy_success(self, service, mock_session):
        vacancy_id = "vacancy-id-123"
        mock_updated_vacancy = MagicMock(spec=Vacancies)
        
        with patch.object(service.repository, 'update', AsyncMock(return_value=mock_updated_vacancy)):
            result = await service.close_vacancy(vacancy_id)
            
            service.repository.update.assert_called_once_with(vacancy_id, {'status': 'closed'})
            assert result == mock_updated_vacancy
    
    @pytest.mark.asyncio
    async def test_vacancy_id_is_uuid(self, service, mock_session):
        vacancy_data = {"category": "backend"}
        
        mock_created_vacancy = MagicMock(spec=Vacancies)
        
        with patch.object(service.repository, 'create', AsyncMock(return_value=mock_created_vacancy)):
            await service.create_vacancy(vacancy_data)
            
            call_arg = service.repository.create.call_args[0][0]
            try:
                uuid.UUID(call_arg.id, version=4)
                is_valid_uuid = True
            except ValueError:
                is_valid_uuid = False
            
            assert is_valid_uuid, f"ID '{call_arg.id}' не является валидным UUID"