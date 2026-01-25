.PHONY: run inspect http install test

# Install dependencies
install:
	uv sync

# Run MCP server (stdio mode)
run:
	uv run python server.py

# Run MCP Inspector for debugging
inspect:
	uv run mcp dev server.py

# Run in HTTP mode (SSE)
http:
	uv run mcp run server.py --transport sse
