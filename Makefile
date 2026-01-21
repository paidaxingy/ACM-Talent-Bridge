PY ?= python3
VENV ?= .venv

.PHONY: venv venv-fish deps backend-dev worker

venv:
	$(PY) -m venv $(VENV)
	$(VENV)/bin/python -m pip install -U pip
	$(VENV)/bin/pip install -r backend/requirements.txt

# fish users can run: source .venv/bin/activate.fish
venv-fish: venv
	@echo "Run: source $(VENV)/bin/activate.fish"

deps:
	docker compose up -d mysql redis

backend-dev:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

worker:
	cd backend && celery -A app.core.celery_app:celery worker -l INFO
