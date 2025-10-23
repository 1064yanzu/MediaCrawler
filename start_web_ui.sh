#!/bin/bash
# MediaCrawler Web UI 启动脚本

echo "🚀 启动 MediaCrawler Web UI 控制面板..."
echo ""
echo "📡 服务地址："
echo "  - Web UI:      http://localhost:8000"
echo "  - API 文档:     http://localhost:8000/docs"
echo "  - 交互式文档:   http://localhost:8000/redoc"
echo ""
echo "按 Ctrl+C 停止服务"
echo "────────────────────────────────────────────"
echo ""

# 启动服务
uv run python api_server.py
