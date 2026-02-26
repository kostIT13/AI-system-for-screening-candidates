import sys
from pathlib import Path
from src.core.database import get_db
from src.services.candidates.parser import load_candidates_from_csv


sys.path.append(str(Path(__file__).parent.parent))

def main():
    db = next(get_db())
    csv_path = Path(__file__).parent.parent / 'data' / 'candidates.csv'
    
    try:
        count = load_candidates_from_csv(db, str(csv_path))
        print(f"Загружено {count} кандидатов")
    except Exception as e:
        print(f"Ошибка: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == '__main__':
    main()