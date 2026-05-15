# src/streamlit_app/app.py
import streamlit as st
import asyncio
import logging
import nest_asyncio
from typing import Optional, List, Dict, Any
import uuid
import csv
import io
import pandas as pd

from src.streamlit_app.api_client import APIClient
from src.services.vacancies.parser import parse_vacancies_csv
from src.services.candidates.parser import parse_candidates_csv

# 🔧 Применяем nest_asyncio для работы с asyncio в Streamlit
nest_asyncio.apply()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# =============================================================================
# 🎨 PAGE CONFIG
# =============================================================================
st.set_page_config(
    page_title="AI Screening System",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# 🧠 SESSION STATE INIT
# =============================================================================
def init_session_state():
    defaults = {
        "api_client": None,
        "step": 1,
        "scoring_mode": None,
        "vacancy_source": None,
        "candidate_file": None,
        "vacancy_file": None,
        "vacancy_text": None,
        "candidates_data": None,
        "vacancy_data": None,
        "parsed_vacancy": None,
        "results": None,
        "processing": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# =============================================================================
# 🔌 API CLIENT INIT
# =============================================================================
if st.session_state.api_client is None:
    try:
        st.session_state.api_client = APIClient()
        logger.info("✅ API client initialized")
    except Exception as e:
        st.error(f"❌ Ошибка подключения к API: {e}")
        st.stop()

# =============================================================================
# 🧩 ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =============================================================================

def parse_vacancy_text(text: str) -> Dict:
    """Парсинг текста вакансии"""
    result = {
        'category': None, 'title': None, 'location': None, 'skills': [],
        'exp_years_min': None, 'exp_years_max': None,
        'salary_min': None, 'salary_max': None,
        'employment': None, 'remote': None, 'summary': None,
    }
    text_lower = text.lower()

    # Попытка распарсить как CSV-строку
    try:
        row = next(csv.reader([text]))
        if len(row) >= 10:
            result['category'] = row[0].strip() or None
            result['title'] = row[1].strip() or None
            exp_raw = row[2].strip()
            if '-' in exp_raw:
                parts = exp_raw.split('-', 1)
                result['exp_years_min'] = int(parts[0].strip()) if parts[0].strip().isdigit() else None
                result['exp_years_max'] = int(parts[1].strip()) if parts[1].strip().isdigit() else None
            elif exp_raw.isdigit():
                result['exp_years_min'] = result['exp_years_max'] = int(exp_raw)
            result['skills'] = [s.strip() for s in row[3].split(',') if s.strip()]
            result['location'] = row[4].strip() or None
            result['salary_min'] = int(row[5].strip()) if row[5].strip().isdigit() else None
            result['salary_max'] = int(row[6].strip()) if row[6].strip().isdigit() else None
            result['employment'] = row[7].strip() or None
            result['remote'] = row[8].strip() or None
            result['summary'] = row[9].strip() or None
            return result
    except Exception:
        pass
    
    # Fallback: эвристики
    locations = {'москва': 'Москва', 'спб': 'Санкт-Петербург', 'казань': 'Казань', 'регионы': 'Регионы'}
    for key, value in locations.items():
        if key in text_lower:
            result['location'] = value
            break
    
    known_skills = ['python', 'django', 'react', 'vue', 'angular', 'javascript', 'typescript', 'postgresql', 'docker', 'fastapi']
    for skill in known_skills:
        if skill in text_lower:
            result['skills'].append(skill.capitalize())
    
    words = [w.strip() for w in text.split(',') if w.strip()]
    if words:
        result['category'] = words[0]
        result['title'] = words[0]
    
    result['summary'] = text[:500]
    return result


def render_sidebar():
    """Боковая панель"""
    with st.sidebar:
        st.image("https://ucarecdn.stepik.net/f621c671-b27b-48cf-8b95-8f6136963541/-/scale_crop/180x180/center/", width=100)
        st.title("🎯 AI Screening")
        
        st.markdown("### Режим работы")
        if st.session_state.step == 1:
            mode = st.radio(
                "Выберите режим:",
                ["👤 Один кандидат", "👥 Массовый скоринг"],
                key="mode_selector",
                index=0 if st.session_state.scoring_mode != "batch" else 1
            )
            if "👤" in mode:
                st.session_state.scoring_mode = "single"
            else:
                st.session_state.scoring_mode = "batch"
        
        st.markdown("---")
        
        if st.button("🔄 Начать заново", width="stretch"):
            for key in list(st.session_state.keys()):
                if key not in ["api_client"]:
                    del st.session_state[key]
            init_session_state()
            st.session_state.api_client = APIClient()
            st.rerun()
        
        st.markdown("---")
        st.markdown("### ℹ️ Справка")
        with st.expander("📋 Формат CSV кандидата", expanded=False):
            st.code("""Category,Title,Exp_Years,Key_Skills,Location,Salary_Min,Salary_Max,Employment,Remote,Summary
Python-разработчик,Backend Developer,3-5,"Python, Django",Москва,100000,180000,Полная,Нет,"Опыт разработки""", language="csv")
        with st.expander("📋 Формат CSV вакансии", expanded=False):
            st.code("""Category,Title,Exp_Years_Min,Exp_Years_Max,Key_Skills,Location,Salary_Min,Salary_Max,Employment,Remote,Summary
Python-разработчик,Backend Dev,2,5,"Python, FastAPI",Москва,120000,200000,Полная,Гибрид,"Разработка API""", language="csv")


def show_single_result(score: Dict, candidate: Dict, vacancy: Dict):
    """Отображение результата для одного кандидата"""
    match_score = score.get('match_score', 0)
    confidence = score.get('confidence', 0)
    analysis = score.get('analysis', {})
    
    if match_score >= 80:
        color, emoji, rec = "#22c55e", "🟢", "✅ Пригласить"
    elif match_score >= 50:
        color, emoji, rec = "#eab308", "🟡", "⚠️ Рассмотреть"
    else:
        color, emoji, rec = "#ef4444", "🔴", "❌ Отклонить"
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {color}22, transparent); 
                padding: 20px; border-radius: 12px; border-left: 4px solid {color}; margin: 20px 0;">
        <h2 style="margin: 0; color: {color}">{emoji} Match Score: {match_score:.1f}%</h2>
        <p style="margin: 5px 0;"><strong>Рекомендация:</strong> {rec}</p>
        <p style="margin: 5px 0; opacity: 0.8;">Уверенность модели: {confidence:.0%}</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 👤 Кандидат")
        st.markdown(f"**{candidate.get('title', 'N/A')}** ({candidate.get('category', 'N/A')})")
        st.markdown(f"📍 {candidate.get('location', '—')} | 💰 {candidate.get('salary_min', '?') or '?'}-{candidate.get('salary_max', '?') or '?'} ₽")
        if candidate.get('key_skills'):
            skills = candidate['key_skills'] if isinstance(candidate['key_skills'], list) else [candidate['key_skills']]
            st.markdown(f"🛠 **Навыки:** {', '.join(skills[:5])}")
    
    with col2:
        st.markdown("### 💼 Вакансия")
        st.markdown(f"**{vacancy.get('title', 'N/A')}** ({vacancy.get('category', 'N/A')})")
        st.markdown(f"📍 {vacancy.get('location', '—')} | 💰 {vacancy.get('salary_min', '?') or '?'}-{vacancy.get('salary_max', '?') or '?'} ₽")
        if vacancy.get('key_skills'):
            skills = vacancy['key_skills'] if isinstance(vacancy['key_skills'], list) else [vacancy['key_skills']]
            st.markdown(f"🛠 **Требования:** {', '.join(skills[:5])}")
    
    with st.expander("🔍 Детальный анализ", expanded=True):
        if analysis:
            for key, label in [('skills_match','🛠 Навыки'), ('experience_match','📅 Опыт'), ('salary_match','💰 Зарплата'), ('location_match','📍 Локация')]:
                if analysis.get(key):
                    st.markdown(f"- **{label}:** {analysis[key]}")
            if analysis.get('strengths'):
                st.markdown("#### ✅ Сильные стороны")
                for s in analysis['strengths'][:3]:
                    st.markdown(f"  • {s}")
            if analysis.get('weaknesses'):
                st.markdown("#### ⚠️ Зоны роста")
                for w in analysis['weaknesses'][:3]:
                    st.markdown(f"  • {w}")
        else:
            st.info("Детальный анализ недоступен")


def show_batch_results(results: List[Dict], vacancy: Dict):
    """Отображение результатов массового скоринга"""
    if not results:
        st.warning("Нет результатов для отображения")
        return
    
    results_sorted = sorted(results, key=lambda x: x["score"], reverse=True)
    best = results_sorted[0]
    avg_score = sum(r["score"] for r in results_sorted) / len(results_sorted)
    
    st.markdown(f"""
    ### 📊 Сводка по массовому скорингу
    - **Вакансия:** {vacancy.get('title', 'N/A')}
    - **Обработано кандидатов:** {len(results_sorted)}
    - **Лучший кандидат:** {best['candidate'].get('title', 'N/A')} ({best['score']:.1f}%)
    - **Средний score:** {avg_score:.1f}%
    """)
    
    df_data = []
    for i, item in enumerate(results_sorted, 1):
        cand = item["candidate"]
        score = item["score"]
        skills = cand.get('key_skills', [])
        skills_str = ", ".join((skills if isinstance(skills, list) else [skills])[:2]) if skills else "—"
        df_data.append({
            "№": i,
            "Кандидат": cand.get('title', 'N/A'),
            "Опыт": f"{cand.get('exp_years')} лет" if cand.get('exp_years') else "—",
            "Навыки": skills_str,
            "Match Score": score,
            "Рекомендация": "🟢 Пригласить" if score >= 80 else "🟡 Рассмотреть" if score >= 50 else "🔴 Отклонить",
        })
    
    df = pd.DataFrame(df_data)
    
    st.dataframe(
        df,
        width="stretch",
        hide_index=True,
        column_config={
            "Match Score": st.column_config.ProgressColumn("Match Score", format="%d%%", min_value=0, max_value=100),
        }
    )
    
    with st.expander("🔍 Детали по кандидату", expanded=False):
        selected = st.selectbox(
            "Выберите кандидата для детального просмотра:",
            options=[f"{r['candidate'].get('title')} ({r['score']:.1f}%)" for r in results_sorted],
            index=0
        )
        if selected:
            idx = [f"{r['candidate'].get('title')} ({r['score']:.1f}%)" for r in results_sorted].index(selected)
            item = results_sorted[idx]
            show_single_result(
                {"match_score": item["score"], "confidence": item.get("confidence", 0), "analysis": item.get("analysis", {})},
                item["candidate"],
                vacancy
            )
    
    csv_data = df.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        "📥 Скачать результаты (CSV)",
        data=csv_data,
        file_name=f"scoring_results_{vacancy.get('title', 'vacancy')}.csv",
        mime="text/csv",
        width="stretch"
    )

