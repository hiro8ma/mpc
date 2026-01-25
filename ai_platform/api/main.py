"""
AI Platform - Main API Server

社内AI基盤のメインサーバー
FastAPIベース
"""

import os
import asyncio
from contextlib import asynccontextmanager
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from llm_providers import LLMFactory, LLMProvider
from mcp_adapter.mcp_to_langchain import MCPToolCollector
from agents.base_agent import AIAgent, create_design_system_agent, create_general_agent
from prompts.template_manager import PromptTemplateManager


# グローバル状態
tool_collector: Optional[MCPToolCollector] = None
agents: dict = {}
prompt_manager: Optional[PromptTemplateManager] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """起動時・終了時の処理"""
    global tool_collector, agents, prompt_manager

    print("[起動] AI Platform を起動中...")

    # プロンプトマネージャーの初期化
    prompt_manager = PromptTemplateManager()
    print(f"[完了] プロンプトテンプレート: {len(prompt_manager.templates)}個")

    # MCPツールの収集
    tool_collector = MCPToolCollector("config/mcp_servers.json")
    try:
        await tool_collector.connect_all()
        tools = await tool_collector.collect_tools()
        print(f"[完了] MCPツール: {len(tools)}個")

        # エージェントの初期化
        llm_client = LLMFactory.create_from_env()
        agents["general"] = create_general_agent(tools)
        agents["design-system"] = create_design_system_agent(tools)
        print(f"[完了] エージェント: {len(agents)}個")

    except Exception as e:
        print(f"[警告] MCP接続エラー: {e}")
        print("[継続] MCPなしで起動します")

    print("[完了] AI Platform 起動完了\n")

    yield

    # 終了処理
    print("\n[終了] AI Platform を終了中...")
    if tool_collector:
        await tool_collector.disconnect_all()
    print("[完了] 終了しました")


app = FastAPI(
    title="AI Platform",
    description="社内AI基盤 - MCPツールとLLMを統合",
    version="0.1.0",
    lifespan=lifespan
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== リクエスト/レスポンスモデル ====================

class ChatRequest(BaseModel):
    message: str
    agent: str = "general"  # "general" or "design-system"
    thread_id: str = "default"


class ChatResponse(BaseModel):
    response: str
    agent: str
    thread_id: str


class ToolInfo(BaseModel):
    name: str
    description: str
    server: Optional[str] = None


class PromptTemplateRequest(BaseModel):
    template_id: str
    variables: dict = {}


# ==================== エンドポイント ====================

@app.get("/")
async def root():
    """ヘルスチェック"""
    return {
        "status": "ok",
        "service": "AI Platform",
        "version": "0.1.0"
    }


@app.get("/health")
async def health():
    """詳細なヘルスチェック"""
    tools_count = len(tool_collector.langchain_tools) if tool_collector else 0
    return {
        "status": "healthy",
        "mcp_connected": tool_collector is not None,
        "tools_available": tools_count,
        "agents_available": list(agents.keys()),
        "prompts_available": len(prompt_manager.templates) if prompt_manager else 0
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    チャットエンドポイント

    指定されたエージェントでメッセージを処理
    """
    if request.agent not in agents:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown agent: {request.agent}. Available: {list(agents.keys())}"
        )

    agent = agents[request.agent]

    try:
        response = await agent.chat(
            message=request.message,
            thread_id=request.thread_id
        )
        return ChatResponse(
            response=response,
            agent=request.agent,
            thread_id=request.thread_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tools", response_model=List[ToolInfo])
async def list_tools():
    """利用可能なツール一覧"""
    if not tool_collector:
        return []

    return [
        ToolInfo(
            name=tool.name,
            description=tool.description,
            server=tool.mcp_server if hasattr(tool, 'mcp_server') else None
        )
        for tool in tool_collector.langchain_tools
    ]


@app.get("/agents")
async def list_agents():
    """利用可能なエージェント一覧"""
    return {
        "agents": [
            {
                "id": agent_id,
                "tools_count": len(agent.tools)
            }
            for agent_id, agent in agents.items()
        ]
    }


@app.get("/prompts")
async def list_prompts():
    """利用可能なプロンプトテンプレート一覧"""
    if not prompt_manager:
        return {"templates": []}

    return {"templates": prompt_manager.list_all()}


@app.get("/prompts/{template_id}")
async def get_prompt(template_id: str):
    """特定のプロンプトテンプレートを取得"""
    if not prompt_manager:
        raise HTTPException(status_code=500, detail="Prompt manager not initialized")

    template = prompt_manager.get(template_id)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template not found: {template_id}")

    return template.to_dict()


@app.post("/prompts/render")
async def render_prompt(request: PromptTemplateRequest):
    """プロンプトテンプレートをレンダリング"""
    if not prompt_manager:
        raise HTTPException(status_code=500, detail="Prompt manager not initialized")

    try:
        rendered = prompt_manager.render_template(
            request.template_id,
            **request.variables
        )
        return {"rendered": rendered}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ==================== CLI起動 ====================

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )
