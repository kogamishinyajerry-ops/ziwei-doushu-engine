"""
Focused tests for the chart orchestration layer.
"""

from pathlib import Path
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ziwei.chart.engine import chart_to_dict, generate_chart


def _body_palace(chart):
    matches = [palace for palace in chart.palaces if palace.is_body]
    assert len(matches) == 1
    return matches[0]


@pytest.mark.parametrize(
    ("year", "month", "day", "hour", "minute"),
    [
        (1998, 3, 21, 8, 30),
        (2024, 2, 4, 10, 0),
    ],
)
def test_shen_palace_uses_body_palace_stem(year, month, day, hour, minute):
    chart = generate_chart(year, month, day, hour, minute, name="测试", gender="男", city="北京")
    body = _body_palace(chart)

    assert body.name != "命宫"
    assert chart.shen_palace == f"{body.stem}{body.branch}"
    assert chart_to_dict(chart)["shen_palace"] == chart.shen_palace


def test_shen_palace_handles_body_in_ming_palace():
    chart = generate_chart(2024, 2, 10, 0, 0, name="测试", gender="男")
    body = _body_palace(chart)

    assert body.name == "命宫"
    assert chart.shen_palace == chart.ming_palace
    assert chart.shen_palace == f"{body.stem}{body.branch}"


def test_unknown_city_emits_solar_time_quality_flag():
    chart = generate_chart(
        1998,
        3,
        21,
        8,
        30,
        name="测试",
        gender="男",
        city="不存在城市",
    )

    data = chart_to_dict(chart)

    assert data["quality_flags"]["solar_time"]["status"] == "unknown_city"
    assert data["quality_flags"]["solar_time"]["fallback"] is True
    assert data["quality_flags"]["solar_time"]["city"] == "不存在城市"
    assert data["solar_correction"]["province"] == "未知"


def test_lunar_conversion_fallback_emits_quality_flag(monkeypatch):
    from ziwei.chart import engine as chart_engine

    def raise_lunar_error(year, month, day):
        raise RuntimeError("forced lunar failure")

    monkeypatch.setattr(chart_engine, "solar_to_lunar", raise_lunar_error)

    chart = chart_engine.generate_chart(
        1998,
        3,
        21,
        8,
        30,
        name="测试",
        gender="男",
    )
    data = chart_engine.chart_to_dict(chart)

    assert data["quality_flags"]["lunar"]["status"] == "fallback"
    assert data["quality_flags"]["lunar"]["fallback"] is True
    assert "forced lunar failure" in data["quality_flags"]["lunar"]["reason"]
    assert data["lunar_date"].startswith("农历")


def test_analysis_modules_flag_full_on_healthy_chart():
    chart = generate_chart(1998, 3, 21, 8, 30, name="星辰", gender="男", city="北京")
    data = chart_to_dict(chart, include_analysis=True)

    am = data["quality_flags"]["analysis_modules"]
    assert am["status"] == "full"
    assert am["fallback"] is False
    assert am["degraded"] == []
    assert "analysis" in data


def test_analysis_modules_flag_marks_partial_on_submodule_failure(monkeypatch):
    from ziwei.analysis import archetype as archetype_mod

    def boom(*args, **kwargs):
        raise RuntimeError("forced archetype failure")

    monkeypatch.setattr(archetype_mod, "compute_archetype", boom)

    chart = generate_chart(1998, 3, 21, 8, 30, name="星辰", gender="男", city="北京")
    data = chart_to_dict(chart, include_analysis=True)

    am = data["quality_flags"]["analysis_modules"]
    assert am["status"] == "partial"
    assert am["fallback"] is True
    assert "archetype_rarity" in am["degraded"]
    assert "forced archetype failure" in am["errors"]["archetype_rarity"]
    # 单个子模块失败不应拖垮整体分析输出
    assert "analysis" in data
