import chainlit as cl
import csv
import io
import uuid
import logging
from typing import Optional, List, Dict

# Твои импорты
from src.core.database import create_async_session
from src.services.candidates.candidate_service import CandidateService
from src.services.vacancies.vacancies_service import VacancyService
from src.services.scoring.scoring_service import ScoringService
from src.services.candidates.parser import parse_candidates_csv
from src.models.candidates import Candidates
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# ============================================
# 🏁 Старт: Шаг 1 — Загрузка файла
# ============================================

@cl.on_chat_start
async def start():
    """Инициализация + Шаг 1"""
    
    try:
        # Инициализация БД и сервисов
        db: AsyncSession = await create_async_session()
        cl.user_session.set("db", db)
        cl.user_session.set("candidate_service", CandidateService(db))
        cl.user_session.set("vacancy_service", VacancyService(db))
        cl.user_session.set("scoring_service", ScoringService(db))
        cl.user_session.set("step", 1)
        
        logger.info("✅ Chainlit services initialized")
        
    except Exception as e:
        await cl.Message(content=f"❌ Ошибка инициализации: {e}").send()
        return
    
    # Шаг 1: Загрузка файла
    await show_step_1()


async def show_step_1():
    """Шаг 1: Загрузка резюме"""
    files = await cl.AskFileMessage(
        content="📄 **Шаг 1:** Загрузите резюме кандидата (CSV)\n\nОжидаемые колонки: `Category, Title, Exp_Years, Key_Skills, Location, Salary_Min, Salary_Max, Employment, Remote, Summary`",
        accept={"text/csv": [".csv"]},
        max_files=1,
    ).send()
    
    if not files:
        await cl.Message(content="❌ Файл не загружен").send()
        return
    
    cl.user_session.set("file", files[0])
    cl.user_session.set("step", 2)
    
    await cl.Message(
        content="✅ Файл загружен!\n\n📝 **Шаг 2:** Напишите описание вакансии текстовым сообщением\n\nПример: `Python Developer, 3-5 лет, Django, PostgreSQL, Москва, 100000-180000 ₽`"
    ).send()


# ============================================
# 💬 Обработка сообщений (Шаг 2)
# ============================================

@cl.on_message
async def on_message(message: cl.Message):
    """Обработка текстовых сообщений"""
    step = cl.user_session.get("step", 0)
    file = cl.user_session.get("file")
    
    # Шаг 2: Получаем вакансию
    if step == 2 and file:
        vacancy_text = message.content.strip()
        
        if len(vacancy_text) < 10:
            await cl.Message(
                content="❌ Слишком коротко.\n\nНапишите полноценное описание вакансии.\n\nПример: `Python Developer, 3-5 лет, Django, PostgreSQL, Москва`"
            ).send()
            return
        
        cl.user_session.set("vacancy_text", vacancy_text)
        cl.user_session.set("step", 3)
        
        # Показываем кнопку
        action = cl.Action(name="calc", label="🚀 Рассчитать соответствие", payload={})
        await cl.Message(
            content=f"✅ Вакансия принята: **{vacancy_text}**\n\nНажми кнопку для запуска AI-скоринга:",
            actions=[action]
        ).send()
    
    elif step == 3:
        await cl.Message(content="👆 Нажмите кнопку **🚀 Рассчитать соответствие**").send()
    
    elif step == 1:
        await cl.Message(content="👆 Загрузите файл выше").send()
    
    else:
        await cl.Message(content="👋 Напишите `/start` для начала").send()


# ============================================
# ⚡ Кнопка «Рассчитать» (Шаг 3)
# ============================================

