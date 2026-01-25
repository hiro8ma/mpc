# Design System MCP Server

デザインシステムの情報をAIに提供するMCPサーバー。
Ubie UI MCPを参考に実装。

## 機能（MCPツール）

| ツール | 説明 |
|--------|------|
| `get-components` | コンポーネント一覧を取得 |
| `get-style-types` | スタイルの種類を取得 |
| `get-design-tokens` | デザイントークンを取得 |
| `get-icon-list` | アイコン一覧を取得 |
| `get-icon-detail` | アイコン詳細を取得 |

## 使い方

```bash
# インストール
uv sync

# 実行（stdio）
make run

# MCP Inspector
make inspect
```

## ディレクトリ構成

```
design_system/
├── server.py           # MCPサーバー
├── components/         # コンポーネント定義
├── tokens/             # デザイントークン
└── icons/              # アイコン定義
```
