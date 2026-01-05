# OpenAPI MCP Server

OpenAPI specを読み込んで自然言語でAPIを実行するMCPサーバー。

## Tools

- `list_endpoints` - エンドポイント一覧取得（検索可能）
- `get_endpoint_detail` - エンドポイント詳細取得
- `call_api` - API実行

## Environment Variables

| 変数 | 説明 | 例 |
|------|------|-----|
| `OPENAPI_SPEC_PATH` | OpenAPI specファイルパス | `/path/to/swagger.json` |
| `API_BASE_URL` | APIのベースURL | `http://localhost:8001` |
| `API_AUTH_TOKEN` | 認証トークン（オプション） | `your-token` |

## Usage

```bash
OPENAPI_SPEC_PATH=/path/to/spec.json API_BASE_URL=http://localhost:8001 make run
```

## Example

```
> list_endpoints user
エンドポイント一覧 (3件):
GET /v1/users: ユーザー一覧取得
GET /v1/users/{id}: ユーザー詳細取得
POST /v1/users: ユーザー作成

> call_api /v1/users/{id} GET {"id": "123"}
ステータス: 200

レスポンス:
{"id": "123", "name": "Taro"}
```
