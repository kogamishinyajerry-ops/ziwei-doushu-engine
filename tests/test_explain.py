"""
Tests for the 安星 "why" explanation layer.

Core guarantee: the rule each explanation STATES must reproduce the actual
placement on the chart (no drift between explain.py and stars.py).
"""

from pathlib import Path
import sys

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ziwei.api.server import app
from ziwei.chart.engine import generate_chart
from ziwei.chart.explain import (
    explain_chart, ZIWEI_SERIES_OFFSET, TIANFU_SERIES_OFFSET,
    LUCUN_BY_STEM, TIANMA_BY_BRANCH,
)
from ziwei.calendar.constants import EARTHLY_BRANCHES as Bc

client = TestClient(app)

GRID = [
    (1984, 1, 5, 0, "男"), (1990, 2, 14, 3, "女"), (1998, 3, 21, 8, "男"),
    (2003, 8, 8, 13, "男"), (2016, 12, 25, 22, "女"), (1962, 9, 9, 9, "男"),
]


def _pos(chart):
    return {s: Bc.index(p.branch) for p in chart.palaces for s in p.stars}


def test_explain_stated_rules_reproduce_actual_placement():
    for params in GRID:
        chart = generate_chart(*params[:4], 0, "T", params[4])
        pos = _pos(chart)
        zw, tf = pos["紫微"], pos["天府"]

        # 天府 寅申轴
        assert tf == (4 - zw) % 12
        # 紫微系逆布
        for star, off in ZIWEI_SERIES_OFFSET.items():
            assert pos[star] == (zw + off) % 12, f"{params} {star}"
        # 天府系顺布
        for star, off in TIANFU_SERIES_OFFSET.items():
            assert pos[star] == (tf + off) % 12, f"{params} {star}"
        # 禄存 (年干)
        year_stem = chart.year_pillar[0]
        assert pos["禄存"] == Bc.index(LUCUN_BY_STEM[year_stem])
        # 擎羊/陀罗 围禄存
        assert pos["擎羊"] == (pos["禄存"] + 1) % 12
        assert pos["陀罗"] == (pos["禄存"] - 1) % 12
        # 天马 (年支)
        year_branch = chart.year_pillar[1]
        assert pos["天马"] == Bc.index(TIANMA_BY_BRANCH[year_branch])
        # 地劫顺 / 地空逆 (自亥)
        h = Bc.index(chart.hour_pillar[1])
        assert pos["地劫"] == (Bc.index("亥") + h) % 12
        assert pos["地空"] == (Bc.index("亥") - h) % 12


def test_explain_chart_covers_main_stars_and_sihua():
    chart = generate_chart(1998, 3, 21, 8, 30, name="星辰", gender="男", city="北京")
    data = explain_chart(chart)

    explained = {e["star"] for e in data["stars"]}
    main14 = {
        "紫微", "天机", "太阳", "武曲", "天同", "廉贞",
        "天府", "太阴", "贪狼", "巨门", "天相", "天梁", "七杀", "破军",
    }
    assert main14 <= explained, f"缺主星: {main14 - explained}"
    # 每条解释字段完整
    for e in data["stars"]:
        assert e["rule"] and e["formula"] and e["derivation"] and e["source"]
        assert e["branch"] == Bc[e["branch_index"]]
    # 四化恰 4
    assert len(data["sihua"]) == 4
    assert {s["type"] for s in data["sihua"]} == {"化禄", "化权", "化科", "化忌"}


def test_explain_endpoint_returns_structured_payload():
    resp = client.get("/api/explain", params={
        "year": 1998, "month": 3, "day": 21, "hour": 8, "minute": 30,
        "name": "星辰", "gender": "男", "city": "北京",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "explain" in data and "stars" in data["explain"]
    assert data["explain"]["stars"]
    # 抽查天府解释含寅申轴规则
    tianfu = [e for e in data["explain"]["stars"] if e["star"] == "天府"]
    assert tianfu and "寅申" in tianfu[0]["rule"]
    assert "quality_flags" in data


def test_explain_endpoint_rejects_invalid_input():
    resp = client.get("/api/explain", params={
        "year": 1850, "month": 3, "day": 21, "hour": 8,
    })
    assert resp.status_code in (400, 422)