# =============================================================================
# 🧭 SIDEBAR
# =============================================================================
render_sidebar()

# =============================================================================
# 🎬 MAIN APP FLOW
# =============================================================================

# === ШАГ 1: Выбор режима и загрузка кандидата ===
if st.session_state.step == 1:
    st.title("🎯 AI Screening System")
    st.markdown("""
    ### Добро пожаловать в систему интеллектуального подбора персонала!
    
    | Функция | Описание |
    |---------|----------|
    | **Анализ резюме** | Парсинг CSV с навыками, опытом, зарплатными ожиданиями |
    | **Сравнение с вакансией** | Оценка соответствия кандидата требованиям |
    | **AI-скоринг** | Расчёт match_score с помощью LLM (Ollama/Groq) |
    | **Детальный разбор** | Анализ по навыкам, опыту, зарплате, локации |
    """)
    
    if st.session_state.scoring_mode is None:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("👤 Один кандидат (детально)", width="stretch", type="primary"):
                st.session_state.scoring_mode = "single"
                st.rerun()
        with col2:
            if st.button("👥 Массовый скоринг (CSV)", width="stretch"):
                st.session_state.scoring_mode = "batch"
                st.rerun()
    else:
        from src.streamlit_app.components.file_upload import upload_candidate_file
        upload_candidate_file()

