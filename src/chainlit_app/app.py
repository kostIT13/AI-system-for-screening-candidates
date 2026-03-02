import chainlit as cl
import logging
import re
from datetime import datetime
from typing import Optional
from src.core.database import create_async_session  
from src.services.candidates.candidate_service import CandidateService
from src.services.vacancies.vacancies_service import VacancyService
from src.services.scoring.scoring_service import ScoringService
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


@cl.on_chat_start
async def start():
    try:
        db: AsyncSession = await create_async_session()
        
        candidate_service = CandidateService(db)
        vacancy_service = VacancyService(db)
        scoring_service = ScoringService(db)
        
        cl.user_session.set("db", db)
        cl.user_session.set("candidate_service", candidate_service)
        cl.user_session.set("vacancy_service", vacancy_service)
        cl.user_session.set("scoring_service", scoring_service)
        cl.user_session.set("initialized", True)
        
        logger.info("Chainlit services initialized")
        
        await cl.Message(
            content="""
# 👋 AI Screening System

Я помогу тебе с подбором кандидатов.

**Что я умею:**
- 🔍 **Найти кандидатов** — *"найди Python разработчиков"*
- 💼 **Найти вакансии** — *"покажи активные вакансии"*
- 🎯 **Оценить кандидата** — *"оцени кандидата <ID>"*
- 📊 **Статистика** — *"покажи статистику"*

Напиши, что нужно сделать!
            """
        ).send()
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        await cl.Message(
            content=f"Ошибка инициализации: {str(e)}\n\nПроверь логи."
        ).send()


@cl.on_message
async def main(message: cl.Message):
    if not cl.user_session.get("initialized"):
        await cl.Message(content="Сервисы не инициализированы. Перезапусти чат.").send()
        return
    
    candidate_service = cl.user_session.get("candidate_service")
    vacancy_service = cl.user_session.get("vacancy_service")
    scoring_service = cl.user_session.get("scoring_service")
    
    if not all([candidate_service, vacancy_service, scoring_service]):
        await cl.Message(content="Один из сервисов не загружен. Перезапусти чат.").send()
        return
    
    query = message.content.lower()
    
    if any(word in query for word in ["найди", "покажи", "искать"]) and \
       any(word in query for word in ["кандидат", "разработчик", "специалист"]):
        await search_candidates(query, candidate_service)
    
    elif any(word in query for word in ["ваканс", "должн", "позиц"]):
        await search_vacancies(query, vacancy_service)
    
    elif any(word in query for word in ["оцени", "скрин", "матч"]):
        await scoring(query, candidate_service, vacancy_service, scoring_service)
    
    elif any(word in query for word in ["статист", "сколько"]):
        await show_stats(candidate_service, vacancy_service)
    
    else:
        await cl.Message(
            content="""
**Примеры команд:**
- `Найди Python разработчиков`
- `Покажи активные вакансии`
- `Оцени кандидата <ID>`
- `Покажи статистику`
            """
        ).send()


async def search_candidates(query: str, service):
    await cl.Message(content="🔍 Ищу кандидатов...").send()
    
    try:
        candidates = await service.get_candidates(limit=10)
        
        if not candidates:
            await cl.Message(content="Кандидаты не найдены").send()
            return
        
        msg = f"**Найдено: {len(candidates)}**\n\n"
        for i, c in enumerate(candidates[:5], 1):
            skills = ", ".join(c.key_skills[:3]) if c.key_skills else "Нет навыков"
            msg += f"**{i}. {c.title}**\n"
            msg += f"{c.location} | {c.salary_min or '?'}-{c.salary_max or '?'} ₽\n"
            msg += f"{skills}\n"
            msg += f"`{c.id}`\n\n"
        
        await cl.Message(content=msg).send()
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        await cl.Message(content=f"Ошибка: {str(e)}").send()


async def search_vacancies(query: str, service):
    await cl.Message(content="Ищу вакансии...").send()
    
    try:
        vacancies = await service.get_vacancies(limit=10, status='active')
        
        if not vacancies:
            await cl.Message(content="Вакансии не найдены").send()
            return
        
        msg = f"**Найдено: {len(vacancies)}**\n\n"
        for i, v in enumerate(vacancies[:5], 1):
            skills = ", ".join(v.key_skills[:3]) if v.key_skills else "Нет навыков"
            msg += f"**{i}. {v.title}** \n"
            msg += f"{v.location} | {v.salary_min or '?'}-{v.salary_max or '?'} ₽\n"
            msg += f"{skills}\n"
            msg += f"`{v.id}`\n\n"
        
        await cl.Message(content=msg).send()
        
    except Exception as e:
        logger.error(f"Vacancy search error: {e}")
        await cl.Message(content=f"Ошибка: {str(e)}").send()


async def scoring(query: str, candidate_service, vacancy_service, scoring_service):
    await cl.Message(content="Запускаю скоринг...").send()
    
    try:
        uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
        match = re.search(uuid_pattern, query)
        
        if not match:
            await cl.Message(
                content="**Укажи ID кандидата**\n\nПример: `оцени кандидата 8f58cde9-5825-4d10-9931-90eb56b5729e`"
            ).send()
            return
        
        candidate_id = match.group(0)
        candidate = await candidate_service.get_candidate(candidate_id)
        
        if not candidate:
            await cl.Message(content=f"Кандидат не найден").send()
            return
        
        scores = await scoring_service.get_best_matches_for_candidate(candidate_id, limit=3)
        
        msg = f"**Результаты для:**\n**{candidate.title}**\n\n"
        
        if scores:
            msg += "**Лучшие вакансии:**\n"
            for i, score in enumerate(scores, 1):
                vacancy = await vacancy_service.get_vacancy(score.vacancy_id)
                emoji = "🟢" if score.match_score >= 80 else "🟡" if score.match_score >= 50 else "🔴"
                vacancy_title = vacancy.title if vacancy else "Unknown"
                msg += f"{emoji} **{i}. {vacancy_title}** — {score.match_score:.1f}%\n"
        else:
            msg += "_Скоринг ещё не проводился_\n"
        
        await cl.Message(content=msg).send()
        
    except Exception as e:
        logger.error(f"Scoring error: {type(e).__name__}: {e}")
        await cl.Message(content=f"Ошибка: {str(e)}").send()


async def show_stats(candidate_service, vacancy_service):
    await cl.Message(content="Собираю статистику...").send()
    
    try:
        candidates = await candidate_service.get_candidates(limit=1000)
        vacancies = await vacancy_service.get_vacancies(limit=1000)
        
        categories = {}
        for c in candidates:
            categories[c.category] = categories.get(c.category, 0) + 1
        
        active = sum(1 for v in vacancies if getattr(v, 'status', 'active') == 'active')
        
        msg = "**Статистика**\n\n"
        msg += f"**Кандидаты:**\nВсего: {len(candidates)}\n"
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]:
            msg += f" {cat}: {count}\n"
        
        msg += f"\n**Вакансии:**\nВсего: {len(vacancies)}\nАктивные: {active}\nЗакрытые: {len(vacancies) - active}\n"
        
        await cl.Message(content=msg).send()
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        await cl.Message(content=f"Ошибка: {str(e)}").send()


@cl.on_chat_end
async def end():
    """При завершении чата — закрываем сессию"""
    db = cl.user_session.get("db")
    if db:
        try:
            await db.close()
            logger.info("Database session closed")
        except Exception as e:
            logger.error(f"Error closing DB: {e}")