.PHONY: test test-unit test-integration test-cov test-all test-repositories test-services test-api test-scoring

test:
	uv run pytest tests/ -v

test-unit:
	uv run pytest tests/unit/ -v

test-integration:
	uv run pytest tests/integration/ -v || echo "Интеграционные тесты не найдены"

test-cov:
	uv run pytest tests/ -v --cov=src --cov-report=html --cov-report=term

test-e2e:
	uv run pytest tests/e2e/ -v -m e2e

test-repositories:
	uv run pytest tests/unit/test_*repository.py -v

test-services:
	uv run pytest tests/unit/test_*service.py -v

test-api:
	uv run pytest tests/unit/test_*api.py -v

test-scoring:
	uv run pytest tests/unit/test_scoring*.py -v

test-all: test-unit test-integration test-cov

test-fast:
	uv run pytest tests/unit/ -v --tb=short

test-cov-term:
	uv run pytest tests/ -v --cov=src --cov-report=term

test-cov-html:
	uv run pytest tests/ -v --cov=src --cov-report=html
	@echo "Отчёт покрытия доступен в htmlcov/index.html"

test-file:
	@if [ -z "$(FILE)" ]; then \
		echo "Использование: make test-file FILE=path/to/test_file.py"; \
		exit 1; \
	fi
	uv run pytest $(FILE) -v

test-mark:
	@if [ -z "$(MARK)" ]; then \
		echo "Использование: make test-mark MARK=marker_name"; \
		exit 1; \
	fi
	uv run pytest tests/ -v -m $(MARK)

clean:
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name '.pytest_cache' -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '.coverage' -delete
	rm -rf htmlcov/ .coverage .pytest_cache

help:
	@echo "Доступные команды тестирования:"
	@echo "  test                    - Запуск всех тестов"
	@echo "  test-unit               - Только unit тесты"
	@echo "  test-integration        - Только интеграционные тесты"
	@echo "  test-cov                - Тесты с покрытием (HTML + терминал)"
	@echo "  test-cov-term           - Тесты с покрытием (только терминал)"
	@echo "  test-cov-html           - Тесты с покрытием (только HTML)"
	@echo "  test-all                - Все тесты (unit + integration + coverage)"
	@echo "  test-fast               - Быстрые unit тесты"
	@echo "  test-repositories       - Тесты репозиториев"
	@echo "  test-services           - Тесты сервисов"
	@echo "  test-api                - Тесты API endpoints"
	@echo "  test-scoring            - Тесты компонентов скоринга"
	@echo "  test-file FILE=...      - Запуск конкретного тестового файла"
	@echo "  test-mark MARK=...      - Запуск тестов с маркером"
	@echo "  clean                   - Очистка кэша тестов и отчётов"
	@echo "  help                    - Показать эту справку"