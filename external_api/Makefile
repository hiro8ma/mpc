.PHONY: run inspect http

run:
	uv run python external_api_server.py

inspect:
	npx @modelcontextprotocol/inspector uv run python external_api_server.py

http:
	uv run python external_api_server.py --http
