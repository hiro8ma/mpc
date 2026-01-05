.PHONY: run inspect http help

run:
	uv run openapi_server.py

inspect:
	npx @modelcontextprotocol/inspector uv run openapi_server.py

http:
	uv run openapi_server.py --http

help:
	@echo "Available commands:"
	@echo "  make run     - Run server (stdio)"
	@echo "  make inspect - Run with MCP Inspector"
	@echo "  make http    - Run HTTP mode (port 8000)"
