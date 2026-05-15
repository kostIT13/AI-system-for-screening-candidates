# src/streamlit_app/components/file_upload.py
import streamlit as st
import pandas as pd
import logging
from typing import Optional

from src.services.vacancies.parser import parse_vacancies_csv
from src.services.candidates.parser import parse_candidates_csv

logger = logging.getLogger(__name__)


def upload_candidate_file():
    """Загрузка кандидата"""
    st.markdown("### 📤 Шаг 1: Загрузка резюме")
    help_text = (
        "Загрузите CSV с несколькими кандидатами" 
        if st.session_state.get("scoring_mode") == "batch" 
        else "Загрузите CSV с данными одного кандидата"
    )
    
    uploaded_file = st.file_uploader(help_text, type=["csv"], key="candidate_uploader")
    
    if uploaded_file is not None:
        try:
            content_bytes = uploaded_file.getvalue()
            candidates_data = parse_candidates_csv(content_bytes)
            
            if candidates_data:
                st.session_state.candidates_data = candidates_data
                with st.expander("👀 Предпросмотр", expanded=False):
                    st.dataframe(pd.DataFrame(candidates_data[:5]), width="stretch")
                st.success(f"✅ Загружено {len(candidates_data)} записей")
                st.session_state.step = 2
                st.rerun()
            else:
                st.error("❌ Не удалось распарсить CSV")
        except Exception as e:
            st.error(f"❌ Ошибка: {type(e).__name__}: {e}")
            logger.error(f"Parse error: {e}", exc_info=True)


def upload_vacancy_file() -> Optional[bytes]:
    """Загрузка вакансии из CSV"""
    st.markdown("### 📤 Шаг 2: Загрузка вакансии (CSV)")
    
    is_disabled = (
        st.session_state.get("step") != 2 or 
        st.session_state.get("vacancy_source") != "csv"
    )
    
    uploaded_file = st.file_uploader(
        "Загрузите файл вакансии",
        type=["csv"],
        key="vacancy_uploader",
        disabled=is_disabled
    )
    
    if uploaded_file is not None and not st.session_state.get("vacancy_loaded"):
        try:
            content_bytes = uploaded_file.getvalue()
            vacancies_data = parse_vacancies_csv(content_bytes)
            
            if vacancies_data:
                vacancy = vacancies_data[0]
                
                # ✅ Сохраняем ВСЕ нужные ключи
                st.session_state.vacancy_data = vacancies_data
                st.session_state.parsed_vacancy = vacancy.copy()  # ✅ Копия!
                st.session_state.vacancy_loaded = True  # ✅ Флаг защиты от повторной загрузки
                
                # ✅ Отладка: показываем что загрузилось
                with st.expander("🔍 Загруженные данные", expanded=True):
                    st.write(f"**Категория:** `{vacancy.get('category')}`")
                    st.write(f"**Заголовок:** `{vacancy.get('title')}`")
                    st.write(f"**Навыки:** `{vacancy.get('key_skills')}`")
                    st.json(vacancy, expanded=False)
                
                st.success(f"✅ Вакансия загружена: **{vacancy.get('title')}**")
                st.session_state.step = 3
                st.rerun()
            else:
                st.error("❌ CSV пустой или неверный формат")
                
        except Exception as e:
            st.error(f"❌ Ошибка: {type(e).__name__}: {str(e)[:150]}")
            logger.error(f"Vacancy parse error: {e}", exc_info=True)
            # ✅ Кнопка сброса при ошибке
            if st.button("🔄 Сбросить и попробовать снова"):
                st.session_state.vacancy_file = None
                st.session_state.vacancy_loaded = False
                st.rerun()
    
    return uploaded_file