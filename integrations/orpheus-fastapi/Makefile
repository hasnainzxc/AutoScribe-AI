.PHONY: dev-rocm dev-cuda dev-cpu down logs build-rocm

# Ensure UID/GID are available to compose without editing .env
UID := $(shell id -u)
GID := $(shell id -g)

dev-rocm:
	UID=$(UID) GID=$(GID) docker compose -f docker-compose-gpu-rocm.yml -f docker-compose.dev.yml up --build

dev-cuda:
	UID=$(UID) GID=$(GID) docker compose -f docker-compose-gpu.yml -f docker-compose.dev.yml up --build

dev-cpu:
	UID=$(UID) GID=$(GID) docker compose -f docker-compose-cpu.yaml -f docker-compose.dev.yml up --build

down:
	UID=$(UID) GID=$(GID) docker compose down

logs:
	docker compose logs -f

build-rocm:
	UID=$(UID) GID=$(GID) docker compose -f docker-compose-gpu-rocm.yml build orpheus-fastapi

