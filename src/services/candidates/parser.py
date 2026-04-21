import csv
import uuid
import io
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.candidates import Candidates


def parse_skills(skills_str: str) -> Optional[List[str]]:
    if not skills_str or skills_str.strip() == '':
        return None
    return [skill.strip() for skill in skills_str.split(',') if skill.strip()]


def parse_exp_years(exp_str: str) -> Optional[int]:
    if not exp_str or str(exp_str).strip() == '':
        return None
    try:
        exp_str = str(exp_str).strip()
        if '-' in exp_str:
            return int(exp_str.split('-')[0].strip())
        elif '+' in exp_str:
            return int(exp_str.replace('+', '').strip())
        return int(exp_str)
    except (ValueError, TypeError):
        return None


def parse_int(value) -> Optional[int]:
    if not value or str(value).strip() == '':
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


async def parse_candidates_csv(file_content: bytes) -> List[dict]:
    candidates_data = []
    csv_content = file_content.decode('utf-8')
    reader = csv.DictReader(io.StringIO(csv_content))
    
    for row in reader:
        candidate_data = {
            'id': str(uuid.uuid4()),
            'category': row.get('Category', '').strip(),
            'title': row.get('Title', '').strip() or row.get('Category', '').strip(),
            'exp_years': parse_exp_years(row.get('Exp_Years', '')),
            'key_skills': parse_skills(row.get('Key_Skills', '')),
            'location': row.get('Location', '').strip() or 'Not specified',
            'salary_min': parse_int(row.get('Salary_Min', '')),
            'salary_max': parse_int(row.get('Salary_Max', '')),
            'employment': row.get('Employment', '').strip(),
            'remote': row.get('Remote', '').strip(),
            'summary': (row.get('Summary', '') or '')[:500],
        }
        if candidate_data['category']:
            candidates_data.append(candidate_data)
    
    return candidates_data


async def load_candidates_from_csv_async(db: AsyncSession, file_content: bytes) -> int:
    candidates_data = await parse_candidates_csv(file_content)
    
    count = 0
    for data in candidates_data:
        candidate = Candidates(**data)
        db.add(candidate)
        count += 1
    
    await db.commit()
    return count