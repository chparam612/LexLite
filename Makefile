.PHONY: install test lint run-backend run-frontend docker-up docker-down

install:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

test:
	cd backend && pytest -v
	cd frontend && npm run type-check

lint:
	cd backend && flake8 app tests || true
	cd frontend && npm run lint || true

run-backend:
	cd backend && uvicorn app.main:app --reload --port 8000

run-frontend:
	cd frontend && npm run dev

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down
