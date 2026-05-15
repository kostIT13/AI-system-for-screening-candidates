# src/services/vacancies/parser.py
import csv
import uuid
import io
import re
import logging
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.vacancies import Vacancies

logger = logging.getLogger(__name__)


def parse_skills(skills_str: str) -> Optional[List[str]]:
    if not skills_str or not skills_str.strip():
        return None
    return [s.strip() for s in skills_str.split(',') if s.strip()]


def parse_exp_years(exp_str: str) -> Tuple[Optional[int], Optional[int]]:
    if not exp_str or not str(exp_str).strip():
        return None, None
    exp_str = str(exp_str).strip()
    try:
        if '-' in exp_str:
            parts = exp_str.split('-', 1)
            min_exp = int(parts[0].strip()) if parts[0].strip().isdigit() else None
            max_exp = int(parts[1].strip()) if len(parts) > 1 and parts[1].strip().isdigit() else None
            return min_exp, max_exp
        elif '+' in exp_str:
            val = exp_str.replace('+', '').strip()
            return (int(val), None) if val.isdigit() else (None, None)
        elif exp_str.isdigit():
            val = int(exp_str)
            return val, val
    except (ValueError, IndexError):
        pass
    return None, None


def parse_int(value) -> Optional[int]:
    if value is None or str(value).strip() == '':
        return None
    try:
        normalized = re.sub(r"[^\d\-]", "", str(value).strip())
        if normalized in ("", "-"):
            return None
        return int(normalized)
    except (ValueError, TypeError):
        return None


def parse_vacancies_csv(file_content: bytes) -> List[dict]:
    """Парсинг CSV с вакансиями — с отладкой и защитой"""
    vacancies_data = []
    
    try:
        # Пробуем разные кодировки
        for encoding in ['utf-8-sig', 'utf-8', 'cp1251']:
            try:
                csv_content = file_content.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            raise ValueError("Не удалось декодировать файл")
        
        # Отладка: логируем первые строки
        lines = csv_content.split('\n')[:3]
        logger.info(f"CSV preview: {lines}")
        
        reader = csv.DictReader(io.StringIO(csv_content))
        
        # Отладка: проверяем заголовки
        if reader.fieldnames:
            logger.info(f"CSV headers: {reader.fieldnames}")
            # Нормализуем заголовки (убираем лишние пробелы, кавычки)
            reader.fieldnames = [h.strip().strip('"').strip("'") for h in reader.fieldnames]
        
        for row_num, row in enumerate(reader, start=2):
            try:
                # Отладка: логируем строку
                logger.debug(f"Row {row_num}: {row}")
                
                exp_min, exp_max = parse_exp_years(row.get('Exp_Years', ''))
                
                category = (row.get('Category') or '').strip()
                title = (row.get('Title') or '').strip()
                
                vacancy_data = {
                    'id': str(uuid.uuid4()),
                    'category': category or 'Разработчик',  # ✅ Обязательно!
                    'title': title or category or 'Вакансия',
                    'exp_years_min': exp_min,
                    'exp_years_max': exp_max,
                    'key_skills': parse_skills(row.get('Key_Skills', '')),
                    'location': (row.get('Location') or '').strip() or 'Не указана',
                    'salary_min': parse_int(row.get('Salary_Min', '')),
                    'salary_max': parse_int(row.get('Salary_Max', '')),
                    'employment': (row.get('Employment') or '').strip(),
                    'remote': (row.get('Remote') or '').strip(),
                    'summary': ((row.get('Description') or row.get('Summary')) or '')[:500],
                    'status': 'active'
                }
                
                # ✅ Добавляем только если есть категория или заголовок
                if vacancy_data['category'] or vacancy_data['title']:
                    vacancies_data.append(vacancy_data)
                    logger.info(f"✅ Parsed vacancy: {vacancy_data['title']}")
                    
            except Exception as e:
                logger.warning(f"⚠️ Skip row {row_num}: {e}")
                continue
                
    except Exception as e:
        logger.error(f"❌ CSV parse error: {e}", exc_info=True)
        raise
    
    logger.info(f"📊 Total vacancies parsed: {len(vacancies_data)}")
    return vacancies_data


async def load_vacancies_from_csv_async(db: AsyncSession, file_content: bytes) -> int:
    vacancies_data = parse_vacancies_csv(file_content)
    count = 0
    for data in vacancies_data:
        vacancy = Vacancies(**data)
        db.add(vacancy)
        count += 1
    await db.commit()
    return count