"""
Prompt Template Manager

再利用可能なプロンプトテンプレートを管理
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class PromptTemplate:
    """プロンプトテンプレート"""

    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        template: str,
        variables: List[str] = None,
        category: str = "general",
        tags: List[str] = None
    ):
        self.id = id
        self.name = name
        self.description = description
        self.template = template
        self.variables = variables or []
        self.category = category
        self.tags = tags or []
        self.created_at = datetime.now()

    def render(self, **kwargs) -> str:
        """テンプレートに変数を適用"""
        result = self.template
        for var in self.variables:
            placeholder = f"{{{var}}}"
            if var in kwargs:
                result = result.replace(placeholder, str(kwargs[var]))
        return result

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "template": self.template,
            "variables": self.variables,
            "category": self.category,
            "tags": self.tags
        }


class PromptTemplateManager:
    """
    プロンプトテンプレート管理

    機能:
    - テンプレートの登録・取得・検索
    - カテゴリ別管理
    - 変数の自動抽出と適用
    """

    def __init__(self, templates_dir: str = "prompts/templates"):
        self.templates_dir = Path(templates_dir)
        self.templates: Dict[str, PromptTemplate] = {}
        self._load_builtin_templates()

    def _load_builtin_templates(self):
        """組み込みテンプレートを読み込み"""
        builtin = [
            PromptTemplate(
                id="design-system-helper",
                name="デザインシステムヘルパー",
                description="デザインシステムに関する質問に回答",
                template="""あなたはUIデザインとフロントエンド開発の専門家です。
デザインシステム「{design_system_name}」について質問に回答してください。

## コンテキスト
{context}

## ユーザーの質問
{question}

## 回答のガイドライン
- 具体的なコード例を含めてください
- デザイントークンの値を明示してください
- 複数の選択肢がある場合は比較してください
""",
                variables=["design_system_name", "context", "question"],
                category="design",
                tags=["ui", "frontend", "components"]
            ),
            PromptTemplate(
                id="code-review",
                name="コードレビュー",
                description="コードのレビューとフィードバック",
                template="""あなたは経験豊富なソフトウェアエンジニアです。
以下のコードをレビューしてください。

## レビュー対象コード
```{language}
{code}
```

## レビュー観点
- コードの品質
- ベストプラクティスへの準拠
- 潜在的なバグ
- パフォーマンス
- セキュリティ

## 回答形式
改善点を具体的に指摘し、修正例を示してください。
""",
                variables=["language", "code"],
                category="development",
                tags=["code", "review", "quality"]
            ),
            PromptTemplate(
                id="task-breakdown",
                name="タスク分解",
                description="大きなタスクを小さなステップに分解",
                template="""あなたはプロジェクトマネージャーです。
以下のタスクを実行可能な小さなステップに分解してください。

## タスク
{task_description}

## 制約・コンテキスト
{constraints}

## 回答形式
1. 各ステップを番号付きリストで
2. 各ステップの所要時間の目安
3. 依存関係があれば明示
""",
                variables=["task_description", "constraints"],
                category="project",
                tags=["planning", "task", "breakdown"]
            ),
            PromptTemplate(
                id="slack-summary",
                name="Slack要約",
                description="Slackのスレッドや会話を要約",
                template="""以下のSlackでの会話を要約してください。

## 会話内容
{conversation}

## 要約形式
- 主要な議論ポイント（箇条書き）
- 決定事項
- アクションアイテム（担当者がいれば明記）
- 未解決の課題
""",
                variables=["conversation"],
                category="communication",
                tags=["slack", "summary", "meeting"]
            ),
        ]

        for template in builtin:
            self.templates[template.id] = template

    def register(self, template: PromptTemplate):
        """テンプレートを登録"""
        self.templates[template.id] = template

    def get(self, template_id: str) -> Optional[PromptTemplate]:
        """テンプレートを取得"""
        return self.templates.get(template_id)

    def list_all(self) -> List[Dict]:
        """すべてのテンプレートを一覧"""
        return [t.to_dict() for t in self.templates.values()]

    def list_by_category(self, category: str) -> List[Dict]:
        """カテゴリでフィルタ"""
        return [
            t.to_dict() for t in self.templates.values()
            if t.category == category
        ]

    def search_by_tag(self, tag: str) -> List[Dict]:
        """タグで検索"""
        return [
            t.to_dict() for t in self.templates.values()
            if tag in t.tags
        ]

    def render_template(self, template_id: str, **kwargs) -> str:
        """テンプレートをレンダリング"""
        template = self.get(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")
        return template.render(**kwargs)

    def save_to_file(self, filepath: str):
        """テンプレートをファイルに保存"""
        data = {
            "templates": [t.to_dict() for t in self.templates.values()]
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_from_file(self, filepath: str):
        """ファイルからテンプレートを読み込み"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for t_data in data.get("templates", []):
            template = PromptTemplate(
                id=t_data["id"],
                name=t_data["name"],
                description=t_data["description"],
                template=t_data["template"],
                variables=t_data.get("variables", []),
                category=t_data.get("category", "general"),
                tags=t_data.get("tags", [])
            )
            self.register(template)
