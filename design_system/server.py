"""
Design System MCP Server

デザインシステムの情報をAIに提供するMCPサーバー
Ubie UI MCPを参考に実装

提供するツール:
- get-components: コンポーネント一覧を取得
- get-style-types: スタイルの種類を取得
- get-design-tokens: デザイントークンを取得
- get-icon-list: アイコン一覧を取得
- get-icon-detail: アイコン詳細を取得
"""

import json
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP

# サーバー初期化
mcp = FastMCP("design-system")

# ベースディレクトリ
BASE_DIR = Path(__file__).parent


def load_json(file_path: Path) -> dict | list:
    """JSONファイルを読み込む"""
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


# =============================================================================
# Tool 1: get-components
# =============================================================================
@mcp.tool()
def get_components(category: Optional[str] = None) -> str:
    """
    デザインシステムのコンポーネント一覧を取得する

    Args:
        category: フィルタするカテゴリ (例: "form", "layout", "feedback")
                  指定しない場合はすべてのコンポーネントを返す

    Returns:
        コンポーネント一覧（名前、説明、使用例を含む）
    """
    components_file = BASE_DIR / "components" / "components.json"
    components = load_json(components_file)

    if not components:
        return "コンポーネントが定義されていません"

    if category:
        components = [c for c in components if c.get("category") == category]

    if not components:
        return f"カテゴリ '{category}' のコンポーネントが見つかりません"

    result = "# コンポーネント一覧\n\n"
    for comp in components:
        result += f"## {comp['name']}\n"
        result += f"- **カテゴリ**: {comp.get('category', 'N/A')}\n"
        result += f"- **説明**: {comp.get('description', 'N/A')}\n"
        if comp.get("props"):
            result += "- **Props**:\n"
            for prop in comp["props"]:
                required = "必須" if prop.get("required") else "任意"
                result += f"  - `{prop['name']}` ({prop.get('type', 'any')}, {required}): {prop.get('description', '')}\n"
        if comp.get("example"):
            result += f"- **使用例**:\n```tsx\n{comp['example']}\n```\n"
        result += "\n"

    return result


# =============================================================================
# Tool 2: get-style-types
# =============================================================================
@mcp.tool()
def get_style_types() -> str:
    """
    デザインシステムで使用可能なスタイルの種類を取得する

    Returns:
        スタイルタイプ一覧（カラー、サイズ、バリアントなど）
    """
    styles_file = BASE_DIR / "tokens" / "style-types.json"
    styles = load_json(styles_file)

    if not styles:
        return "スタイルタイプが定義されていません"

    result = "# スタイルタイプ一覧\n\n"

    for style_type, values in styles.items():
        result += f"## {style_type}\n"
        if isinstance(values, list):
            for v in values:
                if isinstance(v, dict):
                    result += f"- `{v.get('name', v)}`: {v.get('description', '')}\n"
                else:
                    result += f"- `{v}`\n"
        elif isinstance(values, dict):
            for k, v in values.items():
                result += f"- `{k}`: {v}\n"
        result += "\n"

    return result


# =============================================================================
# Tool 3: get-design-tokens
# =============================================================================
@mcp.tool()
def get_design_tokens(token_type: Optional[str] = None) -> str:
    """
    デザイントークン（色、スペーシング、タイポグラフィなど）を取得する

    Args:
        token_type: 取得するトークンの種類
                   (例: "color", "spacing", "typography", "shadow", "radius")
                   指定しない場合はすべてのトークンを返す

    Returns:
        デザイントークンの値一覧
    """
    tokens_file = BASE_DIR / "tokens" / "design-tokens.json"
    tokens = load_json(tokens_file)

    if not tokens:
        return "デザイントークンが定義されていません"

    if token_type:
        if token_type not in tokens:
            available = ", ".join(tokens.keys())
            return f"トークンタイプ '{token_type}' が見つかりません。利用可能: {available}"
        tokens = {token_type: tokens[token_type]}

    result = "# デザイントークン\n\n"

    for category, values in tokens.items():
        result += f"## {category}\n"
        if isinstance(values, dict):
            for name, value in values.items():
                if isinstance(value, dict):
                    result += f"- `{name}`:\n"
                    for k, v in value.items():
                        result += f"  - {k}: `{v}`\n"
                else:
                    result += f"- `{name}`: `{value}`\n"
        result += "\n"

    return result


# =============================================================================
# Tool 4: get-icon-list
# =============================================================================
@mcp.tool()
def get_icon_list(category: Optional[str] = None) -> str:
    """
    利用可能なアイコンの一覧を取得する

    Args:
        category: フィルタするカテゴリ (例: "action", "navigation", "status")
                  指定しない場合はすべてのアイコンを返す

    Returns:
        アイコン名の一覧
    """
    icons_file = BASE_DIR / "icons" / "icons.json"
    icons = load_json(icons_file)

    if not icons:
        return "アイコンが定義されていません"

    if category:
        icons = [i for i in icons if i.get("category") == category]

    if not icons:
        return f"カテゴリ '{category}' のアイコンが見つかりません"

    result = "# アイコン一覧\n\n"

    # カテゴリでグループ化
    categories = {}
    for icon in icons:
        cat = icon.get("category", "other")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(icon)

    for cat, cat_icons in categories.items():
        result += f"## {cat}\n"
        for icon in cat_icons:
            result += f"- `{icon['name']}`: {icon.get('description', '')}\n"
        result += "\n"

    return result


# =============================================================================
# Tool 5: get-icon-detail
# =============================================================================
@mcp.tool()
def get_icon_detail(icon_name: str) -> str:
    """
    特定のアイコンの詳細情報を取得する

    Args:
        icon_name: アイコン名

    Returns:
        アイコンの詳細情報（SVGデータ、使用例など）
    """
    icons_file = BASE_DIR / "icons" / "icons.json"
    icons = load_json(icons_file)

    if not icons:
        return "アイコンが定義されていません"

    icon = next((i for i in icons if i["name"] == icon_name), None)

    if not icon:
        available = [i["name"] for i in icons[:10]]
        return f"アイコン '{icon_name}' が見つかりません。例: {', '.join(available)}"

    result = f"# {icon['name']}\n\n"
    result += f"- **カテゴリ**: {icon.get('category', 'N/A')}\n"
    result += f"- **説明**: {icon.get('description', 'N/A')}\n"

    if icon.get("keywords"):
        result += f"- **キーワード**: {', '.join(icon['keywords'])}\n"

    if icon.get("svg"):
        result += f"\n## SVG\n```svg\n{icon['svg']}\n```\n"

    if icon.get("usage"):
        result += f"\n## 使用例\n```tsx\n{icon['usage']}\n```\n"

    return result


# =============================================================================
# エントリーポイント
# =============================================================================
if __name__ == "__main__":
    mcp.run()