# === ШАГ 2: Ввод вакансии ===
elif st.session_state.step == 2:
    st.title("📋 Укажите вакансию")
    
    # 🔧 Если источник не выбран, показываем radio
    if st.session_state.vacancy_source is None:
        source_options = ["📁 Из CSV", "✍️ Ввести текстом"]
        source = st.radio(
            "Источник данных вакансии:",
            options=source_options,
            index=0,
            horizontal=True,
            key="vacancy_source_radio"
        )
        if source and "CSV" in source:
            st.session_state.vacancy_source = "csv"
            st.rerun()
        elif source and "текстом" in source:
            st.session_state.vacancy_source = "text"
            st.rerun()
    else:
        # Показываем текущий выбор и кнопку смены
        st.info(f"📌 Текущий источник: **{st.session_state.vacancy_source.upper()}**")
        if st.button("🔄 Изменить источник", width="content"):
            st.session_state.vacancy_source = None
            st.rerun()
        st.markdown("---")
    
    # Отображение соответствующего компонента
    if st.session_state.vacancy_source == "csv":
        from src.streamlit_app.components.file_upload import upload_vacancy_file
        upload_vacancy_file()
    elif st.session_state.vacancy_source == "text":
        from src.streamlit_app.components.vacancy_input import vacancy_text_input
        vacancy_text_input()
    else:
        st.info("👈 Выберите источник данных вакансии выше")

