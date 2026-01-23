# Image Classifier

CNNによる画像分類MCPサーバー & 学習ノートブック

## 構成

- `notebooks/` - 学習用Jupyter Notebook（Colab対応）
- `server.py` - MCPサーバー実装

## 学習内容

1. 画像データの構造（ピクセル、グレースケール、RGB）
2. 畳み込みニューラルネットワーク（CNN）
3. 誤差逆伝播法
4. 特徴マップと圧縮

## Setup

```bash
uv sync
```

## Usage

```bash
make run      # stdio mode
make inspect  # MCP Inspector
```
