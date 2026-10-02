.PHONY: up down logs backend-test frontend-check

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

backend-test:
	cd backend && python3 -m pytest -q

frontend-check:
	cd client-web && npm run typecheck && npm run lint && npm run build
	cd admin-web && npm run typecheck && npm run lint && npm run build
