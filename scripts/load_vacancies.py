import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src.core.database import get_db
from src.services.vacancies.parser import load_vacancies_from_csv


def main():
    db = next(get_db())
    csv_path = Path(__file__).parent.parent / 'data' / 'vacancies_main.csv'
    
    try:
        count = load_vacancies_from_csv(db, str(csv_path))
        print(f"Загружено {count} вакансий")
    except Exception as e:
        print(f"Ошибка: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == '__main__':
    main()