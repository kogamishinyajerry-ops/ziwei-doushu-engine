"""
紫微斗数 API 服务 — FastAPI
"""

import sys
import os
from pathlib import Path

# 确保项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional

from ziwei.chart.engine import generate_chart, chart_to_dict, print_chart

APP_VERSION = "0.8.0"
DEFAULT_PORT = 8088


def _cors_origins() -> list[str]:
    raw = os.environ.get("ZIWEI_CORS_ORIGINS", "")
    if raw:
        return [origin.strip() for origin in raw.split(",") if origin.strip()]
    return [
        "http://localhost:8088",
        "http://127.0.0.1:8088",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


app = FastAPI(
    title="紫微斗数排盘系统",
    description="Zi Wei Dou Shu — Professional Chart Calculation API",
    version=APP_VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
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
    """主页面 — 桌面版."""
    html_path = Path(__file__).parent.parent.parent / "desktop" / "index.html"
    if html_path.exists():
        return HTMLResponse(html_path.read_text(encoding="utf-8"))
    # fallback to old frontend
    old_path = Path(__file__).parent.parent.parent / "frontend" / "index.html"
    if old_path.exists():
        return HTMLResponse(old_path.read_text(encoding="utf-8"))
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
    huoling: str = Query("mainstream", description="火铃流派: mainstream/songban"),
):
    """生成命盘 + 完整分析."""
    try:
        if huoling not in {"mainstream", "songban"}:
            raise HTTPException(status_code=400, detail="huoling must be mainstream or songban")
        chart = generate_chart(year, month, day, hour, minute, name, gender, city,
                               huoling_variant=huoling)
        return JSONResponse(chart_to_dict(chart, include_analysis=True))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/explain")
async def get_explain(
    year: int = Query(..., ge=1900, le=2100),
    month: int = Query(..., ge=1, le=12),
    day: int = Query(..., ge=1, le=31),
    hour: int = Query(..., ge=0, le=23),
    minute: int = Query(0, ge=0, le=59),
    name: str = Query(""),
    gender: str = Query("男"),
    city: str = Query(""),
    huoling: str = Query("mainstream", description="火铃流派: mainstream/songban"),
):
    """安星"为什么"解释 — 每颗星的规则/公式/推导/出处 (透明可验证)."""
    try:
        if huoling not in {"mainstream", "songban"}:
            raise HTTPException(status_code=400, detail="huoling must be mainstream or songban")
        from ziwei.chart.explain import explain_chart
        chart = generate_chart(year, month, day, hour, minute, name, gender, city,
                               huoling_variant=huoling)
        return JSONResponse({
            "ming_palace": chart.ming_palace,
            "shen_palace": chart.shen_palace,
            "wuxing_ju": chart.wuxing_ju_name,
            "explain": explain_chart(chart),
            "quality_flags": chart.quality_flags,
        })
    except HTTPException:
        raise
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
    provider: str = Query("auto", description="LLM提供者: auto/minimax/deepseek/openai"),
):
    """生成LLM增强解读 (或本地回退)."""
    try:
        if provider not in {"auto", "minimax", "deepseek", "openai"}:
            raise HTTPException(status_code=400, detail="provider must be one of auto/minimax/deepseek/openai")

        chart = generate_chart(year, month, day, hour, minute, name, gender, city)
        chart_dict = chart_to_dict(chart, include_analysis=True)
        
        from ziwei.analysis.llm_prompt import enhance_chart_with_llm
        llm_provider = None if provider == "auto" else provider
        llm_result = enhance_chart_with_llm(chart_dict, mode=mode, provider=llm_provider)
        quality_flags = dict(chart_dict.get("quality_flags", {}))
        if llm_result.get("llm_reading"):
            response_source = "llm"
            llm_result.setdefault("source", "llm")
            llm_result.setdefault("source_detail", llm_result.get("llm_provider", "llm"))
            quality_flags["llm"] = {
                "status": "llm_ok",
                "fallback": False,
                "source": llm_result.get("llm_provider", "llm"),
            }
        elif llm_result.get("local_reading"):
            response_source = "local"
            llm_result.setdefault("source", "local")
            llm_result.setdefault("source_detail", "local_rules")
            quality_flags["llm"] = {
                "status": "local_fallback",
                "fallback": True,
                "source": "local",
                "reason": llm_result.get("note", "local fallback"),
            }
        else:
            response_source = "local"
            llm_result.setdefault("source", "local")
            llm_result.setdefault("source_detail", "unavailable")
            quality_flags["llm"] = {
                "status": "unavailable",
                "fallback": True,
                "source": "unknown",
                "reason": llm_result.get("error", "empty reading result"),
            }
        quality_flags["analysis"] = {
            "status": "rule_based",
            "fallback": False,
            "source": llm_result.get("source_detail", "local_rules")
            if response_source == "local" else "llm_prompt",
        }
        
        return JSONResponse({
            "chart": chart_dict,
            "reading": llm_result,
            "source": response_source,
            "quality_flags": quality_flags,
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/liunian")
async def get_liunian(
    year: int = Query(..., ge=1900, le=2100),
    month: int = Query(..., ge=1, le=12),
    day: int = Query(..., ge=1, le=31),
    hour: int = Query(..., ge=0, le=23),
    minute: int = Query(0, ge=0, le=59),
    name: str = Query(""),
    gender: str = Query("男"),
    city: str = Query(""),
    target_year: int = Query(None, description="目标流年年份, 默认当前年"),
    count: int = Query(3, ge=1, le=10, description="分析年数"),
):
    """生成流年运势分析."""
    try:
        from datetime import datetime
        from ziwei.chart.engine import generate_chart, chart_to_dict
        from ziwei.analysis.liunian import (
            calculate_liunian_info, analyze_liunian, analyze_multi_years, liunian_to_dict
        )
        from ziwei.calendar.constants import EARTHLY_BRANCHES

        # 默认目标流年 = 当前年, 避免硬编码年份随时间漂移
        if target_year is None:
            target_year = datetime.now().year
        
        chart = generate_chart(year, month, day, hour, minute, name, gender, city)
        chart_dict = chart_to_dict(chart, include_analysis=True)
        
        # 构建 auxiliary data
        palace_stars = {}
        palace_branch_map = {}
        for p in chart.palaces:
            palace_stars[p.name] = p.stars
            palace_branch_map[p.name] = EARTHLY_BRANCHES.index(p.branch)
        
        ming_branch = chart.palaces[0].branch if chart.palaces else "子"
        ming_index = EARTHLY_BRANCHES.index(ming_branch)
        
        sihua_map = chart.sihua_map
        
        # 流年分析
        analyses = analyze_multi_years(
            chart, palace_stars, palace_branch_map,
            ming_index, target_year, count
        )
        
        return JSONResponse({
            "chart": chart_dict,
            "liunian": [liunian_to_dict(a) for a in analyses],
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/health")
async def health():
    """健康检查."""
    return {"status": "ok", "version": APP_VERSION}


# ═══════════════════════════════════════════
# 合盘 API
# ═══════════════════════════════════════════

class HepanRequest(BaseModel):
    name1: str = Field(..., description="命主1姓名")
    year1: int = Field(..., ge=1900, le=2100)
    month1: int = Field(..., ge=1, le=12)
    day1: int = Field(..., ge=1, le=31)
    hour1: int = Field(..., ge=0, le=23)
    minute1: int = Field(0, ge=0, le=59)
    gender1: str = Field("男", description="命主1性别")
    city1: str = Field("", description="命主1出生城市")
    name2: str = Field(..., description="命主2姓名")
    year2: int = Field(..., ge=1900, le=2100)
    month2: int = Field(..., ge=1, le=12)
    day2: int = Field(..., ge=1, le=31)
    hour2: int = Field(..., ge=0, le=23)
    minute2: int = Field(0, ge=0, le=59)
    gender2: str = Field("女", description="命主2性别")
    city2: str = Field("", description="命主2出生城市")


@app.post("/api/hepan")
async def hepan_post(req: HepanRequest):
    """合盘分析 (POST)."""
    try:
        from ziwei.chart.engine import generate_chart, chart_to_dict
        from ziwei.analysis.hepan import analyze_hepan
        
        chart1 = generate_chart(req.year1, req.month1, req.day1,
                                req.hour1, req.minute1, req.name1, req.gender1, req.city1)
        chart2 = generate_chart(req.year2, req.month2, req.day2,
                                req.hour2, req.minute2, req.name2, req.gender2, req.city2)
        
        d1 = chart_to_dict(chart1, include_analysis=True)
        d2 = chart_to_dict(chart2, include_analysis=True)
        
        result = analyze_hepan(d1, d2)
        
        # 转换为 JSON 友好格式
        return JSONResponse({
            "person1": result.person1,
            "person2": result.person2,
            "dimensions": [
                {"name": d.name, "score": d.score, "label": d.label,
                 "good": d.good, "bad": d.bad, "detail": d.detail}
                for d in result.dimensions
            ],
            "total_score": result.total_score,
            "total_stars": result.total_stars,
            "summary": result.summary,
            "verdict": result.verdict,
            "compatibility_tags": result.compatibility_tags,
            "shared_stars": result.shared_stars,
            "sihua_interactions": result.sihua_interactions,
            "key_strengths": result.key_strengths,
            "key_challenges": result.key_challenges,
            "charts": {"chart1": d1, "chart2": d2},
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/hepan")
async def hepan_get(
    name1: str = Query(""), year1: int = Query(...), month1: int = Query(...),
    day1: int = Query(...), hour1: int = Query(...), minute1: int = Query(0),
    gender1: str = Query("男"), city1: str = Query(""),
    name2: str = Query(""), year2: int = Query(...), month2: int = Query(...),
    day2: int = Query(...), hour2: int = Query(...), minute2: int = Query(0),
    gender2: str = Query("女"), city2: str = Query(""),
):
    """合盘分析 (GET)."""
    try:
        from ziwei.chart.engine import generate_chart, chart_to_dict
        from ziwei.analysis.hepan import analyze_hepan
        
        chart1 = generate_chart(year1, month1, day1, hour1, minute1, name1, gender1, city1)
        chart2 = generate_chart(year2, month2, day2, hour2, minute2, name2, gender2, city2)
        
        d1 = chart_to_dict(chart1, include_analysis=True)
        d2 = chart_to_dict(chart2, include_analysis=True)
        
        result = analyze_hepan(d1, d2)
        
        return JSONResponse({
            "person1": result.person1,
            "person2": result.person2,
            "dimensions": [
                {"name": d.name, "score": d.score, "label": d.label,
                 "good": d.good, "bad": d.bad, "detail": d.detail}
                for d in result.dimensions
            ],
            "total_score": result.total_score,
            "total_stars": result.total_stars,
            "summary": result.summary,
            "verdict": result.verdict,
            "compatibility_tags": result.compatibility_tags,
            "shared_stars": result.shared_stars,
            "sihua_interactions": result.sihua_interactions,
            "key_strengths": result.key_strengths,
            "key_challenges": result.key_challenges,
            "charts": {"chart1": d1, "chart2": d2},
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ═══════════════════════════════════════════
# 八字分析 API
# ═══════════════════════════════════════════

@app.get("/api/bazi")
async def get_bazi(
    year: int = Query(..., ge=1900, le=2100),
    month: int = Query(..., ge=1, le=12),
    day: int = Query(..., ge=1, le=31),
    hour: int = Query(..., ge=0, le=23),
    minute: int = Query(0, ge=0, le=59),
    name: str = Query(""),
    gender: str = Query("男"),
    city: str = Query(""),
    target_year: int = Query(None, description="目标流年年份, 默认当年"),
    count: int = Query(3, ge=1, le=5, description="分析年数"),
):
    """
    八字排盘 + 十神分析 + 用神推断 + 流年.
    
    返回:
    - bazi: 八字完整分析 (四柱、日主、十神、用神、格局)
    - liunian: 八字流年分析列表
    """
    try:
        from ..analysis.bazi import (
            analyze_bazi, bazi_to_dict,
            analyze_liunian_bazi, analyze_multi_years_bazi, liunian_bazi_to_dict,
        )
        
        chart = generate_chart(year, month, day, hour, minute, name, gender, city)
        
        # Build four pillars from chart attributes
        fp = {
            "year": chart.year_pillar,
            "month": chart.month_pillar,
            "day": chart.day_pillar,
            "hour": chart.hour_pillar,
        }
        
        # 八字分析
        bazi = analyze_bazi(
            fp.get("year", ""),
            fp.get("month", ""),
            fp.get("day", ""),
            fp.get("hour", ""),
        )
        
        # 流年
        ty = target_year or year  # 默认当年
        year_branch_birth = fp.get("year", "子")[1] if len(fp.get("year", "子")) >= 2 else "子"
        liunian_list = analyze_multi_years_bazi(bazi, year_branch_birth, ty, count)
        
        return JSONResponse({
            "bazi": bazi_to_dict(bazi),
            "liunian": [liunian_bazi_to_dict(ln) for ln in liunian_list],
            "chart_summary": {
                "name": name or "未命名",
                "gender": gender,
                "zodiac": chart.zodiac,
                "ming_palace": chart.ming_palace,
                "wuxing_ju": chart.wuxing_ju,
            },
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))


# ═══════════════════════════════════════════
# 智能问答 API
# ═══════════════════════════════════════════

class AskRequest(BaseModel):
    question: str = Field(..., description="用户问题")
    name: str = Field("", description="姓名(可选, 用于排盘)")
    year: int = Field(None, ge=1900, le=2100)
    month: int = Field(None, ge=1, le=12)
    day: int = Field(None, ge=1, le=31)
    hour: int = Field(None, ge=0, le=23)
    minute: int = Field(0, ge=0, le=59)
    gender: str = Field("男")
    city: str = Field("")
    use_llm: bool = Field(True, description="是否接真实 LLM 润色 (无 key 自动回退本地, 离线可用)")
    provider: str = Field("auto", description="LLM 提供者: auto/minimax/deepseek/openai")


def _advisor_response(question: str, chart_dict: dict, use_llm: bool, provider: str) -> dict:
    """共享的诚实顾问响应组装 (POST/GET 复用)。"""
    from ziwei.analysis.advisor import advise
    llm_provider = None if provider in (None, "auto") else provider
    result = advise(question, chart_dict, use_llm=use_llm, provider=llm_provider)

    quality_flags = _build_advisor_quality_flags(result, chart_dict)
    quality_flags["llm"] = result.get("llm", {"used": False, "reason": "local_only"})
    resp = {
        "question": question,
        "answer": result["answer"],
        "category": result["category"],
        "confidence": result["confidence"],
        "needs_chart": result["needs_chart"],
        "used_knowledge": result["used_knowledge"],
        "chart_references": result.get("chart_references", []),
        "grounding": result.get("grounding"),
        "honesty": result.get("honesty"),
        "answer_source": result.get("answer_source", "local"),
        "llm": result.get("llm", {"used": False}),
        "source": "local_fallback" if quality_flags["analysis"]["fallback"] else "advisor_rules",
        "quality_flags": quality_flags,
    }
    # LLM 润色时保留规则引擎原文供对照核验 (透明原则)
    if result.get("answer_source") == "llm":
        resp["local_answer"] = result.get("local_answer", "")
    if chart_dict:
        resp["chart"] = chart_dict
    return resp


@app.post("/api/ask")
async def ask_post(req: AskRequest):
    """智能问答 (POST)."""
    try:
        chart_dict = None
        if req.year is not None and req.month is not None and req.day is not None and req.hour is not None:
            from ziwei.chart.engine import generate_chart, chart_to_dict
            chart = generate_chart(req.year, req.month, req.day,
                                   req.hour, req.minute, req.name, req.gender, req.city)
            chart_dict = chart_to_dict(chart, include_analysis=True)

        resp = _advisor_response(req.question, chart_dict, req.use_llm, req.provider)
        return JSONResponse(resp)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/ask")
async def ask_get(
    q: str = Query(..., description="用户问题"),
    name: str = Query(""), year: int = Query(None), month: int = Query(None),
    day: int = Query(None), hour: int = Query(None), minute: int = Query(0),
    gender: str = Query("男"), city: str = Query(""),
    use_llm: bool = Query(True), provider: str = Query("auto"),
):
    """智能问答 (GET)."""
    try:
        chart_dict = None
        if year is not None and month is not None and day is not None and hour is not None:
            from ziwei.chart.engine import generate_chart, chart_to_dict
            chart = generate_chart(year, month, day, hour, minute, name, gender, city)
            chart_dict = chart_to_dict(chart, include_analysis=True)

        resp = _advisor_response(q, chart_dict, use_llm, provider)
        return JSONResponse(resp)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def _build_advisor_quality_flags(result: dict, chart_dict: dict = None) -> dict:
    """Build source flags for rule-based advisor answers."""
    flags = dict((chart_dict or {}).get("quality_flags", {}))
    if result.get("needs_chart"):
        flags["analysis"] = {
            "status": "local_fallback",
            "fallback": True,
            "source": "advisor_rules",
            "reason": "chart_required",
        }
    else:
        flags["analysis"] = {
            "status": "rule_based",
            "fallback": False,
            "source": "advisor_rules",
        }
    return flags


if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", DEFAULT_PORT))
    uvicorn.run(app, host="0.0.0.0", port=port)
