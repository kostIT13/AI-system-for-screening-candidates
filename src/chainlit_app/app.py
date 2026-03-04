import chainlit as cl
import uuid
import logging
import csv
import io
from typing import List, Dict, Optional

from src.chainlit_app.api_client import APIClient
from src.services.vacancies.parser import parse_vacancies_csv
from src.services.candidates.parser import parse_candidates_csv

logger = logging.getLogger(__name__)


@cl.on_chat_start
async def start():
    try:
        api_client = APIClient()
        cl.user_session.set("api_client", api_client)
        cl.user_session.set("step", 1)
        logger.info("API client initialized")
    except Exception as e:
        await cl.Message(content=f"Ошибка инициализации: {e}").send()
        return
    
    await show_welcome()


async def show_welcome():
    
    welcome_msg = """
# AI Screening System

Добро пожаловать в систему интеллектуального подбора персонала!

## Что я умею:
| Функция | Описание |
|---------|----------|
| **Анализ резюме** | Парсинг CSV с навыками, опытом, зарплатными ожиданиями |
| **Сравнение с вакансией** | Оценка соответствия кандидата требованиям |
| **AI-скоринг** | Расчёт match_score с помощью LLM (Ollama/Groq) |
| **Детальный разбор** | Анализ по навыкам, опыту, зарплате, локации |

## Как использовать:
1. **Загрузите резюме кандидата** (CSV с колонками: `Category,Title,Exp_Years,...`)
2. **Загрузите вакансию** (CSV) **или** введите описание текстом
3. **Нажмите «Рассчитать»** — получите оценку соответствия

## Формат CSV для кандидата:
```csv
Category,Title,Exp_Years,Key_Skills,Location,Salary_Min,Salary_Max,Employment,Remote,Summary
Python-разработчик,Backend Developer,3-5,"Python, Django, PostgreSQL",Москва,100000,180000,Полная,Нет,"Опыт разработки API"
"""

    start_action = cl.Action(name="start_upload", label="▶Начать загрузку", payload={})
    await cl.Message(content=welcome_msg, actions=[start_action]).send()

@cl.action_callback("start_upload")
async def on_start_upload(action: cl.Action):
    await show_step_1()


async def show_step_1():
    files = await cl.AskFileMessage(
        content="**Шаг 1/3:** Загрузите резюме кандидата (CSV)\n\nКолонки: `Category,Title,Exp_Years,Key_Skills,Location,Salary_Min,Salary_Max,Employment,Remote,Summary`",
        accept={"text/csv": [".csv"]},
        max_files=1,
    ).send()
    
    if not files:
        await cl.Message(content="❌ Файл не загружен").send()
        return
    
    cl.user_session.set("candidate_file", files[0])
    cl.user_session.set("step", 2)
    
    await cl.Message(
        content="Кандидат загружен!\n\n**Шаг 2/3:** Как указать вакансию?",
        actions=[
            cl.Action(name="vacancy_csv", label="Загрузить CSV", payload={"source": "csv"}),
            cl.Action(name="vacancy_text", label="Ввести текстом", payload={"source": "text"}),
        ]
    ).send()

@cl.action_callback("vacancy_csv")
async def on_vacancy_csv(action: cl.Action):
    cl.user_session.set("vacancy_source", "csv")
    await show_step_2_csv()


@cl.action_callback("vacancy_text")
async def on_vacancy_text(action: cl.Action):
    cl.user_session.set("vacancy_source", "text")
    cl.user_session.set("step", 3)
    
    await cl.Message(
        content="**Введите описание вакансии:**\n\nПример: `Frontend Developer, React, Vue, Москва, 80000-150000 ₽`"
    ).send()


async def show_step_2_csv():
    files = await cl.AskFileMessage(
        content="**Загрузите вакансию (CSV)**\n\nКолонки: `Category,Title,Exp_Years_Min,Exp_Years_Max,Key_Skills,Location,Salary_Min,Salary_Max,Employment,Remote,Summary`",
        accept={"text/csv": [".csv"]},
        max_files=1,
    ).send()
    
    if not files:
        await cl.Message(content="Файл не загружен").send()
        return
    
    cl.user_session.set("vacancy_file", files[0])
    cl.user_session.set("step", 3)
    
    await cl.Message(
        content="Вакансия загружена!\n\n**Шаг 3/3:** Нажмите кнопку для расчёта:",
        actions=[cl.Action(name="calc", label="Рассчитать", payload={})]
    ).send()