# === ШАГ 3: Расчёт ===
# === ШАГ 3: Расчёт — с отладкой ===
elif st.session_state.step == 3:
    st.title("🚀 Готово к расчёту")
    
    # 🔍 ОТЛАДКА: показываем состояние
    with st.expander("🐛 Debug Info", expanded=False):
        st.write({
            "parsed_vacancy": st.session_state.parsed_vacancy,
            "vacancy_data_count": len(st.session_state.vacancy_data or []),
            "candidates_count": len(st.session_state.candidates_data or []),
        })
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 👤 Кандидат(ы)")
        if st.session_state.candidates_data:
            st.dataframe(pd.DataFrame(st.session_state.candidates_data[:3]), width="stretch")
        else:
            st.warning("⚠️ Кандидаты не загружены")
            
    with col2:
        st.markdown("### 💼 Вакансия")
        # ✅ Проверяем и parsed_vacancy, и vacancy_data
        vacancy_to_show = st.session_state.parsed_vacancy or (
            st.session_state.vacancy_data[0] if st.session_state.vacancy_data else None
        )
        
        if vacancy_to_show:
            st.success(f"✅ **{vacancy_to_show.get('title', 'N/A')}**")
            st.json(vacancy_to_show, expanded=False)
        else:
            st.error("❌ Вакансия не задана!")
            if st.button("🔄 Вернуться и загрузить вакансию", width="stretch"):
                st.session_state.step = 2
                st.session_state.vacancy_loaded = False
                st.rerun()
            st.stop()  # ✅ Останавливаем выполнение если нет вакансии
    
    if st.button("▶️ Рассчитать соответствие", type="primary", width="stretch", disabled=st.session_state.processing):
        st.session_state.processing = True
        st.rerun()
    
    if st.session_state.processing:
        with st.spinner("🔄 Обрабатываю..."):
            try:
                api = st.session_state.api_client
                loop = asyncio.get_event_loop()
                
                # 1. Кандидаты
                candidate_ids = []
                for cand_data in (st.session_state.candidates_data or [])[:20]:
                    cand_data = cand_data.copy()
                    cand_data['id'] = f"temp_{uuid.uuid4()}"
                    created = loop.run_until_complete(api.create_candidate(cand_data))
                    candidate_ids.append(created['id'])
                
                # 2. Вакансия — ✅ используем vacancy_to_show
                vacancy_to_show = st.session_state.parsed_vacancy or (
                    st.session_state.vacancy_data[0] if st.session_state.vacancy_data else {}
                )
                
                vac_data = {
                    'id': f"temp_vac_{uuid.uuid4()}",
                    'category': vacancy_to_show.get('category') or 'Разработчик',
                    'title': vacancy_to_show.get('title') or 'Вакансия',
                    'exp_years_min': vacancy_to_show.get('exp_years_min'),
                    'exp_years_max': vacancy_to_show.get('exp_years_max'),
                    'key_skills': vacancy_to_show.get('key_skills') or [],
                    'location': vacancy_to_show.get('location') or 'Не указана',
                    'salary_min': vacancy_to_show.get('salary_min'),
                    'salary_max': vacancy_to_show.get('salary_max'),
                    'employment': vacancy_to_show.get('employment'),
                    'remote': vacancy_to_show.get('remote'),
                    'summary': vacancy_to_show.get('summary') or '',
                    'status': 'active'
                }
                
                logger.info(f"📤 Sending to API: {vac_data}")
                
                created_vac = loop.run_until_complete(api.create_vacancy(vac_data))
                vacancy_id = created_vac['id']
                
                persisted = loop.run_until_complete(api.get_vacancy(vacancy_id))
                if not persisted:
                    raise ValueError("Vacancy not persisted")
                
                # 3. Скоринг
                results = []
                if st.session_state.scoring_mode == "batch":
                    progress = st.progress(0)
                    for idx, cid in enumerate(candidate_ids):
                        try:
                            score = loop.run_until_complete(api.calculate_match(cid, vacancy_id))
                            candidate = loop.run_until_complete(api.get_candidate(cid))
                            results.append({
                                "candidate": candidate,
                                "score": score.get('match_score', 0),
                                "confidence": score.get('confidence', 0),
                                "analysis": score.get('analysis', {})
                            })
                        except Exception as e:
                            logger.warning(f"Scoring failed for {cid}: {e}")
                            continue
                        progress.progress(min((idx + 1) / len(candidate_ids), 1.0))
                    progress.empty()
                else:
                    score = loop.run_until_complete(api.calculate_match(candidate_ids[0], vacancy_id))
                    candidate = loop.run_until_complete(api.get_candidate(candidate_ids[0]))
                    results = [{"candidate": candidate, "score": score.get('match_score', 0), 
                               "confidence": score.get('confidence', 0), "analysis": score.get('analysis', {})}]
                
                st.session_state.results = results
                st.session_state.vacancy_data = [persisted]
                st.session_state.step = 4
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Ошибка: {type(e).__name__}: {str(e)[:200]}")
                logger.error(f"Calculate error: {e}", exc_info=True)
                st.session_state.processing = False
                if st.button("🔄 Повторить", width="stretch"):
                    st.rerun()

