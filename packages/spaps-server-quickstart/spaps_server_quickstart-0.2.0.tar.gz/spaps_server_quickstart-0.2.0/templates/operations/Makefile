# Operational Makefile template for services adopting spaps-server-quickstart

PYTHON ?= python3.12
POETRY ?= poetry
REGISTRY_IMAGE ?= ghcr.io/example/service
GIT_SHA ?= $(shell git rev-parse --short HEAD)
DEPLOY_HOST ?= your-prod-host
DEPLOY_USER ?= root

.PHONY: install lint format test prepush docker-build docker-push deploy

install:
	$(POETRY) install

format:
	$(POETRY) run ruff format src tests
	$(POETRY) run ruff check src tests --select I --fix

lint:
	$(POETRY) run ruff check src tests
	$(POETRY) run mypy src

test:
	SPAPS_ENV=test $(POETRY) run pytest -q

prepush: format lint test

docker-build:
	docker build --pull -t $(REGISTRY_IMAGE):$(GIT_SHA) -f Dockerfile.prod .

docker-push:
	docker push $(REGISTRY_IMAGE):$(GIT_SHA)
	docker push $(REGISTRY_IMAGE):latest

deploy:
	REGISTRY_IMAGE=$(REGISTRY_IMAGE) IMAGE_TAG=$(GIT_SHA) \
	GHCR_DEPLOY_USER=$(GHCR_DEPLOY_USER) GHCR_DEPLOY_TOKEN=$(GHCR_DEPLOY_TOKEN) \
	bash deploy/deploy.sh $(DEPLOY_HOST) $(DEPLOY_USER)
