#!/bin/bash
# 紫微斗数排盘系统 — 快速启动
cd "$(dirname "$0")"
source .venv/bin/activate 2>/dev/null || python3 -m venv .venv && source .venv/bin/activate && pip install fastapi uvicorn pydantic jinja2 -q
PORT=${PORT:-8088}
echo "🔮 紫微斗数排盘系统启动中..."
echo "   浏览器打开: http://localhost:$PORT"
python3 -c "import uvicorn,os;from ziwei.api.server import app;uvicorn.run(app,host='0.0.0.0',port=int(os.environ.get('PORT',8088)))"
