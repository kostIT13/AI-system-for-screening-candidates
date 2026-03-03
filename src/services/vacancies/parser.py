# import csv
# import uuid
# import re
# from typing import List, Optional, Tuple
# from sqlalchemy.orm import Session
# from src.models.vacancies import Vacancies


# def parse_skills(skills_str: str) -> Optional[List[str]]:
#     if not skills_str or skills_str.strip() == '':
#         return None
#     return [skill.strip() for skill in skills_str.split(',')]


# def parse_exp_years(exp_str: str) -> Tuple[Optional[int], Optional[int]]:
#     if not exp_str or exp_str.strip() == '':
#         return None, None
    
#     exp_str = exp_str.strip()
    
#     if '-' in exp_str:
#         parts = exp_str.split('-')
#         try:
#             min_exp = int(parts[0].strip())
#             max_exp = int(parts[1].strip()) if len(parts) > 1 and parts[1].strip() else None
#             return min_exp, max_exp
#         except ValueError:
#             return None, None
    
#     elif '+' in exp_str:
#         try:
#             min_exp = int(exp_str.replace('+', '').strip())
#             return min_exp, None
#         except ValueError:
#             return None, None
    
#     else:
#         try:
#             exp = int(exp_str)
#             return exp, exp
#         except ValueError:
#             return None, None


# def load_vacancies_from_csv(db: Session, csv_path: str) -> int:
#     count = 0
#     with open(csv_path, 'r', encoding='utf-8') as f:
#         reader = csv.DictReader(f)
#         for row in reader:
#             exp_min, exp_max = parse_exp_years(row.get('Exp_Years', ''))
            
#             vacancy = Vacancies(
#                 id=str(uuid.uuid4()),
#                 category=row.get('Category', ''),
#                 title=row.get('Title', ''),
#                 exp_years_min=exp_min,
#                 exp_years_max=exp_max,  
#                 key_skills=parse_skills(row.get('Key_Skills', '')),
#                 location=row.get('Location', ''),
#                 salary_min=int(row['Salary_Min']) if row.get('Salary_Min') else None,
#                 salary_max=int(row['Salary_Max']) if row.get('Salary_Max') else None,
#                 employment=row.get('Employment', ''),
#                 remote=row.get('Remote', ''),
#                 summary=row.get('Summary', '')[:500] if row.get('Summary') else None,
#                 status='active'
#             )
#             db.add(vacancy)
#             count += 1
#     db.commit()
#     return count

import csv
import uuid
import io
import re
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.vacancies import Vacancies


def parse_skills(skills_str: str) -> Optional[List[str]]:
    """Парсит строку навыков в список"""
    if not skills_str or skills_str.strip() == '':
        return None
    return [skill.strip() for skill in skills_str.split(',') if skill.strip()]


def parse_exp_years(exp_str: str) -> Tuple[Optional[int], Optional[int]]:
    """Парсит опыт: '3-5' → (3, 5), '5+' → (5, None), '4' → (4, 4)"""
    if not exp_str or str(exp_str).strip() == '':
        return None, None
    
    exp_str = str(exp_str).strip()
    
    if '-' in exp_str:
        parts = exp_str.split('-')
        try:
            min_exp = int(parts[0].strip())
            max_exp = int(parts[1].strip()) if len(parts) > 1 and parts[1].strip() else None
            return min_exp, max_exp
        except ValueError:
            return None, None
    elif '+' in exp_str:
        try:
            min_exp = int(exp_str.replace('+', '').strip())
            return min_exp, None
        except ValueError:
            return None, None
    else:
        try:
            exp = int(exp_str)
            return exp, exp
        except ValueError:
            return None, None


def parse_int(value) -> Optional[int]:
    """Безопасный парсинг целых чисел"""
    if not value or str(value).strip() == '':
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


async def parse_vacancies_csv(file_content: bytes) -> List[dict]:
    """
    Парсит CSV и возвращает список словарей (без работы с БД).
    """
    vacancies_data = []
    csv_content = file_content.decode('utf-8')
    reader = csv.DictReader(io.StringIO(csv_content))
    
    for row in reader:
        exp_min, exp_max = parse_exp_years(row.get('Exp_Years', ''))
        
        vacancy_data = {
            'id': str(uuid.uuid4()),
            'category': row.get('Category', '').strip(),
            'title': row.get('Title', '').strip() or row.get('Category', '').strip(),
            'exp_years_min': exp_min,
            'exp_years_max': exp_max,
            'key_skills': parse_skills(row.get('Key_Skills', '')),
            'location': row.get('Location', '').strip() or 'Not specified',
            'salary_min': parse_int(row.get('Salary_Min', '')),
            'salary_max': parse_int(row.get('Salary_Max', '')),
            'employment': row.get('Employment', '').strip(),
            'remote': row.get('Remote', '').strip(),
            'summary': (row.get('Description', '') or row.get('Summary', ''))[:500],
            'status': 'active'  # По умолчанию все вакансии активные
        }
        if vacancy_data['category']:
            vacancies_data.append(vacancy_data)
    
    return vacancies_data


async def load_vacancies_from_csv_async(db: AsyncSession, file_content: bytes) -> int:
    """
    Парсит CSV и сохраняет вакансии в БД (асинхронная версия).
    """
    vacancies_data = await parse_vacancies_csv(file_content)
    
    count = 0
    for data in vacancies_data:
        vacancy = Vacancies(**data)
        db.add(vacancy)
        count += 1
    
    await db.commit()
    return count