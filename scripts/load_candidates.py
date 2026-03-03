import sys
import asyncio
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src.core.database import create_async_session
from src.services.candidates.parser import load_candidates_from_csv_async


async def main():
    db = await create_async_session()
    csv_path = Path(__file__).parent.parent / 'data' / 'candidates.csv'
    
    try:
        with open(csv_path, 'rb') as f:
            file_content = f.read()
        
        count = await load_candidates_from_csv_async(db, file_content)
        print(f"Загружено {count} кандидатов")
    except Exception as e:
        print(f"Ошибка: {e}")
        await db.rollback()
        raise
    finally:
        await db.close()


if __name__ == '__main__':
    asyncio.run(main())