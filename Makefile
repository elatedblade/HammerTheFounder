.PHONY: up down logs backend-test frontend-check backend-locks

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

backend-test:
	cd backend && python3 -m pytest -q

backend-locks:
	python3 -m pip install --upgrade pip-tools
	pip-compile --generate-hashes --output-file=backend/requirements.lock --strip-extras backend/pyproject.toml
	pip-compile --extra=dev --generate-hashes --output-file=backend/requirements-dev.lock --strip-extras backend/pyproject.toml

frontend-check:
	cd client-web && npm run typecheck && npm run lint && npm run build
	cd admin-web && npm run typecheck && npm run lint && npm run build
