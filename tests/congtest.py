import pytest
import pytest_asyncio
import os
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from src.main import app
from src.core.database import Base, get_db
from src.services.candidates.repository import CandidatesRepository
from src.services.vacancies.repository import VacanciesRepository
from src.services.scoring.repository import ScoringRepository


TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Создаёт тестовый engine"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False, pool_pre_ping=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Создаёт изолированную сессию для каждого теста"""
    async_session = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()


@pytest.fixture(scope="function")
def override_get_db(test_session):
    """Override зависимости get_db для тестов"""
    async def _override():
        yield test_session
    
    app.dependency_overrides[get_db] = _override
    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def client(override_get_db) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP клиент для тестирования API"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


@pytest_asyncio.fixture(scope="function")
async def candidate_repo(test_session) -> CandidatesRepository:
    """Репозиторий кандидатов для тестов"""
    return CandidatesRepository(test_session)


@pytest_asyncio.fixture(scope="function")
async def vacancy_repo(test_session) -> VacanciesRepository:
    """Репозиторий вакансий для тестов"""
    return VacanciesRepository(test_session)


@pytest_asyncio.fixture(scope="function")
async def scoring_repo(test_session) -> ScoringRepository:
    """Репозиторий скоринга для тестов"""
    return ScoringRepository(test_session)



@pytest.fixture
def candidate_factory(faker):
    """Factory для создания тестовых кандидатов"""
    def _create(**overrides):
        data = {
            "id": faker.uuid4(),
            "category": faker.random_element(["Python-разработчик", "Фронтенд-разработчик"]),
            "title": faker.job(),
            "exp_years": faker.random_int(1, 10),
            "key_skills": faker.words(nb=5),
            "location": faker.city(),
            "salary_min": faker.random_int(50000, 100000),
            "salary_max": faker.random_int(100000, 250000),
            "employment": "Полная",
            "remote": faker.random_element(["Да", "Нет"]),
            "summary": faker.sentence(),
        }
        data.update(overrides)
        return data
    return _create


@pytest.fixture
def vacancy_factory(faker):
    """Factory для создания тестовых вакансий"""
    def _create(**overrides):
        data = {
            "id": faker.uuid4(),
            "category": faker.random_element(["Python-разработчик", "Фронтенд-разработчик"]),
            "title": faker.job(),
            "exp_years_min": faker.random_int(1, 3),
            "exp_years_max": faker.random_int(3, 7),
            "key_skills": faker.words(nb=5),
            "location": faker.city(),
            "salary_min": faker.random_int(80000, 150000),
            "salary_max": faker.random_int(150000, 300000),
            "employment": "Полная",
            "remote": faker.random_element(["Да", "Нет"]),
            "summary": faker.sentence(),
            "status": "active",
        }
        data.update(overrides)
        return data
    return _create