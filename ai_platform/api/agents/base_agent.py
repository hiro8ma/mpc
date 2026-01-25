"""
AI Agent with LangChain/LangGraph

MCPツールを使用可能なAIエージェント
"""

from typing import List, Optional, Dict, Any
from langchain_core.tools import BaseTool
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver


class AIAgent:
    """
    LangGraph ReActエージェント

    - MCPツールをLangChainツールとして使用
    - 会話履歴をメモリに保持
    - プロンプトテンプレートを適用
    """

    def __init__(
        self,
        tools: List[BaseTool],
        model_name: str = "gpt-4o-mini",
        system_prompt: Optional[str] = None
    ):
        self.tools = tools
        self.model_name = model_name
        self.system_prompt = system_prompt or self._default_system_prompt()

        # LLMの初期化
        self.llm = ChatOpenAI(model=model_name, temperature=0)

        # メモリ（会話履歴の保持）
        self.memory = MemorySaver()

        # ReActエージェントの作成
        self.agent = create_react_agent(
            model=self.llm,
            tools=self.tools,
            checkpointer=self.memory
        )

    def _default_system_prompt(self) -> str:
        return """あなたは優秀なAIアシスタントです。
ユーザーの質問に対して、利用可能なツールを適切に使用して回答してください。

## 利用可能なツール
ツールは「サーバー名__ツール名」の形式で提供されています。
例: design-system__get-components

## 回答のガイドライン
- 日本語で回答してください
- ツールの実行結果を分かりやすく説明してください
- 不明な点があれば確認してください
"""

    async def chat(
        self,
        message: str,
        thread_id: str = "default"
    ) -> str:
        """
        メッセージを処理して回答を生成

        Args:
            message: ユーザーのメッセージ
            thread_id: 会話スレッドID（履歴管理用）

        Returns:
            AIの回答
        """
        config = {"configurable": {"thread_id": thread_id}}

        # システムプロンプトを含むメッセージを構築
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=message)
        ]

        # エージェントを実行
        result = await self.agent.ainvoke(
            {"messages": messages},
            config=config
        )

        # 最後のAIメッセージを取得
        ai_messages = [m for m in result["messages"] if isinstance(m, AIMessage)]
        if ai_messages:
            return ai_messages[-1].content

        return "回答を生成できませんでした。"

    def get_available_tools(self) -> List[Dict[str, str]]:
        """利用可能なツール一覧を取得"""
        return [
            {
                "name": tool.name,
                "description": tool.description
            }
            for tool in self.tools
        ]


class AgentWithPromptTemplate(AIAgent):
    """
    プロンプトテンプレートを使用するエージェント

    特定のユースケース向けにカスタマイズされたプロンプトを使用
    """

    def __init__(
        self,
        tools: List[BaseTool],
        prompt_template: str,
        model_name: str = "gpt-4o-mini"
    ):
        super().__init__(
            tools=tools,
            model_name=model_name,
            system_prompt=prompt_template
        )


# プリセットエージェント
def create_design_system_agent(tools: List[BaseTool]) -> AIAgent:
    """デザインシステム専用エージェント"""
    prompt = """あなたはUIデザインとフロントエンド開発の専門家です。
デザインシステムのツールを使用して、ユーザーの質問に回答してください。

## 得意なこと
- コンポーネントの使い方の説明
- デザイントークンの値の提供
- 適切なアイコンの提案
- UIパターンの提案

## 回答のガイドライン
- コード例を含めて説明してください
- デザイントークンの具体的な値（色コード、px値など）を示してください
- 複数の選択肢がある場合は比較して説明してください
"""
    # デザインシステム関連のツールのみフィルタ
    ds_tools = [t for t in tools if "design-system" in t.name]
    return AIAgent(tools=ds_tools, system_prompt=prompt)


def create_general_agent(tools: List[BaseTool]) -> AIAgent:
    """汎用エージェント"""
    return AIAgent(tools=tools)
