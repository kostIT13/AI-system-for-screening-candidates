import csv
import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from src.models.candidates import Candidates


def parse_skills(skills_str: str) -> Optional[List[str]]:
    if not skills_str or skills_str.strip() == '':
        return None
    return [skill.strip() for skill in skills_str.split(',')]


def parse_exp_years(exp_str: str) -> Optional[int]:
    if not exp_str or exp_str.strip() == '':
        return None
    try:
        return int(exp_str)
    except ValueError:
        return None


def load_candidates_from_csv(db: Session, csv_path: str) -> int:
    count = 0
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            candidate = Candidates(
                id=str(uuid.uuid4()),
                category=row.get('Category', ''),
                title=row.get('Title', ''),
                exp_years=parse_exp_years(row.get('Exp_Years', '')),
                key_skills=parse_skills(row.get('Key_Skills', '')),
                location=row.get('Location', ''),
                salary_min=int(row['Salary_Min']) if row.get('Salary_Min') else None,
                salary_max=int(row['Salary_Max']) if row.get('Salary_Max') else None,
                employment=row.get('Employment', ''),
                remote=row.get('Remote', ''),
                summary=row.get('Summary', '')[:500] if row.get('Summary') else None
            )
            db.add(candidate)
            count += 1
    db.commit()
    return count