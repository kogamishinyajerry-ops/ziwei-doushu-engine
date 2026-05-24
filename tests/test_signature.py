"""
Tests for 专属命盘深度报告 (signature extraction + 犀利 report).

确定性骨架可测 + LLM 路径用注入 caller 免网络 + 离线回退 + 诚实层。
"""

from pathlib import Path
import sys

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ziwei.api.server import app
from ziwei.chart.engine import generate_chart, chart_to_dict
from ziwei.analysis.signature import (
    extract_signature, generate_personal_report, MAIN_STARS,
)

client = TestClient(app)


def _chart():
    return chart_to_dict(
        generate_chart(1995, 8, 16, 16, 30, name="林蕾", gender="女", city="上海"),
        include_analysis=True,
    )


# ─────────────────────────────────────────────
# 特征提取 (确定性)
# ─────────────────────────────────────────────

def test_signature_has_core_fields():
    sig = extract_signature(_chart())
    for k in ("ming_combo", "strongest_palace", "weakest_palace", "ji", "lu",
              "engine", "leak", "peak_daxian", "rarity", "anchors"):
        assert k in sig


def test_ji_palace_matches_huaji_star_location():
    d = _chart()
    sig = extract_signature(d)
    ji_star = d["sihua"]["化忌"]
    # 化忌落宫 = 该星实际所在宫
    star_palace = {s: p["name"] for p in d["palaces"] for s in p["stars"]}
    assert sig["ji"]["star"] == ji_star
    assert sig["ji"]["palace"] == star_palace[ji_star]


def test_strongest_weakest_are_distinct_and_real_palaces():
    d = _chart()
    sig = extract_signature(d)
    names = {p["name"] for p in d["palaces"]}
    assert sig["strongest_palace"]["palace"] in names
    assert sig["weakest_palace"]["palace"] in names
    # 最强分 >= 最弱分
    assert sig["strongest_palace"]["score"] >= sig["weakest_palace"]["score"]


def test_anchors_at_most_three_and_specific():
    sig = extract_signature(_chart())
    assert len(sig["anchors"]) <= 3
    assert len(sig["anchors"]) >= 1
    for a in sig["anchors"]:
        assert a["title"] and a["detail"]


def test_signature_deterministic():
    a = extract_signature(_chart())
    b = extract_signature(_chart())
    assert a == b


# ─────────────────────────────────────────────
# 报告生成 (LLM 注入 + 回退)
# ─────────────────────────────────────────────

def _caller(reply):
    seen = {}

    def _c(system, user):
        seen["system"] = system
        seen["user"] = user
        if isinstance(reply, Exception):
            raise reply
        return reply

    _c.seen = seen
    return _c


def test_report_llm_success():
    c = _caller({"content": "你的命宫太阴化忌——直说，你最大的成本是自我消耗。",
                 "provider": "deepseek", "model": "deepseek-chat"})
    res = generate_personal_report(_chart(), llm_caller=c)
    assert res["report_source"] == "llm"
    assert res["report"].startswith("你的命宫")
    assert res["llm"]["used"] is True
    assert res["llm"]["tone"] == "incisive_professional"
    # 诚实层 + 本地原文保留
    assert res["honesty"]["grounding"] == "chart_signature"
    assert res["local_report"]


def test_report_system_prompt_is_incisive_and_honest():
    c = _caller({"content": "x"})
    generate_personal_report(_chart(), llm_caller=c)
    sysp = c.seen["system"]
    assert "犀利" in sysp
    assert "绝不编造" in sysp
    assert "确定性" in sysp  # 高风险不下定论 / 非确定性预测


def test_report_injects_signature_and_facts():
    c = _caller({"content": "x"})
    generate_personal_report(_chart(), llm_caller=c)
    user = c.seen["user"]
    assert "专属特征" in user
    assert "命盘事实" in user
    assert "最强宫" in user
    assert "锚点" in user


def test_report_falls_back_local_on_empty():
    res = generate_personal_report(_chart(), llm_caller=_caller({"content": ""}))
    assert res["report_source"] == "local"
    assert res["llm"]["used"] is False
    # 本地犀利报告含专属结构
    assert "专属命盘解读" in res["report"]
    assert "隐性成本" in res["report"]


def test_report_falls_back_on_exception():
    res = generate_personal_report(_chart(), llm_caller=_caller(RuntimeError("boom")))
    assert res["report_source"] == "local"
    assert "llm_error" in res["llm"]["reason"]


def test_report_use_llm_false():
    def _boom(s, u):
        raise AssertionError("should not call")
    res = generate_personal_report(_chart(), use_llm=False, llm_caller=_boom)
    assert res["report_source"] == "local"
    assert res["llm"]["reason"] == "disabled"


# ─────────────────────────────────────────────
# API
# ─────────────────────────────────────────────

def test_api_report_local_fallback(monkeypatch):
    import ziwei.analysis.llm_prompt as lp
    monkeypatch.setattr(lp, "call_llm",
                        lambda *a, **k: {"error": "未设置API密钥", "content": ""})
    resp = client.get("/api/report", params={
        "year": 1995, "month": 8, "day": 16, "hour": 16, "minute": 30,
        "city": "上海", "use_llm": "true",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["report_source"] == "local"
    assert body["signature"]["anchors"]
    assert body["report"]
    assert body["honesty"]


def test_api_report_uses_llm(monkeypatch):
    import ziwei.analysis.llm_prompt as lp
    monkeypatch.setattr(lp, "call_llm",
                        lambda *a, **k: {"content": "犀利专属解读正文。",
                                          "provider": "deepseek", "model": "deepseek-chat"})
    resp = client.get("/api/report", params={
        "year": 1995, "month": 8, "day": 16, "hour": 16,
        "city": "上海", "use_llm": "true",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["report_source"] == "llm"
    assert body["report"] == "犀利专属解读正文。"
    assert body["llm"]["used"] is True
