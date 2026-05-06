"""
紫微斗数 API 服务 — FastAPI
"""

import sys
import os
from pathlib import Path

# 确保项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional

from ziwei.chart.engine import generate_chart, chart_to_dict, print_chart

app = FastAPI(
    title="紫微斗数排盘系统",
    description="Zi Wei Dou Shu — Professional Chart Calculation API",
    version="0.1.0",
)


class ChartRequest(BaseModel):
    year: int = Field(..., ge=1900, le=2100, description="出生年份")
    month: int = Field(..., ge=1, le=12, description="出生月份")
    day: int = Field(..., ge=1, le=31, description="出生日期")
    hour: int = Field(..., ge=0, le=23, description="出生小时")
    minute: int = Field(0, ge=0, le=59, description="出生分钟")
    name: str = Field("", description="姓名")
    gender: str = Field("男", description="性别 (男/女)")


@app.get("/", response_class=HTMLResponse)
async def root():
    """主页面."""
    html_path = Path(__file__).parent.parent.parent / "frontend" / "index.html"
    if html_path.exists():
        return HTMLResponse(html_path.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>紫微斗数排盘系统</h1><p>前端文件缺失</p>")


@app.get("/api/chart")
async def get_chart(
    year: int = Query(..., ge=1900, le=2100),
    month: int = Query(..., ge=1, le=12),
    day: int = Query(..., ge=1, le=31),
    hour: int = Query(..., ge=0, le=23),
    minute: int = Query(0, ge=0, le=59),
    name: str = Query(""),
    gender: str = Query("男"),
):
    """生成命盘 (GET)."""
    try:
        chart = generate_chart(year, month, day, hour, minute, name, gender)
        return JSONResponse(chart_to_dict(chart))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/chart")
async def post_chart(req: ChartRequest):
    """生成命盘 (POST)."""
    try:
        chart = generate_chart(
            req.year, req.month, req.day,
            req.hour, req.minute, req.name, req.gender
        )
        return JSONResponse(chart_to_dict(chart))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/chart/text")
async def get_chart_text(
    year: int = Query(...),
    month: int = Query(...),
    day: int = Query(...),
    hour: int = Query(...),
    minute: int = Query(0),
    name: str = Query(""),
    gender: str = Query("男"),
):
    """生成命盘 (纯文本)."""
    try:
        chart = generate_chart(year, month, day, hour, minute, name, gender)
        text = print_chart(chart)
        return HTMLResponse(f"<pre>{text}</pre>")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/chart/full")
async def get_chart_full(
    year: int = Query(..., ge=1900, le=2100),
    month: int = Query(..., ge=1, le=12),
    day: int = Query(..., ge=1, le=31),
    hour: int = Query(..., ge=0, le=23),
    minute: int = Query(0, ge=0, le=59),
    name: str = Query(""),
    gender: str = Query("男"),
    city: str = Query(""),
):
    """生成命盘 + 完整分析."""
    try:
        chart = generate_chart(year, month, day, hour, minute, name, gender, city)
        return JSONResponse(chart_to_dict(chart, include_analysis=True))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/cities")
async def search_cities(q: str = Query("", description="搜索关键词")):
    """搜索城市经纬度."""
    from ziwei.calendar.solar_time import search_cities
    results = search_cities(q, limit=15)
    return JSONResponse(results)


@app.get("/api/reading")
async def get_reading(
    year: int = Query(..., ge=1900, le=2100),
    month: int = Query(..., ge=1, le=12),
    day: int = Query(..., ge=1, le=31),
    hour: int = Query(..., ge=0, le=23),
    minute: int = Query(0, ge=0, le=59),
    name: str = Query(""),
    gender: str = Query("男"),
    city: str = Query(""),
    mode: str = Query("full", description="解读模式: full/personality/career/relationship/yearly"),
):
    """生成LLM增强解读 (或本地回退)."""
    try:
        chart = generate_chart(year, month, day, hour, minute, name, gender, city)
        chart_dict = chart_to_dict(chart, include_analysis=True)
        
        from ziwei.analysis.llm_prompt import enhance_chart_with_llm
        llm_result = enhance_chart_with_llm(chart_dict, mode=mode)
        
        return JSONResponse({"chart": chart_dict, "reading": llm_result})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/health")
async def health():
    """健康检查."""
    return {"status": "ok", "version": "0.2.0"}


if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
