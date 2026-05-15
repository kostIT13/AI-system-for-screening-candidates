# src/streamlit_app/components/vacancy_input.py
import streamlit as st
import csv
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


def parse_vacancy_csv_row(text: str) -> Dict:
    """Парсинг одной строки CSV вакансии"""
    result = {
        'category': None, 'title': None, 'location': None, 'skills': [],
        'exp_years_min': None, 'exp_years_max': None,
        'salary_min': None, 'salary_max': None,
        'employment': None, 'remote': None, 'summary': None,
    }
    
    try:
        # Пробуем распарсить как CSV строку
        row = next(csv.reader([text]))
        if len(row) >= 10:
            result['category'] = row[0].strip() or None
            result['title'] = row[1].strip() or None
            
            # Парсинг опыта
            exp_raw = row[2].strip()
            if '-' in exp_raw:
                parts = exp_raw.split('-', 1)
                try:
                    result['exp_years_min'] = int(parts[0].strip())
                    result['exp_years_max'] = int(parts[1].strip()) if parts[1].strip() else None
                except ValueError:
                    pass
            elif exp_raw.isdigit():
                result['exp_years_min'] = result['exp_years_max'] = int(exp_raw)
            
            # Навыки
            skills_str = row[3].strip()
            if skills_str:
                result['skills'] = [s.strip() for s in skills_str.split(',') if s.strip()]
            
            # Остальные поля
            result['location'] = row[4].strip() or None
            try:
                result['salary_min'] = int(row[5].strip()) if row[5].strip() else None
                result['salary_max'] = int(row[6].strip()) if row[6].strip() else None
            except ValueError:
                pass
            
            result['employment'] = row[7].strip() or None
            result['remote'] = row[8].strip() or None
            result['summary'] = row[9].strip() or None
            
            return result
    except Exception as e:
        logger.warning(f"CSV parse error: {e}")
    
    # Fallback: простой парсинг по запятым
    parts = [p.strip() for p in text.split(',')]
    if len(parts) >= 2:
        result['category'] = parts[0]
        result['title'] = parts[1]
    result['summary'] = text[:500]
    
    return result


def vacancy_text_input():
    """Компонент ввода вакансии текстом"""
    st.markdown("### ✍️ Шаг 2б: Описание вакансии")
    
    vacancy_text = st.text_area(
        "Введите описание вакансии (или вставьте строку CSV):",
        value=st.session_state.get("vacancy_text", ""),
        height=150,
        placeholder="Пример: Фронтенд-разработчик,Frontend Developer,3-5,\"React, TypeScript\",Москва,90000,150000,Полная,Да,Разработка интерфейсов"
    )
    
    if vacancy_text and len(vacancy_text.strip()) >= 10:
        # Показываем превью распарсенных данных
        parsed = parse_vacancy_csv_row(vacancy_text.strip())
        
        with st.expander("🔍 Распознанные поля", expanded=True):
            st.json(parsed, expanded=False)
        
        if st.button("💾 Сохранить и продолжить", type="primary", width="stretch"):
            st.session_state.vacancy_text = vacancy_text.strip()
            st.session_state.parsed_vacancy = parsed
            st.session_state.vacancy_data = [parsed]
            st.session_state.step = 3
            st.rerun()
    elif vacancy_text:
        st.warning("⚠️ Описание слишком короткое (минимум 10 символов)")