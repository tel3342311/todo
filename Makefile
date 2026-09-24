.PHONY: dev test lint build run kind-up kind-load deploy

IMAGE ?= todo-api
TAG   ?= dev

dev:
	uvicorn app.main:app --reload --port 8000

test:
	pytest -q

lint:
	ruff check .

build:
	docker build -t $(IMAGE):$(TAG) .

run:
	docker run --rm -p 8000:8000 $(IMAGE):$(TAG)

kind-up:
	kind create cluster --name harness-lab --config k8s/kind-config.yaml

kind-load:
	kind load docker-image $(IMAGE):$(TAG) --name harness-lab

deploy:
	kubectl apply -k k8s/
