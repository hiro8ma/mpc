#!/usr/bin/env python3
"""
OpenAPI MCP Server
OpenAPI specを読み込んで自然言語でAPI実行するMCPサーバー
"""

import json
import os
import re
import time
from typing import Any
import requests
import yaml
from dotenv import load_dotenv
from fastmcp import FastMCP

load_dotenv()

mcp = FastMCP("OpenAPI Server")

# グローバル変数
openapi_spec = {}
base_url = ""
endpoints = []


def load_openapi_spec():
    """OpenAPI specを読み込む"""
    global openapi_spec, base_url, endpoints

    spec_path = os.getenv("OPENAPI_SPEC_PATH", "")
    if not spec_path:
        return

    # ファイル読み込み
    with open(spec_path, "r", encoding="utf-8") as f:
        if spec_path.endswith(".yaml") or spec_path.endswith(".yml"):
            openapi_spec = yaml.safe_load(f)
        else:
            openapi_spec = json.load(f)

    # ベースURL設定
    base_url = os.getenv("API_BASE_URL", "")
    if not base_url:
        # OpenAPI specから推測
        if "servers" in openapi_spec:
            base_url = openapi_spec["servers"][0].get("url", "")
        elif "host" in openapi_spec:
            scheme = openapi_spec.get("schemes", ["https"])[0]
            host = openapi_spec["host"]
            base_path = openapi_spec.get("basePath", "")
            base_url = f"{scheme}://{host}{base_path}"

    # エンドポイント一覧を構築
    endpoints.clear()
    for path, path_item in openapi_spec.get("paths", {}).items():
        for method, operation in path_item.items():
            if method.lower() not in ["get", "post", "put", "delete", "patch"]:
                continue

            # パラメータ情報を収集
            params = []
            for param in operation.get("parameters", []):
                params.append({
                    "name": param.get("name"),
                    "in": param.get("in"),
                    "required": param.get("required", False),
                    "type": param.get("type", param.get("schema", {}).get("type", "string")),
                    "description": param.get("description", "")
                })

            endpoints.append({
                "path": path,
                "method": method.upper(),
                "operationId": operation.get("operationId", ""),
                "summary": operation.get("summary", ""),
                "description": operation.get("description", ""),
                "tags": operation.get("tags", []),
                "parameters": params
            })


# 起動時に読み込み
load_openapi_spec()


@mcp.tool()
def list_endpoints(query: str = "") -> str:
    """
    利用可能なAPIエンドポイント一覧を取得します。

    Args:
        query: 検索クエリ（オプション）。エンドポイント名、パス、説明で絞り込み

    Returns:
        エンドポイント一覧
    """
    if not endpoints:
        return "OpenAPI specが読み込まれていません。OPENAPI_SPEC_PATH環境変数を設定してください。"

    results = []
    query_lower = query.lower()

    for ep in endpoints:
        # クエリでフィルタリング
        if query:
            searchable = f"{ep['path']} {ep['summary']} {ep['description']} {ep['operationId']} {' '.join(ep['tags'])}".lower()
            if query_lower not in searchable:
                continue

        params_str = ""
        if ep["parameters"]:
            param_names = [f"{p['name']}({'必須' if p['required'] else '任意'})" for p in ep["parameters"]]
            params_str = f" | パラメータ: {', '.join(param_names)}"

        results.append(f"{ep['method']} {ep['path']}: {ep['summary']}{params_str}")

    if not results:
        return f"'{query}'に一致するエンドポイントが見つかりませんでした。"

    return f"エンドポイント一覧 ({len(results)}件):\n" + "\n".join(results)


@mcp.tool()
def get_endpoint_detail(path: str, method: str = "GET") -> str:
    """
    特定のエンドポイントの詳細情報を取得します。

    Args:
        path: APIパス（例: /v1/users/{id}）
        method: HTTPメソッド（GET, POST, PUT, DELETE, PATCH）

    Returns:
        エンドポイントの詳細情報
    """
    method = method.upper()

    for ep in endpoints:
        if ep["path"] == path and ep["method"] == method:
            lines = [
                f"## {ep['method']} {ep['path']}",
                f"概要: {ep['summary']}",
                f"説明: {ep['description']}",
                f"操作ID: {ep['operationId']}",
                f"タグ: {', '.join(ep['tags'])}",
                "",
                "### パラメータ:"
            ]

            if ep["parameters"]:
                for p in ep["parameters"]:
                    req = "必須" if p["required"] else "任意"
                    lines.append(f"- {p['name']} ({p['type']}, {p['in']}, {req}): {p['description']}")
            else:
                lines.append("なし")

            return "\n".join(lines)

    return f"エンドポイント {method} {path} が見つかりませんでした。"


@mcp.tool()
def call_api(
    path: str,
    method: str = "GET",
    path_params: dict[str, Any] | None = None,
    query_params: dict[str, Any] | None = None,
    body: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None
) -> str:
    """
    APIを実行します。

    Args:
        path: APIパス（例: /v1/users/{id}）
        method: HTTPメソッド（GET, POST, PUT, DELETE, PATCH）
        path_params: パスパラメータ（例: {"id": "123"}）
        query_params: クエリパラメータ
        body: リクエストボディ（POST/PUT/PATCH用）
        headers: 追加のHTTPヘッダー

    Returns:
        APIレスポンス
    """
    if not base_url:
        return "API_BASE_URLが設定されていません。"

    # パスパラメータを置換
    actual_path = path
    if path_params:
        for key, value in path_params.items():
            actual_path = actual_path.replace(f"{{{key}}}", str(value))

    url = f"{base_url.rstrip('/')}{actual_path}"

    # ヘッダー設定
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)

    # 認証トークン
    auth_token = os.getenv("API_AUTH_TOKEN", "")
    if auth_token:
        req_headers["Authorization"] = f"Bearer {auth_token}"

    try:
        start_time = time.time()
        response = requests.request(
            method=method.upper(),
            url=url,
            params=query_params,
            json=body if body else None,
            headers=req_headers,
            timeout=30
        )
        elapsed_ms = (time.time() - start_time) * 1000

        # レスポンス整形
        status = f"ステータス: {response.status_code}"
        latency = f"レイテンシ: {elapsed_ms:.2f}ms"

        try:
            body_json = response.json()
            body_str = json.dumps(body_json, ensure_ascii=False, indent=2)
        except:
            body_str = response.text[:2000]

        return f"{status} | {latency}\n\nレスポンス:\n{body_str}"

    except requests.exceptions.RequestException as e:
        return f"APIリクエストエラー: {str(e)}"


if __name__ == "__main__":
    import sys
    if "--http" in sys.argv:
        mcp.run(transport="streamable-http", host="127.0.0.1", port=8000)
    else:
        mcp.run()
