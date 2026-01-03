# mpc

Personal repository for experimenting with [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) implementations.

## Structure

| Directory | Description |
|-----------|-------------|
| `calc/` | Calculator MCP server (FastMCP) |
| `db_server/` | Database MCP server with SQLite |
| `external_api/` | Weather, News, IP info APIs |
| `universal_tools/` | Web search, Python sandbox execution |
| `client/` | LLM-integrated MCP client |
| `agent/` | Interactive MCP Agent with LLM task orchestration |

## Getting Started

Each server directory has its own `uv` environment.

```bash
cd <server_dir>
make run      # Run server (stdio)
make inspect  # MCP Inspector
```

### MCP Agent

The `agent/` directory contains an interactive agent that connects to multiple MCP servers and uses LLM for task decomposition and execution.

```bash
cd agent
cp .env.example .env  # Set OPENAI_API_KEY
make run
```

Features:
- Connects to calc, db_server, external_api, universal_tools servers
- LLM-based task planning and execution
- Interactive REPL interface

## Configuration

- `claude_desktop_config.json` - Claude Desktop MCP config (symlinked to `~/Library/Application Support/Claude/`)
- `.claude/settings.json` - Claude Code MCP config

## Resources

- [MCP Documentation](https://modelcontextprotocol.io/)
- [MCP GitHub](https://github.com/modelcontextprotocol)
- [FastMCP](https://gofastmcp.com/)