# === ШАГ 4: Результаты ===
elif st.session_state.step == 4:
    st.title("📈 Результаты скоринга")
    
    if st.session_state.results and st.session_state.vacancy_data:
        vacancy = st.session_state.vacancy_data[0]
        
        if st.session_state.scoring_mode == "batch":
            show_batch_results(st.session_state.results, vacancy)
        else:
            item = st.session_state.results[0]
            show_single_result(
                {"match_score": item["score"], "confidence": item.get("confidence", 0), "analysis": item.get("analysis", {})},
                item["candidate"],
                vacancy
            )
        
        st.markdown("---")
        if st.button("🔄 Новый расчёт", width="stretch"):
            for key in list(st.session_state.keys()):
                if key not in ["api_client"]:
                    del st.session_state[key]
            init_session_state()
            st.session_state.api_client = APIClient()
            st.rerun()
    else:
        st.warning("Нет данных для отображения")
        if st.button("← Вернуться к расчёту"):
            st.session_state.step = 3
            st.rerun()

# =============================================================================
# 👣 FOOTER
# =============================================================================
st.markdown("---")
st.markdown("<div style='text-align: center; opacity: 0.6; font-size: 0.9em'>CorpKnow AI Screening • Powered by LLM</div>", unsafe_allow_html=True)