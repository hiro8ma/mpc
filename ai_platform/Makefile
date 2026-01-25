.PHONY: install run dev test

# Install dependencies
install:
	uv sync

# Run API server
run:
	cd api && uv run python main.py

# Run with auto-reload (development)
dev:
	cd api && uv run uvicorn main:app --reload --port 8000

# Run tests
test:
	uv run pytest
