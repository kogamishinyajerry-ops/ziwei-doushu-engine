"""
Tests for the honest-advisor layer (AI 顾问不是神谕).

Guarantees: high-stakes questions (health/marriage/finance/legal) get an
explicit non-determinism disclaimer and capped confidence; every answer
carries a grounding marker and a limits note.
"""

from pathlib import Path
import sys

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ziwei.api.server import app
from ziwei.chart.engine import generate_chart, chart_to_dict
from ziwei.analysis.advisor import answer_question

client = TestClient(app)


def _chart():
    return chart_to_dict(
        generate_chart(1998, 3, 21, 8, 30, name="星辰", gender="男", city="北京"),
        include_analysis=True,
    )


def test_high_stakes_question_gets_disclaimer_and_capped_confidence():
    cd = _chart()
    for q in ("我适合投资股票吗", "我该不该和他结婚", "我会得什么病吗"):
        r = answer_question(q, cd)
        assert r["honesty"]["high_stakes"] is True, q
        assert r["honesty"].get("disclaimer"), q
        # 高风险议题禁止 "high" 确定性断言
        assert r["confidence"] != "high", q


def test_normal_question_not_flagged_high_stakes():
    cd = _chart()
    r = answer_question("我的事业运怎么样", cd)
    assert r["honesty"]["high_stakes"] is False
    assert r["confidence"] in ("high", "medium")


def test_every_answer_carries_grounding_and_limits():
    cd = _chart()
    r = answer_question("我的性格特点", cd)
    assert r["grounding"] in ("chart_grounded", "chart_present", "general_knowledge", "needs_chart")
    assert r["honesty"]["limits"]
    assert r["honesty"]["basis"]


def test_general_knowledge_grounding_without_chart():
    r = answer_question("紫微星代表什么", None)
    assert r["grounding"] == "general_knowledge"
    assert r["honesty"]["high_stakes"] is False


def test_api_ask_surfaces_honesty_layer():
    resp = client.post("/api/ask", json={
        "question": "我适合投资股票吗",
        "year": 1998, "month": 3, "day": 21, "hour": 8, "minute": 30,
        "name": "星辰", "gender": "男", "city": "北京",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["honesty"]["high_stakes"] is True
    assert data["honesty"]["disclaimer"]
    assert data["grounding"]
    assert data["confidence"] != "high"
