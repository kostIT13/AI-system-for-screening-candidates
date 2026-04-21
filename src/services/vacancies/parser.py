import csv
import uuid
import io
import re
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.vacancies import Vacancies


def parse_skills(skills_str: str) -> Optional[List[str]]:
    if not skills_str or skills_str.strip() == '':
        return None
    return [skill.strip() for skill in skills_str.split(',') if skill.strip()]


def parse_exp_years(exp_str: str) -> Tuple[Optional[int], Optional[int]]:
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
    if not value or str(value).strip() == '':
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


async def parse_vacancies_csv(file_content: bytes) -> List[dict]:
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
            'status': 'active' 
        }
        if vacancy_data['category']:
            vacancies_data.append(vacancy_data)
    
    return vacancies_data


async def load_vacancies_from_csv_async(db: AsyncSession, file_content: bytes) -> int:
    vacancies_data = await parse_vacancies_csv(file_content)
    
    count = 0
    for data in vacancies_data:
        vacancy = Vacancies(**data)
        db.add(vacancy)
        count += 1
    
    await db.commit()
    return count