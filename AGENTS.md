# Repository Guidelines

## Project Structure & Module Organization
- `backend/app/` contains the FastAPI service: `api/routes/` endpoints, `core/` infrastructure, `models/` and `schemas/` data contracts, `services/` business logic, and `tasks/` Celery jobs.
- `backend/resumes/` holds uploaded PDFs and other runtime artifacts; do not treat it as source.
- `frontend/src/` contains the Vue 3 app: `views/`, `layouts/`, `router/`, `stores/`, and `api/`.
- `docker/` holds judge-runner assets, and `docker-compose.yml` wires MySQL, Redis, API, worker, and beat.

## Build, Test, and Development Commands
- `make venv` creates `.venv` and installs backend dependencies from `backend/requirements.txt`.
- `make deps` starts MySQL and Redis with Docker for local backend work.
- `make backend-dev` runs FastAPI with hot reload on `http://localhost:8000`.
- `make worker` starts the Celery worker.
- `cd frontend && npm install && npm run dev` starts the Vite frontend.
- `cd frontend && npm run build` runs `vue-tsc` and builds production assets.
- `docker compose up -d --build` launches the full local stack.

## Coding Style & Naming Conventions
- Python uses 4-space indentation, type hints, and small modules. Keep route handlers thin and place domain logic in `backend/app/services/`.
- Vue and TypeScript follow the existing 2-space style with `<script setup lang="ts">`.
- Use `snake_case` for Python modules, `PascalCase` for Vue SFCs such as `HomeView.vue`, and `camelCase` for TypeScript helpers.
- No formatter or linter config is checked in; match the surrounding style and keep imports tidy.

## Testing Guidelines
- No automated test suite is committed yet. Add backend tests under `backend/tests/` with `test_*.py` names when you introduce non-trivial logic.
- Before opening a PR, run `cd frontend && npm run build`, verify changed API flows in `http://localhost:8000/docs`, and smoke-test touched Celery workflows.
- Note required seed data, env vars, or manual verification steps in the PR description.

## Commit & Pull Request Guidelines
- Prefer Conventional Commit prefixes when possible: `feat(frontend): refresh visual theme`, `fix: correct judge timeout`, `chore: ignore generated artifacts`.
- Keep commits focused; avoid bundling unrelated frontend, backend, and infrastructure changes.
- PRs should include purpose, impacted areas, linked issues, setup or migration notes, and screenshots for UI changes.

## Security & Configuration Tips
- Copy `backend/.env.example` to `backend/.env` and never commit secrets.
- Do not commit uploaded resumes, generated artifacts, or local environment files.
- If a change depends on Docker judging or an AI provider, document the needed environment variables in the PR.
