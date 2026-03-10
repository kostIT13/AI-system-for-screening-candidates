# 🤖 AI Candidate Screening System
Интеллектуальная система, предназначенная для автоматизации и улучшения процесса отбора кандидатов. Она использует большие языковые модели (LLM) для анализа резюме и сопоставления их с требованиями вакансий, предоставляя современный интерфейс на базе ИИ. Создан для учебных целей.

## 🚀 Обзор
Этот проект представляет собой полноценное решение для отбора кандидатов. Он позволяет управлять вакансиями и кандидатами, а также использует LLM (например, Llama 3.2 через Ollama) для оценки соответствия кандидатов конкретным должностям. Система включает чат-интерфейс для взаимодействия с ИИ и бэкенд API для управления данными.

## 🎯 О проекте
**AI Candidate Screening System** — интеллектуальная система для автоматизации первичного отбора кандидатов. Система использует большие языковые модели (LLM) для:
* 📄 Анализа резюме и извлечения ключевых навыков
* 🔍 Сопоставления кандидатов с требованиями вакансий
* 📊 Генерации структурированных оценок соответствия (0-100%)
* 💬 Интерактивного чата с ИИ для уточнения деталей отбора
* 🗃️ Управления базой кандидатов и вакансий

## ✨ Возможности
## 🤖 AI-скоринг кандидатов
# Пример результата оценки
```
{
  "overall_match": 85,           # Общая оценка соответствия
  "skills_match": 90,            # Технические навыки
  "experience_match": 78,        # Опыт работы
  "education_match": 88,         # Образование
  "confidence": 0.92,            # Уверенность модели
  "reasoning": "Кандидат имеет 5+ лет опыта в Python..."  # Обоснование
}
```
## 📋 Управление данными
* ✅ Создание и редактирование вакансий с требованиями
* ✅ Загрузка и парсинг резюме (PDF, DOCX, TXT)
* ✅ Фильтрация и поиск кандидатов по параметрам
* ✅ История скрининга с возможностью сравнения версий
  
## 💬 Чат-интерфейс (Chainlit)
* 🗨️ Диалог с ИИ для уточнения критериев отбора
* 🔎 Запросы типа "Покажи топ-5 кандидатов по навыку React"
* 📝 Генерация персонализированных вопросов для интервью

## 📈 Аналитика и метрики
* ⏱️ Time-to-Screen: среднее время обработки резюме
* 🎯 Accuracy: % совпадения решений ИИ и рекрутера
* ⚖️ Fairness: контроль предвзятости по демографическим признакам
* 📊 Визуализация воронки отбора

## 🛠 Технологический стек 
**Бэкенд и язык**
* Python 3.11+ — основной язык разработки
* FastAPI 0.109+ — асинхронный веб-фреймворк для API
* Pydantic 2.0+ — валидация данных и сериализация

**ИИ и обработка текста**
* Ollama — локальный запуск больших языковых моделей
* Llama 3.2:3b — основная модель для анализа и скоринга
* LangChain + langchain-community — оркестрация промптов и цепочек
* spaCy / nltk (опционально) — предобработка текста

**Фронтенд и интерфейс**
* Chainlit — интерактивный чат-интерфейс для работы с ИИ
* Swagger UI (встроен в FastAPI) — документация API

**База данных и хранение**
* PostgreSQL 15+ — реляционная база данных
* SQLAlchemy 2.0 — ORM для работы с БД
* Alembic — миграции схемы базы данных

**Инфраструктура и деплой**
* Docker + Docker Compose — контейнеризация и оркестрация
* uv — быстрый менеджер пакетов и виртуальных окружений

**Тестирование и качество кода**
* pytest — фреймворк для тестирования
* httpx — асинхронный клиент для тестов API
* factory-boy — фабрики тестовых данных
* pytest-cov — отчёт о покрытии кода
* ruff / mypy — линтинг и проверка типов

## 🏗️ Архитектура проекта
```
📦 AI-system-for-screening-candidates
├── 📁 src/
│   ├── 📁 api/                 # API endpoints (FastAPI routers)
│   │   ├── endpoints/
│   │   │   ├── candidates/
│   │   │   │   ├── endpoints.py
│   │   │   │   ├── dependencies.py
│   │   │   │   └── schemas.py
│   │   │   ├── vacancies/
│   │   │   │   │    ├── endpoint.py
│   │   │   │   │    ├── dependencies.py
│   │   │   │   │    └── schemas.py
│   │   │   └── scoring/
│   │   │   │   │    ├── endpoints.py
│   │   │   │   │    ├── dependencies.py
│   │   │   │   │    └── schemas.py 
│   ├── 📁 chainlit_app/
│   │   ├── app.py
│   │   └── api_client.py 
│   ├── 📁 core/                
│   │   ├── config.py           
│   │   ├── database.py
│   │   ├── logging_settings.py         
│   │   └── settings_llm.py      
│   ├── 📁 models/              
│   │   ├── candidate.py
│   │   ├── vacancy.py
│   │   └── scoring.py             
│   ├── 📁 services/            
│   │   ├── ai/
│   │   │   ├── prompts/
│   │   │   │   ├── function_for_prompts.py
│   │   │   │   └── prompt.py
│   │   │   ├── llm_client.py
│   │   │   └── scoring_engine.py
│   │   ├── candidates/
│   │   │   ├── base.py
│   │   │   ├── candidate_service.py
│   │   │   ├── parser.py
│   │   │   └── repository.py
│   │   ├── scoring/
│   │   │   ├── base.py
│   │   │   ├── scoring.py
│   │   │   └── repository.py
│   │   └── vacancies/
│   │   │   ├── base.py
│   │   │   ├── vacancy_service.py
│   │   │   ├── parser.py
│   │   │   └── repository.py                         
├── 📁 tests/                   # Тесты
│   ├── conftest.py          # Тестовые данные
│   ├── 📁 unit/                # Unit-тесты
│   └── 📁 integration/
└── main.py        
├── 📁 alembic/
├── 📄.env.test.example           
├── 📄 docker-compose.yml       
├── 📄 Dockerfile
├── 📄 requirements.txt
├── 📄 pytest.ini
├── 📄 alembic.ini
├── 📄 .dockerignore
├── 📄 .gitignore
├── 📄 uv.lock           
├── 📄 pyproject.toml           
├── 📄 .env.example             
└── 📄 README.md                
```

## 🚀 Быстрый старт
**Предварительные требования**
* Docker и Docker Compose 
* Ollama установлен локально (опционально, если не используете контейнер)
* Минимум 8 ГБ ОЗУ для запуска Llama 3.2:3b
## 1. Клонирование репозитория
```bash
12
git clone https://github.com/kostIT13/AI-system-for-screening-candidates.git
cd AI-system-for-screening-candidates
```
##2. Настройка окружения
```bash
# Скопируйте шаблон переменных
cp .env.example .env

# Отредактируйте .env при необходимости:
# POSTGRES_USER, POSTGRES_PASSWORD, OLLAMA_BASE_URL и т.д.
```
## 3. Запуск через Docker Compose
```bash
# Запуск всех сервисов (БД, бэкенд, Ollama)
docker compose up -d

# Проверка логов
docker compose logs -f api

# Загрузка модели Llama 3.2 (если не загружена)
docker compose exec ollama ollama pull llama3.2:3b
```
## 4. Инициализация базы данных
```bash
# Применение миграций
docker compose exec api alembic upgrade head

# (Опционально) Заполнение тестовыми данными
docker compose exec api python -m src.db.seed
```