@cl.set_chat_profiles
async def chat_profile():
    return [
        cl.ChatProfile(
            name="AI scoring CV",
            icon="https://ucarecdn.stepik.net/f621c671-b27b-48cf-8b95-8f6136963541/-/scale_crop/180x180/center/",
            markdown_description="Скоринг резуме кандидатов с помощью LLM",
        )
    ]


@cl.on_message
async def on_message(message: cl.Message):
    step = cl.user_session.get("step", 0)
    vacancy_source = cl.user_session.get("vacancy_source", "csv")
    
    if step == 3 and vacancy_source == "text":
        vacancy_text = message.content.strip()
        if len(vacancy_text) < 10:
            await cl.Message(content="Слишком коротко. Напишите полноценное описание.").send()
            return
        
        cl.user_session.set("vacancy_text", vacancy_text)
        cl.user_session.set("step", 4)
        
        await cl.Message(
            content=f"Вакансия: **{vacancy_text}**\n\nНажми кнопку:",
            actions=[cl.Action(name="calc", label="Рассчитать", payload={})]
        ).send()
        return
    
    if message.content.strip().lower() == "/start":
        cl.user_session.set("step", 1)
        await show_welcome()
        return
    
    await cl.Message(content="Используйте кнопки выше или напишите `/start` для начала.").send()


@cl.action_callback("calc")
async def on_calc(action: cl.Action):
    
    api_client: APIClient = cl.user_session.get("api_client")
    candidate_file = cl.user_session.get("candidate_file")
    vacancy_file = cl.user_session.get("vacancy_file")
    vacancy_text = cl.user_session.get("vacancy_text")
    vacancy_source = cl.user_session.get("vacancy_source", "text")
    
    if not all([api_client, candidate_file]):
        await cl.Message(content="Ошибка: кандидат не загружен").send()
        return
    
    await cl.Message(content="⏳ Обрабатываю данные...").send()
    
    try:
        
        candidate_content = await read_file_content(candidate_file)
        if not candidate_content:
            await cl.Message(content="Не удалось прочитать файл кандидата").send()
            return
        
        candidates_data = await parse_candidates_csv(candidate_content.encode('utf-8'))
        if not candidates_data:
            await cl.Message(content="Ошибка парсинга CSV кандидата").send()
            return
        
        candidate_data = candidates_data[0]
        candidate_data['id'] = f"temp_{uuid.uuid4()}"
        candidate = await api_client.create_candidate(candidate_data)
        candidate_id = candidate['id']
        
        await cl.Message(content=f"Кандидат: **{candidate.get('title')}**").send()
        
        vacancy_id = None
        
        if vacancy_source == "csv" and vacancy_file:
            vacancy_content = await read_file_content(vacancy_file)
            if not vacancy_content:
                await cl.Message(content="Не удалось прочитать файл вакансии").send()
                return
            
            vacancies_data = await parse_vacancies_csv(vacancy_content.encode('utf-8'))
            if not vacancies_data:
                await cl.Message(content="Ошибка парсинга CSV вакансии").send()
                return
            
            vacancy_data = vacancies_data[0]
            vacancy_data['id'] = f"temp_vac_{uuid.uuid4()}"
            vacancy_data['status'] = 'active'
            
            vacancy = await api_client.create_vacancy(vacancy_data)
            vacancy_id = vacancy['id']
            
            await cl.Message(content=f"Вакансия: **{vacancy.get('title')}**").send()
            
        else:
            vacancy_filters = parse_vacancy_text(vacancy_text)
            vacancies = await api_client.get_vacancies(
                category=vacancy_filters.get('category'),
                location=vacancy_filters.get('location'),
                status='active',
                limit=5
            )
            
            if not vacancies:
                vacancy_data = {
                    'id': f"temp_vac_{uuid.uuid4()}",
                    'category': vacancy_filters.get('category', 'Разработчик'),
                    'title': vacancy_text[:50],
                    'key_skills': vacancy_filters.get('skills', []),
                    'location': vacancy_filters.get('location', 'Не указана'),
                    'status': 'active'
                }
                vacancy = await api_client.create_vacancy(vacancy_data)
                vacancy_id = vacancy['id']
            else:
                vacancy = vacancies[0]
                vacancy_id = vacancy['id']
            
            await cl.Message(content=f"Вакансия: **{vacancy.get('title', vacancy_text[:30])}**").send()
        
        await cl.Message(content="Считаем соответствие...").send()
        
        score = await api_client.calculate_match(candidate_id, vacancy_id)
        
        await show_single_result(score, candidate, vacancy)
        
    except Exception as e:
        logger.error(f"Calculate error: {type(e).__name__}: {e}")
        await cl.Message(content=f"Ошибка: {type(e).__name__}: {str(e)[:200]}").send()


