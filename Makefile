.PHONY: help clean test lint format docs build install dev

help:
	@echo "GeoHealth Pipeline - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install     Install dependencies"
	@echo "  make dev         Install dev dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make test        Run tests"
	@echo "  make test-cov    Run tests with coverage"
	@echo "  make lint        Run linting checks"
	@echo "  make format      Format code with black"
	@echo "  make type-check  Type check with mypy"
	@echo ""
	@echo "Building:"
	@echo "  make build       Build package (wheel + sdist)"
	@echo "  make docs        Build documentation"
	@echo "  make docker      Build Docker image"
	@echo ""
	@echo "Running:"
	@echo "  make demo        Run demo pipeline"
	@echo "  make api         Start API server"
	@echo "  make dashboard   Start dashboard"
	@echo "  make up          Start Docker services"
	@echo "  make down        Stop Docker services"
	@echo ""
	@echo "Cleaning:"
	@echo "  make clean       Clean build artifacts"
	@echo "  make clean-all   Clean everything including venv"

install:
	pip install -r requirements.txt

dev:
	pip install -e ".[dev]"

test:
	pytest -v

test-cov:
	pytest -v --cov=. --cov-report=html --cov-report=term

lint:
	flake8 .
	black --check .
	isort --check-only .

format:
	black .
	isort .

type-check:
	mypy geohealth_pipeline_Project.py --ignore-missing-imports || true

docs:
	cd docs && make html
	@echo "Documentation built: docs/_build/html/index.html"

build:
	python -m build

docker:
	docker build -t geohealth-pipeline:1.0.0 .

demo:
	python geohealth_pipeline_Project.py --demo

api:
	uvicorn api.main:app --reload

dashboard:
	streamlit run dashboard/main.py

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build dist .eggs .pytest_cache .mypy_cache

clean-all: clean
	rm -rf venv .venv env .env
	docker-compose down -v

.DEFAULT_GOAL := help