@cl.action_callback("calc")
async def on_calc(action: cl.Action):
    """Реальный скоринг с БД и LLM"""
    
    file = cl.user_session.get("file")
    vacancy_text = cl.user_session.get("vacancy_text")
    candidate_service = cl.user_session.get("candidate_service")
    vacancy_service = cl.user_session.get("vacancy_service")
    scoring_service = cl.user_session.get("scoring_service")
    
    if not all([file, vacancy_text, candidate_service, vacancy_service, scoring_service]):
        await cl.Message(content="❌ Ошибка: данные не загружены").send()
        return
    
    await cl.Message(content="⏳ Обрабатываю данные и запускаю AI-скоринг...").send()
    
    try:
        # 1. Читаем файл
        content = None
        if hasattr(file, 'path') and file.path:
            with open(file.path, 'r', encoding='utf-8') as f:
                content = f.read()
        elif hasattr(file, 'content'):
            content = file.content
            if hasattr(content, 'read'):
                content = content.read()
            if isinstance(content, bytes):
                content = content.decode('utf-8')
        
        if not content:
            await cl.Message(content="❌ Не удалось прочитать файл").send()
            return
        
        # 2. Парсим резюме через твой парсер
        candidates_data = await parse_candidates_csv(content.encode('utf-8'))
        if not candidates_data:
            await cl.Message(content="❌ Ошибка парсинга CSV").send()
            return
        
        candidate_data = candidates_data[0]
        
        # 3. Создаём кандидата в БД
        temp_id = f"temp_{uuid.uuid4()}"
        candidate_data['id'] = temp_id
        candidate = await candidate_service.create_candidate(candidate_data)
        
        await cl.Message(content=f"✅ Кандидат создан: **{candidate.title}**").send()
        
        # 4. Ищем вакансии в БД (по категории или все активные)
        category = candidate_data.get('category', '')
        vacancies = await vacancy_service.get_vacancies(status='active', limit=10)
        
        if not vacancies:
            await cl.Message(content="😕 Вакансии не найдены в базе").send()
            return
        
        await cl.Message(content=f"🔍 Найдено {len(vacancies)} вакансий. Считаем скоринг...").send()
        
        # 5. Считаем скоринг для каждой вакансии (топ-5)
        results = []
        for i, vac in enumerate(vacancies[:5]):
            try:
                score = await scoring_service.calculate_match(candidate.id, vac.id)
                results.append({
                    "vacancy": vac,
                    "score": score.match_score,
                    "confidence": score.confidence,
                    "analysis": score.analysis or {}
                })
            except Exception as e:
                logger.warning(f"Scoring failed for vacancy {vac.id}: {e}")
                continue
        
        if not results:
            await cl.Message(content="❌ Не удалось рассчитать скоринг").send()
            return
        
        # 6. Сортируем и показываем
        results.sort(key=lambda x: x["score"], reverse=True)
        await show_results(results, candidate)
        
    except Exception as e:
        logger.error(f"❌ Calculate error: {type(e).__name__}: {e}")
        await cl.Message(content=f"❌ Ошибка: {type(e).__name__}: {str(e)[:200]}").send()


# ============================================
# 📊 Показ результатов
# ============================================

async def show_results(results: List[Dict], candidate):
    """Показывает результаты скоринга"""
    
    msg = f"📊 **Результаты AI-скоринга для:**\n"
    msg += f"**{candidate.title}** ({candidate.category})\n\n"
    msg += f"🏆 **Лучшее совпадение:** {results[0]['vacancy'].title} — **{results[0]['score']:.1f}%**\n\n"
    msg += "---\n\n"
    
    for i, item in enumerate(results, 1):
        vac = item["vacancy"]
        score = item["score"]
        analysis = item["analysis"]
        
        emoji = "🟢" if score >= 80 else "🟡" if score >= 50 else "🔴"
        rec = "Пригласить" if score >= 80 else "Рассмотреть" if score >= 50 else "Отклонить"
        
        msg += f"### {emoji} {i}. {vac.title}\n"
        msg += f"- **Match Score:** {score:.1f}%\n"
        msg += f"- **Локация:** {vac.location}\n"
        msg += f"- **Зарплата:** {vac.salary_min or '?'}-{vac.salary_max or '?'} ₽\n"
        msg += f"- **Рекомендация:** {rec}\n"
        
        # Детали из анализа
        if analysis.get('skills_match'):
            msg += f"- **Навыки:** {analysis['skills_match'][:100]}...\n"
        if analysis.get('experience_match'):
            msg += f"- **Опыт:** {analysis['experience_match'][:100]}...\n"
        
        msg += f"- **Уверенность:** {item['confidence']:.0%}\n\n"
    
    await cl.Message(content=msg).send()


# ============================================
# 🧹 Очистка
# ============================================

@cl.on_chat_end
async def end():
    db = cl.user_session.get("db")
    if db:
        try:
            await db.close()
            logger.info("✅ Database session closed")
        except Exception as e:
            logger.error(f"❌ Error closing DB: {e}")