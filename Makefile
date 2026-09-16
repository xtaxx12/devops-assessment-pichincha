.PHONY: install test lint format run docker-build docker-run k8s-apply k8s-delete

install:
	pip install -r requirements-dev.txt

test:
	pytest --cov --cov-report=term-missing --cov-report=xml

lint:
	ruff check . && ruff format --check .

format:
	ruff format . && ruff check --fix .

run:
	PYTHONPATH=src uvicorn devops_service.main:app --reload --port 8000

docker-build:
	docker build -t devops-service:local .

docker-run:
	docker run --rm -p 8000:8000 --env-file .env devops-service:local

k8s-apply:
	kubectl apply -k infra/k8s/overlays/prod

k8s-delete:
	kubectl delete -k infra/k8s/overlays/prod
