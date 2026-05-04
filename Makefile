.PHONY: dev backend frontend test lint typecheck clean install

dev:
	@echo "Starting backend + frontend..."
	@trap 'kill 0' EXIT; \
		uvicorn src.api.routes:app --reload --port 8000 & \
		npm --prefix src/frontend run dev & \
		wait

backend:
	uvicorn src.api.routes:app --reload --port 8000

frontend:
	npm --prefix src/frontend run dev

install:
	pip install -e ".[dev]"
	npm --prefix src/frontend install

test:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

test-coverage:
	pytest --cov=src --cov-report=html

lint:
	ruff check src/ tests/

typecheck:
	mypy src/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name node_modules -exec rm -rf {} + 2>/dev/null || true
