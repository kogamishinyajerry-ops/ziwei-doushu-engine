"""
Tests for the verifiable chart fingerprint.

Guarantees: deterministic (re-run → same), sensitive to birth data and to
school variant when placements differ, and independent of display-only fields
(name). This is what makes the fingerprint a verifiable artifact.
"""

from pathlib import Path
import sys

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ziwei.api.server import app
from ziwei.chart.engine import generate_chart, chart_to_dict
from ziwei.chart.fingerprint import chart_fingerprint

client = TestClient(app)


def _fp(**kw):
    defaults = dict(year=1998, month=3, day=21, hour=8, minute=30,
                    name="星辰", gender="男", city="北京")
    defaults.update(kw)
    return chart_fingerprint(generate_chart(**defaults))["fingerprint"]


def test_fingerprint_is_deterministic():
    assert _fp() == _fp()


def test_fingerprint_format():
    fp = chart_fingerprint(generate_chart(1998, 3, 21, 8, 30, name="星辰"))
    assert fp["fingerprint"].startswith("ZW1-")
    assert len(fp["fingerprint"]) == len("ZW1-") + 12
    assert len(fp["sha256"]) == 64
    assert fp["version"] == "zw1"


def test_fingerprint_changes_with_birth_data():
    assert _fp(year=1998) != _fp(year=1999)
    assert _fp(hour=8) != _fp(hour=20)


def test_fingerprint_independent_of_display_name():
    # 姓名只是显示字段, 不影响排盘事实 → 指纹应相同
    assert _fp(name="甲") == _fp(name="乙丙丁")


def test_fingerprint_reflects_huoling_variant_when_placements_differ():
    # 1989 己巳 (巳酉丑组): songban 改变火铃落宫 → 指纹应不同
    m = chart_fingerprint(generate_chart(1989, 6, 1, 0, 0, "T", "男",
                                         huoling_variant="mainstream"))["fingerprint"]
    s = chart_fingerprint(generate_chart(1989, 6, 1, 0, 0, "T", "男",
                                         huoling_variant="songban"))["fingerprint"]
    assert m != s


def test_fingerprint_present_in_chart_dict_and_api():
    d = chart_to_dict(generate_chart(1998, 3, 21, 8, 30, name="星辰", city="北京"))
    assert d["fingerprint"]["fingerprint"].startswith("ZW1-")

    resp = client.get("/api/chart/full", params={
        "year": 1998, "month": 3, "day": 21, "hour": 8, "city": "北京",
    })
    assert resp.status_code == 200
    assert resp.json()["fingerprint"]["fingerprint"].startswith("ZW1-")
