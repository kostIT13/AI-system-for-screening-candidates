import csv
import uuid
import re
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from src.models.vacancies import Vacancies


def parse_skills(skills_str: str) -> Optional[List[str]]:
    if not skills_str or skills_str.strip() == '':
        return None
    return [skill.strip() for skill in skills_str.split(',')]


def parse_exp_years(exp_str: str) -> Tuple[Optional[int], Optional[int]]:
    if not exp_str or exp_str.strip() == '':
        return None, None
    
    exp_str = exp_str.strip()
    
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


def load_vacancies_from_csv(db: Session, csv_path: str) -> int:
    count = 0
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            exp_min, exp_max = parse_exp_years(row.get('Exp_Years', ''))
            
            vacancy = Vacancies(
                id=str(uuid.uuid4()),
                category=row.get('Category', ''),
                title=row.get('Title', ''),
                exp_years_min=exp_min,
                exp_years_max=exp_max,  
                key_skills=parse_skills(row.get('Key_Skills', '')),
                location=row.get('Location', ''),
                salary_min=int(row['Salary_Min']) if row.get('Salary_Min') else None,
                salary_max=int(row['Salary_Max']) if row.get('Salary_Max') else None,
                employment=row.get('Employment', ''),
                remote=row.get('Remote', ''),
                summary=row.get('Summary', '')[:500] if row.get('Summary') else None,
                status='active'
            )
            db.add(vacancy)
            count += 1
    db.commit()
    return count