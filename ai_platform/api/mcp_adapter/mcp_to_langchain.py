"""
MCP to LangChain Adapter

MCPサーバーのツールをLangChainのツールに変換する
"""

import asyncio
import json
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel, Field, create_model
from langchain_core.tools import BaseTool, ToolException
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPToolWrapper(BaseTool):
    """MCPツールをLangChainツールとしてラップ"""

    name: str
    description: str
    args_schema: Optional[Type[BaseModel]] = None

    mcp_server: str = ""
    mcp_tool_name: str = ""
    session: Optional[ClientSession] = None

    class Config:
        arbitrary_types_allowed = True

    def _run(self, **kwargs) -> str:
        """同期実行（非推奨）"""
        return asyncio.run(self._arun(**kwargs))

    async def _arun(self, **kwargs) -> str:
        """非同期でMCPツールを実行"""
        if not self.session:
            raise ToolException(f"MCP session not initialized for {self.mcp_server}")

        try:
            result = await self.session.call_tool(self.mcp_tool_name, kwargs)

            # 結果を文字列に変換
            if hasattr(result, 'content'):
                if isinstance(result.content, list) and result.content:
                    first = result.content[0]
                    if hasattr(first, 'text'):
                        return first.text
            return str(result)

        except Exception as e:
            raise ToolException(f"MCP tool execution failed: {e}")


class MCPServerConnection:
    """MCPサーバーへの接続を管理"""

    def __init__(self, name: str, command: str, args: List[str]):
        self.name = name
        self.command = command
        self.args = args
        self.session: Optional[ClientSession] = None
        self._read = None
        self._write = None

    async def connect(self):
        """MCPサーバーに接続"""
        server_params = StdioServerParameters(
            command=self.command,
            args=self.args
        )

        self._read, self._write = await stdio_client(server_params).__aenter__()
        self.session = ClientSession(self._read, self._write)
        await self.session.__aenter__()
        await self.session.initialize()

        return self

    async def disconnect(self):
        """接続を切断"""
        if self.session:
            await self.session.__aexit__(None, None, None)

    async def list_tools(self) -> List[Dict]:
        """利用可能なツール一覧を取得"""
        if not self.session:
            raise RuntimeError("Not connected")

        result = await self.session.list_tools()
        return result.tools


class MCPToolCollector:
    """複数のMCPサーバーからツールを収集してLangChainツールに変換"""

    def __init__(self, config_path: str = "config/mcp_servers.json"):
        self.config_path = config_path
        self.connections: Dict[str, MCPServerConnection] = {}
        self.langchain_tools: List[BaseTool] = []

    def load_config(self) -> Dict:
        """設定ファイルを読み込み"""
        with open(self.config_path, 'r') as f:
            return json.load(f)

    async def connect_all(self):
        """すべてのMCPサーバーに接続"""
        config = self.load_config()

        for server_name, server_config in config.get("mcpServers", {}).items():
            try:
                conn = MCPServerConnection(
                    name=server_name,
                    command=server_config["command"],
                    args=server_config["args"]
                )
                await conn.connect()
                self.connections[server_name] = conn
                print(f"[接続] {server_name}: 成功")
            except Exception as e:
                print(f"[エラー] {server_name}: {e}")

    async def disconnect_all(self):
        """すべての接続を切断"""
        for conn in self.connections.values():
            await conn.disconnect()

    def _create_args_schema(self, input_schema: Dict) -> Optional[Type[BaseModel]]:
        """MCPのinputSchemaからPydanticモデルを動的生成"""
        if not input_schema or "properties" not in input_schema:
            return None

        properties = input_schema.get("properties", {})
        required = input_schema.get("required", [])

        fields = {}
        for prop_name, prop_info in properties.items():
            prop_type = prop_info.get("type", "string")
            prop_desc = prop_info.get("description", "")

            # 型マッピング
            type_map = {
                "string": str,
                "integer": int,
                "number": float,
                "boolean": bool,
                "array": list,
                "object": dict
            }
            python_type = type_map.get(prop_type, str)

            if prop_name in required:
                fields[prop_name] = (python_type, Field(description=prop_desc))
            else:
                fields[prop_name] = (Optional[python_type], Field(default=None, description=prop_desc))

        if not fields:
            return None

        return create_model("ToolArgs", **fields)

    async def collect_tools(self) -> List[BaseTool]:
        """すべてのMCPツールをLangChainツールとして収集"""
        self.langchain_tools = []

        for server_name, conn in self.connections.items():
            try:
                mcp_tools = await conn.list_tools()

                for tool in mcp_tools:
                    # 引数スキーマを生成
                    args_schema = None
                    if hasattr(tool, 'inputSchema'):
                        args_schema = self._create_args_schema(tool.inputSchema)

                    # LangChainツールを作成
                    lc_tool = MCPToolWrapper(
                        name=f"{server_name}__{tool.name}",
                        description=tool.description or f"Tool from {server_name}",
                        args_schema=args_schema,
                        mcp_server=server_name,
                        mcp_tool_name=tool.name,
                        session=conn.session
                    )

                    self.langchain_tools.append(lc_tool)

                print(f"[収集] {server_name}: {len(mcp_tools)}個のツール")

            except Exception as e:
                print(f"[エラー] {server_name}からのツール収集失敗: {e}")

        return self.langchain_tools

    def get_tools_by_server(self, server_name: str) -> List[BaseTool]:
        """特定のサーバーのツールのみ取得"""
        return [t for t in self.langchain_tools if t.mcp_server == server_name]
