from typing import Optional, List, Dict


def format_skills(skills: Optional[List[str]]) -> str:
    if not skills:
        return "Не указаны"
    return ", ".join(skills)


def format_salary(min_val: Optional[int], max_val: Optional[int]) -> str:
    if min_val and max_val:
        return f"{min_val} - {max_val} руб."
    elif min_val:
        return f"от {min_val} руб."
    elif max_val:
        return f"до {max_val} руб."
    return "Не указана"


def format_experience(exp_years: Optional[int]) -> str:
    if exp_years is None:
        return "Не указан"
    return f"{exp_years} лет"


def format_experience_range(min_exp: Optional[int], max_exp: Optional[int]) -> str:
    if min_exp and max_exp:
        if min_exp == max_exp:
            return f"{min_exp} лет"
        return f"{min_exp}-{max_exp} лет"
    elif min_exp:
        return f"от {min_exp} лет"
    elif max_exp:
        return f"до {max_exp} лет"
    return "Не указан"


def create_matching_prompt(candidate: Dict, vacancy: Dict) -> str:
    return f"""
## ВАКАНСИЯ:
**Должность:** {vacancy.get('title', 'N/A')}
**Категория:** {vacancy.get('category', 'N/A')}
**Требуемый опыт:** {format_experience_range(vacancy.get('exp_years_min'), vacancy.get('exp_years_max'))}
**Ключевые навыки:** {format_skills(vacancy.get('key_skills'))}
**Локация:** {vacancy.get('location', 'N/A')}
**Зарплата:** {format_salary(vacancy.get('salary_min'), vacancy.get('salary_max'))}
**Тип занятости:** {vacancy.get('employment', 'N/A')}
**Удалённая работа:** {vacancy.get('remote', 'N/A')}
**Описание:** **Описание:** {(vacancy.get('summary') if isinstance(vacancy, dict) else getattr(vacancy, 'summary', None)) or 'N/A'[:300]}

## КАНДИДАТ:
**Текущая должность:** {candidate.get('title', 'N/A')}
**Категория:** {candidate.get('category', 'N/A')}
**Опыт работы:** {format_experience(candidate.get('exp_years'))}
**Навыки:** {format_skills(candidate.get('key_skills'))}
**Локация:** {candidate.get('location', 'N/A')}
**Ожидаемая ЗП:** {format_salary(candidate.get('salary_min'), candidate.get('salary_max'))}
**Тип занятости:** {candidate.get('employment', 'N/A')}
**Удалённая работа:** {candidate.get('remote', 'N/A')}
**Резюме:** {candidate.get('summary', 'N/A')[:300]}

## ЗАДАЧА:
Оцени соответствие кандидата вакансии по критериям из системного промпта.
Верни результат в формате JSON."""