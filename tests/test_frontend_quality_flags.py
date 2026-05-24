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


def test_desktop_surfaces_analysis_modules_degradation():
    html = read_frontend("desktop/index.html")

    assert "addAnalysisModulesFlag" in html
    assert "analysis_modules" in html
    assert "部分降级" in html
    # 仅在 partial 状态提示, 完整时不展示
    assert "'partial'" in html or '"partial"' in html


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


def test_desktop_has_star_why_transparency_layer():
    html = read_frontend("desktop/index.html")
    # 可点击星曜 + "为什么"浮层 + 拉取 /api/explain
    assert "showStarWhy" in html
    assert "star-chip" in html
    assert "/api/explain" in html
    assert "_explainMap" in html


def test_desktop_has_trust_page_and_huoling_selector():
    html = read_frontend("desktop/index.html")
    # 算法可信度页 (差异化信任资产)
    assert 'data-page="trust"' in html
    assert 'id="page-trust"' in html
    assert "算法可信度" in html
    assert "寅申" in html  # 结构铁律展示
    # 流派切换器前端
    assert 'id="p-huoling"' in html
    assert "songban" in html and "mainstream" in html


def test_desktop_shows_verifiable_fingerprint():
    html = read_frontend("desktop/index.html")
    assert "fingerprint" in html
    assert "pc-fp" in html
    assert "可验证指纹" in html


def test_desktop_renders_honest_advisor_layer():
    html = read_frontend("desktop/index.html")
    assert "buildHonestyHtml" in html
    assert "msg-warn" in html
    assert "honesty" in html
    assert "高风险" in html or "顾问不是神谕" in html


def test_desktop_has_llm_toggle_and_source_badge():
    html = read_frontend("desktop/index.html")
    # 真实 LLM 开关 + use_llm 入参
    assert 'id="a-use-llm"' in html
    assert "use_llm" in html
    # 答案来源徽标 (真实AI润色 / 规则引擎)
    assert "answer_source" in html
    assert "真实AI润色" in html
    assert "规则引擎" in html


def test_desktop_wheel_draws_flying_sihua_lines():
    html = read_frontend("desktop/index.html")
    assert "flying_sihua" in html
    # 禄/权/科/忌 四类线切换器
    assert "setFlyingType" in html
    assert "SIHUA_COLORS" in html
    for t in ("化禄", "化权", "化科", "化忌"):
        assert t in html
    # 切换控件 + 默认高亮化忌
    assert 'data-fly="化忌"' in html
    assert "fly-toggle" in html
