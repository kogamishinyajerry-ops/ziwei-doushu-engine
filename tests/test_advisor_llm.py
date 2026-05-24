"""
Tests for the honest-LLM advisor layer (① 真实 LLM 接入, 带诚实系统提示).

全部用注入/monkeypatch 的 caller, 不触网络。验证:
- 诚实系统提示包含关键约束
- 命盘事实作为「唯一可用依据」注入 user prompt, 不编造
- LLM 成功 → 替换答案但保留诚实层 metadata
- 无 key / 出错 / 空响应 / use_llm=False → 回退本地规则引擎 (离线可用)
- 高风险护栏在 LLM 路径下依然生效
"""

from pathlib import Path
import sys

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ziwei.api.server import app
from ziwei.chart.engine import generate_chart, chart_to_dict
from ziwei.analysis import advisor

client = TestClient(app)


def _chart():
    return chart_to_dict(
        generate_chart(1995, 8, 16, 16, 30, name="林蕾", gender="女", city="上海"),
        include_analysis=True,
    )


def _capturing_caller(reply):
    """返回一个记录 system/user 的假 caller。reply 为 dict 或抛出的异常实例。"""
    seen = {}

    def _call(system, user):
        seen["system"] = system
        seen["user"] = user
        if isinstance(reply, Exception):
            raise reply
        return reply

    _call.seen = seen
    return _call


# ─────────────────────────────────────────────
# 成功路径
# ─────────────────────────────────────────────

def test_llm_success_replaces_answer_and_keeps_honesty():
    chart = _chart()
    caller = _capturing_caller({"content": "你的命宫太阳坐守，倾向开朗（仅供参考）。",
                                "provider": "deepseek", "model": "deepseek-chat"})
    res = advisor.advise("我的性格如何？", chart, llm_caller=caller)

    assert res["answer_source"] == "llm"
    assert res["answer"].startswith("你的命宫太阳")
    assert res["llm"]["used"] is True
    assert res["llm"]["provider"] == "deepseek"
    assert res["llm"]["system_honesty"] is True
    # 诚实层 metadata 必须保留 (规则引擎产出)
    assert "honesty" in res and res["honesty"]["grounding"]
    assert "grounding" in res
    # 规则引擎原文保留供核验
    assert res["local_answer"] and res["local_answer"] != res["answer"]


def test_honest_system_prompt_contains_iron_rules():
    chart = _chart()
    caller = _capturing_caller({"content": "x"})
    advisor.advise("我适合什么工作？", chart, llm_caller=caller)
    sys_prompt = caller.seen["system"]
    assert "不是神谕" in sys_prompt
    assert "绝不编造" in sys_prompt
    assert "不确定" in sys_prompt
    # 高风险护栏写进系统提示
    assert "专业人士" in sys_prompt or "医生/律师" in sys_prompt


def test_chart_facts_injected_as_sole_basis():
    chart = _chart()
    caller = _capturing_caller({"content": "x"})
    advisor.advise("我的事业？", chart, llm_caller=caller)
    user = caller.seen["user"]
    assert "唯一可用依据" in user
    assert "命宫" in user and "十二宫" in user
    # 规则引擎初判一并提供
    assert "规则引擎" in user


# ─────────────────────────────────────────────
# 回退路径 (离线可用, 无回归)
# ─────────────────────────────────────────────

def test_fallback_on_empty_content():
    chart = _chart()
    res = advisor.advise("性格", chart, llm_caller=_capturing_caller({"content": ""}))
    assert res["answer_source"] == "local"
    assert res["llm"]["used"] is False


def test_fallback_on_error_dict():
    chart = _chart()
    res = advisor.advise("性格", chart,
                         llm_caller=_capturing_caller({"error": "未设置API密钥", "content": ""}))
    assert res["answer_source"] == "local"
    assert res["llm"]["used"] is False
    assert "API" in (res["llm"]["reason"] or "")


def test_fallback_on_caller_exception():
    chart = _chart()
    res = advisor.advise("性格", chart,
                         llm_caller=_capturing_caller(RuntimeError("boom")))
    assert res["answer_source"] == "local"
    assert res["llm"]["used"] is False
    assert "llm_error" in res["llm"]["reason"]


def test_use_llm_false_never_calls():
    chart = _chart()
    def _boom(system, user):
        raise AssertionError("should not be called")
    res = advisor.advise("性格", chart, use_llm=False, llm_caller=_boom)
    assert res["answer_source"] == "local"
    assert res["llm"]["reason"] == "disabled"


def test_needs_chart_skips_llm():
    def _boom(system, user):
        raise AssertionError("should not be called when chart missing")
    res = advisor.advise("我的财运如何？", None, llm_caller=_boom)
    assert res["needs_chart"] is True
    assert res["answer_source"] == "local"
    assert res["llm"]["reason"] == "needs_chart"


# ─────────────────────────────────────────────
# 高风险护栏在 LLM 路径下仍生效
# ─────────────────────────────────────────────

def test_high_stakes_guardrail_preserved_under_llm():
    chart = _chart()
    caller = _capturing_caller({"content": "命理视角的参考。"})
    res = advisor.advise("我会得癌症吗？", chart, llm_caller=caller)
    assert res["answer_source"] == "llm"
    assert res["honesty"]["high_stakes"] is True
    assert "disclaimer" in res["honesty"]
    # 高风险封顶 confidence
    assert res["confidence"] != "high"


# ─────────────────────────────────────────────
# API 端点: 无 key 时自动回退, 离线可用 (默认行为不回归)
# ─────────────────────────────────────────────

def test_api_ask_falls_back_without_key(monkeypatch):
    # 强制 call_llm 报「无 key」, 模拟离线/未配置
    import ziwei.analysis.llm_prompt as lp
    monkeypatch.setattr(lp, "call_llm",
                        lambda *a, **k: {"error": "未设置API密钥", "content": ""})
    resp = client.get("/api/ask", params={
        "q": "我的性格如何？", "year": 1995, "month": 8, "day": 16, "hour": 16,
        "city": "上海", "use_llm": "true",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["answer_source"] == "local"
    assert body["llm"]["used"] is False
    assert body["answer"]  # 仍有本地答案


def test_api_ask_uses_llm_when_available(monkeypatch):
    import ziwei.analysis.llm_prompt as lp
    monkeypatch.setattr(lp, "call_llm",
                        lambda *a, **k: {"content": "LLM润色后的诚实回答。",
                                          "provider": "deepseek", "model": "deepseek-chat"})
    resp = client.get("/api/ask", params={
        "q": "我适合什么工作？", "year": 1995, "month": 8, "day": 16, "hour": 16,
        "city": "上海", "use_llm": "true",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["answer_source"] == "llm"
    assert body["answer"] == "LLM润色后的诚实回答。"
    assert body["llm"]["used"] is True
    assert body["honesty"]  # 诚实层保留
    assert body["local_answer"]  # 规则引擎原文保留