async def read_file_content(file) -> Optional[str]:
    content = None
    
    if hasattr(file, 'path') and file.path:
        with open(file.path, 'rb') as f:
            content = f.read()
    elif hasattr(file, 'content'):
        fc = file.content
        if isinstance(fc, dict):
            fc = fc.get('content', b'')
        if isinstance(fc, bytes):
            content = fc
        elif hasattr(fc, 'read'):
            content = fc.read()
    
    if isinstance(content, bytes):
        content = content.decode('utf-8')
    
    return content


def parse_vacancy_text(text: str) -> Dict:
    result = {'category': None, 'location': None, 'skills': []}
    text_lower = text.lower()
    
    locations = {'москва': 'Москва', 'спб': 'Санкт-Петербург', 'казань': 'Казань', 'регионы': 'Регионы'}
    for key, value in locations.items():
        if key in text_lower:
            result['location'] = value
            break
    
    known_skills = ['python', 'django', 'react', 'vue', 'angular', 'javascript', 'typescript', 'postgresql', 'docker']
    for skill in known_skills:
        if skill in text_lower:
            result['skills'].append(skill.capitalize())
    
    words = text.split(',')
    if words:
        result['category'] = words[0].strip()
    
    return result


async def show_single_result(score: Dict, candidate: Dict, vacancy: Dict):
    
    match_score = score.get('match_score', 0)
    confidence = score.get('confidence', 0)
    analysis = score.get('analysis', {})
    
    emoji = "🟢" if match_score >= 80 else "🟡" if match_score >= 50 else "🔴"
    rec = "Пригласить" if match_score >= 80 else "Рассмотреть" if match_score >= 50 else "Отклонить"
    
    msg = f"""
# Результат AI-скоринга

## Кандидат
**{candidate.get('title')}** ({candidate.get('category')})
📍 {candidate.get('location')} | 💰 {candidate.get('salary_min') or '?'}-{candidate.get('salary_max') or '?'} ₽

## 💼 Вакансия
**{vacancy.get('title')}** ({vacancy.get('category')})
📍 {vacancy.get('location')} | 💰 {vacancy.get('salary_min') or '?'}-{vacancy.get('salary_max') or '?'} ₽

---

## Оценка соответствия
{emoji} **Match Score: {match_score:.1f}%**
- Уверенность: {confidence:.0%}
- Рекомендация: **{rec}**

## Детали анализа
"""
    
    if analysis.get('skills_match'):
        msg += f"- 🛠 **Навыки:** {analysis['skills_match']}\n"
    if analysis.get('experience_match'):
        msg += f"- 📅 **Опыт:** {analysis['experience_match']}\n"
    if analysis.get('salary_match'):
        msg += f"- 💰 **Зарплата:** {analysis['salary_match']}\n"
    if analysis.get('location_match'):
        msg += f"- 📍 **Локация:** {analysis['location_match']}\n"
    
    if analysis.get('strengths'):
        msg += f"\n✅ **Сильные стороны:**\n"
        for s in analysis['strengths'][:3]:
            msg += f"  • {s}\n"
    
    if analysis.get('weaknesses'):
        msg += f"\n**Зоны роста:**\n"
        for w in analysis['weaknesses'][:3]:
            msg += f"  • {w}\n"
    
    await cl.Message(content=msg).send()


@cl.on_chat_end
async def end():
    api_client = cl.user_session.get("api_client")
    if api_client:
        await api_client.close()
        logger.info("API client closed")