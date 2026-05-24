#!/bin/bash
# 紫微斗数排盘系统 — 快速启动
set -euo pipefail

cd "$(dirname "$0")"

PYTHON=${PYTHON:-python3}

if [ ! -d .venv ]; then
  "$PYTHON" -m venv .venv
fi

source .venv/bin/activate
python -m pip install -q -r requirements.txt

PORT=${PORT:-8088}
echo "🔮 紫微斗数排盘系统启动中..."
echo "   浏览器打开: http://localhost:$PORT"
exec python -m uvicorn ziwei.api.server:app --host 0.0.0.0 --port "$PORT"
