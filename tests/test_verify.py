"""
Tests for 指纹校验 + 可分享二维码 (② verify + QR).

核心契约: 同一出生输入独立复算得同一指纹 (确定性); 比对正确; QR 离线生成。
"""

from pathlib import Path
import sys

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ziwei.api.server import app
from ziwei.chart.engine import generate_chart
from ziwei.chart.fingerprint import chart_fingerprint
from ziwei.chart.verify import verify_fingerprint, build_verify_url, make_verify_qr_svg

client = TestClient(app)

_BIRTH = dict(year=1995, month=8, day=16, hour=16, minute=30, city="上海")


# ─────────────────────────────────────────────
# 复算确定性 + 比对
# ─────────────────────────────────────────────

def test_recompute_matches_engine_fingerprint():
    chart = generate_chart(1995, 8, 16, 16, 30, name="林蕾", gender="女", city="上海")
    expected = chart_fingerprint(chart)["fingerprint"]
    res = verify_fingerprint(**_BIRTH, claimed_fingerprint=expected)
    assert res["computed"]["fingerprint"] == expected
    assert res["match"] is True


def test_name_and_gender_do_not_affect_fingerprint():
    # 指纹只认排盘事实, 不认姓名/性别
    a = generate_chart(1995, 8, 16, 16, 30, name="甲", gender="男", city="上海")
    b = generate_chart(1995, 8, 16, 16, 30, name="乙", gender="女", city="上海")
    assert chart_fingerprint(a)["fingerprint"] == chart_fingerprint(b)["fingerprint"]


def test_mismatch_detected():
    res = verify_fingerprint(**_BIRTH, claimed_fingerprint="ZW1-deadbeef0000")
    assert res["match"] is False


def test_full_sha256_accepted():
    chart = generate_chart(1995, 8, 16, 16, 30, city="上海")
    sha = chart_fingerprint(chart)["sha256"]
    res = verify_fingerprint(**_BIRTH, claimed_fingerprint=sha)
    assert res["match"] is True


def test_short_fp_case_insensitive():
    chart = generate_chart(1995, 8, 16, 16, 30, city="上海")
    short = chart_fingerprint(chart)["fingerprint"]
    res = verify_fingerprint(**_BIRTH, claimed_fingerprint=short.lower())
    assert res["match"] is True


def test_no_claim_returns_match_none():
    res = verify_fingerprint(**_BIRTH)
    assert res["match"] is None
    assert res["computed"]["fingerprint"].startswith("ZW1-")


def test_different_huoling_changes_or_keeps_consistently():
    # 同一流派复算稳定; 不同流派各自内部一致
    m1 = verify_fingerprint(**_BIRTH, huoling="mainstream")["computed"]["fingerprint"]
    m2 = verify_fingerprint(**_BIRTH, huoling="mainstream")["computed"]["fingerprint"]
    assert m1 == m2
    s1 = verify_fingerprint(**_BIRTH, huoling="songban")["computed"]["fingerprint"]
    s2 = verify_fingerprint(**_BIRTH, huoling="songban")["computed"]["fingerprint"]
    assert s1 == s2


# ─────────────────────────────────────────────
# 分享 URL + QR
# ─────────────────────────────────────────────

def test_build_verify_url_encodes_inputs_no_name():
    url = build_verify_url(1995, 8, 16, 16, 30, city="上海",
                           fingerprint="ZW1-abc", base_url="http://h:8088")
    assert url.startswith("http://h:8088/?")
    assert "verify=1" in url
    assert "year=1995" in url and "hour=16" in url
    assert "fp=ZW1-abc" in url
    assert "name" not in url and "gender" not in url


def test_qr_svg_is_offline_inline():
    svg = make_verify_qr_svg("http://h:8088/?verify=1&year=1995")
    assert svg.lstrip().startswith("<svg")
    assert "</svg>" in svg
    # 离线纯矢量: 不外链位图, 不引用外部样式/脚本 (xmlns 命名空间 URI 不算外部抓取)
    assert "<image" not in svg
    assert "xlink:href" not in svg
    assert "<script" not in svg and "<link" not in svg


# ─────────────────────────────────────────────
# API 端点
# ─────────────────────────────────────────────

def test_api_verify_match():
    chart = generate_chart(1995, 8, 16, 16, 30, city="上海")
    fp = chart_fingerprint(chart)["fingerprint"]
    resp = client.get("/api/verify", params={**_BIRTH, "fp": fp})
    assert resp.status_code == 200
    body = resp.json()
    assert body["match"] is True
    assert body["computed"]["fingerprint"] == fp


def test_api_verify_mismatch():
    resp = client.get("/api/verify", params={**_BIRTH, "fp": "ZW1-000000000000"})
    assert resp.status_code == 200
    assert resp.json()["match"] is False


def test_api_qr_returns_svg():
    resp = client.get("/api/fingerprint/qr", params={**_BIRTH, "fp": "ZW1-abc"})
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("image/svg+xml")
    assert resp.text.lstrip().startswith("<svg") or "<svg" in resp.text[:200]
    # 二维码内链接回写到响应头, 含校验参数
    assert "verify=1" in resp.headers.get("x-verify-url", "")
