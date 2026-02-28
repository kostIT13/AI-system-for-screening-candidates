import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from alembic import command
from alembic.config import Config


def main():
    alembic_cfg = Config(Path(__file__).parent.parent / "alembic" / "alembic.ini")
    
    command.upgrade(alembic_cfg, "head")
    print("Миграции успешно применены!")


if __name__ == "__main__":
    main()