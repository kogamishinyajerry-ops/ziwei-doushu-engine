"""
API smoke tests for the current public Zi Wei Dou Shu routes.
"""

from pathlib import Path
import sys

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ziwei.api.server import app


client = TestClient(app)


def birth_params(**overrides):
    params = {
        "year": 1998,
        "month": 3,
        "day": 21,
        "hour": 8,
        "minute": 30,
        "name": "星辰",
        "gender": "男",
        "city": "北京",
    }
    params.update(overrides)
    return params


def test_health():
    resp = client.get("/api/health")

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["version"] == app.version


def test_local_cors_origin_allowed():
    resp = client.options(
        "/api/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert resp.status_code == 200
    assert resp.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_chart_full():
    resp = client.get("/api/chart/full", params=birth_params())

    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "星辰"
    assert data["birth_date"] == "1998-03-21"
    assert set(data["four_pillars"]) == {"year", "month", "day", "hour"}
    assert len(data["palaces"]) == 12
    assert "analysis" in data
    assert "quality_flags" in data


def test_bazi():
    resp = client.get(
        "/api/bazi",
        params=birth_params(target_year=2026, count=2),
    )

    assert resp.status_code == 200
    data = resp.json()
    assert {"bazi", "liunian", "chart_summary"} <= data.keys()
    assert data["bazi"]["day_master"]
    assert isinstance(data["liunian"], list)
    assert len(data["liunian"]) == 2
    assert data["chart_summary"]["name"] == "星辰"


def test_hepan():
    payload = {
        "name1": "甲",
        "year1": 1998,
        "month1": 3,
        "day1": 21,
        "hour1": 8,
        "minute1": 30,
        "gender1": "男",
        "city1": "北京",
        "name2": "乙",
        "year2": 1999,
        "month2": 5,
        "day2": 1,
        "hour2": 20,
        "minute2": 0,
        "gender2": "女",
        "city2": "上海",
    }

    resp = client.post("/api/hepan", json=payload)

    assert resp.status_code == 200
    data = resp.json()
    assert data["person1"]["name"] == "甲"
    assert data["person2"]["name"] == "乙"
    assert isinstance(data["dimensions"], list)
    assert len(data["dimensions"]) > 0
    assert {"name", "score", "label", "good", "bad", "detail"} <= data["dimensions"][0].keys()
    assert data["total_score"] >= 0
    assert "verdict" in data


def test_ask():
    resp = client.post(
        "/api/ask",
        json={
            "question": "我适合做什么事业？",
            **birth_params(),
        },
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["question"] == "我适合做什么事业？"
    assert data["answer"]
    assert data["category"]
    assert data["needs_chart"] is False
    assert isinstance(data["used_knowledge"], list)
    assert "chart" in data


def test_ask_emits_rule_based_source_quality_flag():
    resp = client.post(
        "/api/ask",
        json={
            "question": "我适合做什么事业？",
            **birth_params(city="不存在城市"),
        },
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["source"] == "advisor_rules"
    assert data["quality_flags"]["analysis"]["status"] == "rule_based"
    assert data["quality_flags"]["analysis"]["fallback"] is False
    assert data["quality_flags"]["analysis"]["source"] == "advisor_rules"
    assert data["quality_flags"]["solar_time"]["status"] == "unknown_city"


def test_ask_without_required_chart_emits_local_fallback_quality_flag():
    resp = client.post(
        "/api/ask",
        json={"question": "我适合做什么事业？"},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["needs_chart"] is True
    assert data["source"] == "local_fallback"
    assert data["quality_flags"]["analysis"]["status"] == "local_fallback"
    assert data["quality_flags"]["analysis"]["fallback"] is True
    assert data["quality_flags"]["analysis"]["source"] == "advisor_rules"
    assert data["quality_flags"]["analysis"]["reason"] == "chart_required"


def test_reading_local_fallback_emits_llm_quality_flag(monkeypatch):
    for key in (
        "MINIMAX_API_KEY",
        "DEEPSEEK_API_KEY",
        "OPENAI_API_KEY",
    ):
        monkeypatch.delenv(key, raising=False)

    resp = client.get("/api/reading", params=birth_params(mode="full"))

    assert resp.status_code == 200
    data = resp.json()
    assert "local_reading" in data["reading"]
    assert data["source"] == "local"
    assert data["reading"]["source"] == "local"
    assert data["reading"]["source_detail"] == "local_rules"
    assert data["quality_flags"]["analysis"]["status"] == "rule_based"
    assert data["quality_flags"]["analysis"]["source"] == "local_rules"
    assert data["quality_flags"]["llm"]["status"] == "local_fallback"
    assert data["quality_flags"]["llm"]["fallback"] is True
    assert data["quality_flags"]["llm"]["source"] == "local"
    assert "quality_flags" in data["chart"]


def test_reading_openai_auto_provider_fake_llm(monkeypatch):
    from ziwei.analysis import llm_prompt

    for key in ("MINIMAX_API_KEY", "DEEPSEEK_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "openai-test-key")

    seen = {}

    def fake_call_llm(prompt, api_key=None, model=None, base_url=None, **kwargs):
        seen["provider"] = kwargs.get("provider")
        seen["api_key"] = api_key
        return {
            "content": "fake openai reading",
            "model": "gpt-4o",
            "provider": kwargs.get("provider"),
            "usage": {"prompt_tokens": 1, "completion_tokens": 2},
        }

    monkeypatch.setattr(llm_prompt, "call_llm", fake_call_llm)

    resp = client.get("/api/reading", params=birth_params(mode="full"))

    assert resp.status_code == 200
    data = resp.json()
    assert data["reading"]["llm_reading"] == "fake openai reading"
    assert data["source"] == "llm"
    assert data["reading"]["source"] == "llm"
    assert data["reading"]["source_detail"] == "openai"
    assert data["reading"]["llm_provider"] == "openai"
    assert data["quality_flags"]["llm"]["status"] == "llm_ok"
    assert data["quality_flags"]["llm"]["source"] == "openai"
    assert seen == {"provider": "openai", "api_key": None}


def test_reading_explicit_provider_overrides_auto_priority(monkeypatch):
    from ziwei.analysis import llm_prompt

    monkeypatch.setenv("MINIMAX_API_KEY", "minimax-test-key")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "deepseek-test-key")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    seen = {}

    def fake_call_llm(prompt, api_key=None, model=None, base_url=None, **kwargs):
        seen["provider"] = kwargs.get("provider")
        return {
            "content": "fake deepseek reading",
            "model": "deepseek-chat",
            "provider": kwargs.get("provider"),
            "usage": {},
        }

    monkeypatch.setattr(llm_prompt, "call_llm", fake_call_llm)

    resp = client.get(
        "/api/reading",
        params=birth_params(mode="full", provider="deepseek"),
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["reading"]["llm_provider"] == "deepseek"
    assert data["quality_flags"]["llm"]["source"] == "deepseek"
    assert seen == {"provider": "deepseek"}


def test_invalid_chart_input_returns_validation_error():
    resp = client.get("/api/chart/full", params=birth_params(year=1899))

    assert resp.status_code == 422
    data = resp.json()
    assert "detail" in data
