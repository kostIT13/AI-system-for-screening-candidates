import chainlit as cl
import uuid
import logging
from typing import List, Dict

from src.chainlit_app.api_client import APIClient 

logger = logging.getLogger(__name__)


@cl.on_chat_start
async def start():
    """Инициализация API-клиента вместо сервисов"""
    
    try:
        # ✅ Создаём HTTP-клиент к API
        api_client = APIClient()
        cl.user_session.set("api_client", api_client)
        cl.user_session.set("step", 1)
        
        logger.info("✅ API client initialized")
        
    except Exception as e:
        await cl.Message(content=f"❌ Ошибка инициализации: {e}").send()
        return
    
    await show_step_1()


async def show_step_1():
    """Шаг 1: Загрузка CSV"""
    files = await cl.AskFileMessage(
        content="**Шаг 1:** Загрузите резюме кандидата (CSV)",
        accept={"text/csv": [".csv"]},
        max_files=1,
    ).send()
    
    if not files:
        await cl.Message(content="Файл не загружен").send()
        return
    
    cl.user_session.set("file", files[0])
    cl.user_session.set("step", 2)
    
    await cl.Message(
        content="✅ Файл загружен!\n\n**Шаг 2:** Напишите описание вакансии\n\nПример: `Python Developer, Django, Москва`"
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    """Обработка текстовых сообщений"""
    step = cl.user_session.get("step", 0)
    file = cl.user_session.get("file")
    
    if step == 2 and file:
        vacancy_text = message.content.strip()
        
        if len(vacancy_text) < 10:
            await cl.Message(content="Слишком коротко. Напишите полноценное описание.").send()
            return
        
        cl.user_session.set("vacancy_text", vacancy_text)
        cl.user_session.set("step", 3)
        
        action = cl.Action(name="calc", label="🚀 Рассчитать", payload={})
        await cl.Message(
            content=f"✅ Вакансия: **{vacancy_text}**\n\nНажми кнопку:",
            actions=[action]
        ).send()
    
    elif step == 3:
        await cl.Message(content="Нажми кнопку **Рассчитать**").send()
    
    else:
        await cl.Message(content="Напишите `/start` для начала").send()


@cl.action_callback("calc")
async def on_calc(action: cl.Action):
    
    api_client: APIClient = cl.user_session.get("api_client")
    file = cl.user_session.get("file")  # ← Это AskFileResponse
    vacancy_text = cl.user_session.get("vacancy_text")
    
    if not all([api_client, file, vacancy_text]):
        await cl.Message(content="❌ Ошибка: данные не загружены").send()
        return
    
    await cl.Message(content="⏳ Обрабатываю...").send()
    
    try:
        # ✅ 1. Правильное чтение файла в Chainlit 2.x
        content = None
        
        # Вариант A: Если есть path (файл на диске)
        if hasattr(file, 'path') and file.path:
            with open(file.path, 'rb') as f:
                content = f.read()
        
        # Вариант B: Если content есть (bytes или dict)
        elif hasattr(file, 'content'):
            file_content = file.content
            if isinstance(file_content, dict):
                # В новых версиях content может быть dict с 'content' ключом
                file_content = file_content.get('content', b'')
            if isinstance(file_content, bytes):
                content = file_content
            elif hasattr(file_content, 'read'):
                content = file_content.read()
        
        # Вариант C: Читаем через API клиента (если есть ID файла)
        if not content and hasattr(file, 'id'):
            # Chainlit хранит файлы во временном хранилище
            # Нужно читать напрямую из file.path
            logger.warning(f"File content not accessible, trying path: {getattr(file, 'path', None)}")
        
        if not content:
            await cl.Message(content="❌ Не удалось прочитать файл").send()
            return
        
        # ✅ 2. Конвертируем в строку если нужно
        if isinstance(content, bytes):
            content = content.decode('utf-8')
        
        # ✅ 3. Отправляем в API (который принимает bytes)
        upload_result = await api_client.upload_candidates_csv(
            file_content=content.encode('utf-8'),
            filename="candidate.csv"
        )
        
        # ... остальной код ...
        candidate_id = upload_result.get('candidate_ids', [None])[0]
        
        if not candidate_id:
            await cl.Message(content="❌ Ошибка загрузки кандидата").send()
            return
        
        # 3. Получаем данные кандидата
        candidate = await api_client.get_candidate(candidate_id)
        if not candidate:
            await cl.Message(content="❌ Кандидат не найден").send()
            return
        
        await cl.Message(content=f"👤 Кандидат: **{candidate['title']}**").send()
        
        # 4. Ищем вакансии через API (с фильтрацией по категории!)
        vacancies = await api_client.get_vacancies(
            category=candidate.get('category'),  # ✅ Фильтр по категории
            location=candidate.get('location'),   # ✅ Фильтр по локации
            status='active',
            limit=20
        )
        
        if not vacancies:
            await cl.Message(
                content=f"😕 Не найдено вакансий по критериям:\n"
                       f"- Категория: `{candidate.get('category')}`\n"
                       f"- Локация: `{candidate.get('location')}`"
            ).send()
            return
        
        # 5. Скоринг через API
        await cl.Message(content=f"⚡ Считаем скоринг для {len(vacancies)} вакансий...").send()
        
        results = []
        for vac in vacancies[:5]:
            try:
                score = await api_client.calculate_match(candidate_id, vac['id'])
                results.append({
                    "vacancy": vac,
                    "score": score['match_score'],
                    "confidence": score['confidence'],
                    "analysis": score.get('analysis', {})
                })
            except Exception as e:
                logger.warning(f"Scoring failed for {vac['id']}: {e}")
                continue
        
        if not results:
            await cl.Message(content="⚠️ Не удалось рассчитать скоринг").send()
            return
        
        results.sort(key=lambda x: x["score"], reverse=True)
        await show_results(results, candidate)
        
    except Exception as e:
        logger.error(f"❌ Calculate error: {type(e).__name__}: {e}")
        await cl.Message(content=f"❌ Ошибка: {str(e)[:200]}").send()


async def show_results(results: List[Dict], candidate: Dict):
    """Показ результатов"""
    msg = f"**📊 Результаты для:** {candidate['title']}\n\n"
    msg += f"**🏆 Лучшее:** {results[0]['vacancy']['title']} — {results[0]['score']:.1f}%\n\n---\n\n"
    
    for i, item in enumerate(results, 1):
        vac = item["vacancy"]
        score = item["score"]
        analysis = item["analysis"]
        
        emoji = "🟢" if score >= 80 else "🟡" if score >= 50 else "🔴"
        rec = "Пригласить" if score >= 80 else "Рассмотреть" if score >= 50 else "Отклонить"
        
        msg += f"{emoji} **{i}. {vac['title']}** — {score:.1f}%\n"
        msg += f"📍 {vac['location']} | 💰 {vac['salary_min'] or '?'}-{vac['salary_max'] or '?'} ₽\n"
        msg += f"🎯 Рекомендация: {rec}\n"
        
        if analysis.get('skills_match'):
            msg += f"🛠 {analysis['skills_match'][:80]}...\n"
        msg += "\n"
    
    await cl.Message(content=msg).send()


@cl.on_chat_end
async def end():
    """Закрытие HTTP-клиента"""
    api_client = cl.user_session.get("api_client")
    if api_client:
        await api_client.close()
        logger.info("✅ API client closed")