.PHONY: install sync format lint typecheck test complexity coverage gate

install sync:
	uv sync --all-extras --dev

format:
	uv run ruff format .

lint:
	uv run ruff check .

typecheck:
	uv run mypy .

test:
	uv run pytest

complexity:
	uv run radon cc src tests -s -a
	uv run python scripts/check_complexity.py

coverage:
	uv run pytest --cov=data_intel --cov=scripts --cov-branch --cov-report=term-missing

gate:
	uv run ruff format --check .
	uv run ruff check .
	uv run mypy .
	uv run pytest
	uv run radon cc src tests -s -a
	uv run python scripts/check_complexity.py
