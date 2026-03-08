.PHONY: test test-unit test-integration test-cov

test:
	python -m pytest tests/ -v

test-unit:
	python -m pytest tests/unit/ -v

test-integration:
	python -m pytest tests/integration/ -v

test-cov:
	python -m pytest tests/ -v --cov=src --cov-report=html --cov-report=term

test-e2e:
	python -m pytest tests/e2e/ -v -m e2e

clean:
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name '.pytest_cache' -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '.coverage' -delete
	rm -rf htmlcov/