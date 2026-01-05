PYTHON ?= python
DOCKER ?= docker compose

.PHONY: dev docker-up smoke lint fmt

dev:
	./scripts/dev/run_all.sh

docker-up:
	$(DOCKER) up --build

smoke:
	./scripts/dev/smoke.sh

lint:
	ruff check .

fmt:
	ruff format .
