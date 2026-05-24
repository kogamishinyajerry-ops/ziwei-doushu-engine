"""
Tests for 宫干飞化 (flying transformations) — the flying-star chart data source.
"""

from pathlib import Path
import sys

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ziwei.api.server import app
from ziwei.chart.engine import generate_chart, chart_to_dict
from ziwei.chart.flying import compute_flying_sihua
from ziwei.chart.transformations import determine_sihua

client = TestClient(app)


def test_flying_sihua_has_four_edges_per_palace():
    chart = generate_chart(1998, 3, 21, 8, 30, name="星辰", gender="男", city="北京")
    edges = compute_flying_sihua(chart)["edges"]
    # 12 宫 × 4 化, 所有四化星都已安星 → 48 边
    assert len(edges) == 48
    from collections import Counter
    by_type = Counter(e["type"] for e in edges)
    assert by_type == {"化禄": 12, "化权": 12, "化科": 12, "化忌": 12}


def test_flying_edge_matches_stem_sihua_table_and_actual_location():
    chart = generate_chart(1998, 3, 21, 8, 30, name="星辰", gender="男", city="北京")
    # 盘面星 → 宫名
    star_palace = {s: p.name for p in chart.palaces for s in p.stars}
    edges = compute_flying_sihua(chart)["edges"]
    palace_by_name = {p.name: p for p in chart.palaces}

    for e in edges:
        src = palace_by_name[e["from_palace"]]
        table = determine_sihua(src.stem)  # {星: 化}
        # 飞化星属于本宫天干引动的四化, 类型一致
        assert table.get(e["star"]) == e["type"]
        # 落宫 = 该星实际所在宫
        assert star_palace[e["star"]] == e["to_palace"]
        # self 标志正确
        assert e["self"] == (e["from_index"] == e["to_index"])


def test_flying_sihua_in_chart_dict_and_api():
    d = chart_to_dict(generate_chart(1998, 3, 21, 8, 30, name="星辰", city="北京"))
    assert "flying_sihua" in d and d["flying_sihua"]["edges"]

    resp = client.get("/api/chart/full", params={
        "year": 1998, "month": 3, "day": 21, "hour": 8, "city": "北京",
    })
    assert resp.status_code == 200
    assert resp.json()["flying_sihua"]["edges"]
