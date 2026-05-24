from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_frontend(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_desktop_surfaces_quality_flags_contract():
    html = read_frontend("desktop/index.html")

    assert "function renderQualityFlags(flags)" in html
    assert "quality_flags" in html
    assert "renderQualityFlags(data.quality_flags)" in html
    assert "renderQualityFlags(data.quality_flags || (data.chart" in html
    assert "quality-flags" in html

    for key in ("solar_time", "lunar", "llm"):
        assert key in html

    for status in ("unknown_city", "fallback", "local_fallback", "llm_ok"):
        assert status in html


def test_legacy_frontend_surfaces_chart_quality_flags_safely():
    html = read_frontend("frontend/index.html")

    assert "function renderQualityFlags(flags)" in html
    assert "quality_flags" in html
    assert "renderQualityFlags(cd.quality_flags)" in html
    assert "if(!flags" in html or "if (!flags" in html
    assert "quality-flags" in html

    for key in ("solar_time", "lunar"):
        assert key in html


def test_reading_endpoint_is_documented_as_deferred_from_frontend():
    desktop = read_frontend("desktop/index.html")
    legacy = read_frontend("frontend/index.html")
    readme = read_frontend("README.md")
    slices = read_frontend(".planning/NEXT_SPARK_SLICES_2026-05-24.md")

    assert "/api/reading" not in desktop
    assert "/api/reading" not in legacy
    assert "reading_frontend_strategy" in readme
    assert "defer_frontend_connection" in readme
    assert "defer_frontend_connection" in slices
