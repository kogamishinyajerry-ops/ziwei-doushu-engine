"""
Golden tests for auxiliary (辅星) placement tables.

These lock canonical 年干/年支/时支 → 地支 tables that were independently
cross-checked (Codex gpt-5.5 web research, 2026-05-24). The 2026-05-24
optimization fixed a 地劫/地空 顺逆 swap and aligned 丁-year 天魁/天钺 to
the mainstream 斗数 table.
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ziwei.chart.stars import place_all_stars
from ziwei.calendar.constants import EARTHLY_BRANCHES, HEAVENLY_STEMS

B = EARTHLY_BRANCHES


def _stars(stem="甲", year_branch="子", hour="子"):
    layout = place_all_stars(
        wuxing_ju=2, lunar_day=15, year_stem=stem,
        year_branch=year_branch, month_branch="寅",
        hour_branch=hour, lunar_month=1,
    )
    return {k: B[v] for k, v in layout.stars.items()}


def test_lucun_by_year_stem():
    expected = {
        "甲": "寅", "乙": "卯", "丙": "巳", "丁": "午", "戊": "巳",
        "己": "午", "庚": "申", "辛": "酉", "壬": "亥", "癸": "子",
    }
    for stem, branch in expected.items():
        assert _stars(stem=stem)["禄存"] == branch, f"{stem} 禄存应在 {branch}"


def test_tianma_by_year_branch():
    # 四马: 申子辰→寅, 寅午戌→申, 巳酉丑→亥, 亥卯未→巳
    expected = {
        "申": "寅", "子": "寅", "辰": "寅",
        "寅": "申", "午": "申", "戌": "申",
        "巳": "亥", "酉": "亥", "丑": "亥",
        "亥": "巳", "卯": "巳", "未": "巳",
    }
    for yb, branch in expected.items():
        assert _stars(year_branch=yb)["天马"] == branch, f"{yb} 年天马应在 {branch}"


def test_dijie_advances_dikong_retreats_from_hai():
    # 地劫顺行 / 地空逆行, 皆自亥起子时
    hai = B.index("亥")
    for h_idx, hour in enumerate(EARTHLY_BRANCHES):
        s = _stars(hour=hour)
        assert s["地劫"] == B[(hai + h_idx) % 12], f"{hour}时 地劫顺行错"
        assert s["地空"] == B[(hai - h_idx) % 12], f"{hour}时 地空逆行错"
    # 锚点: 子时同宫于亥; 丑时 地劫子/地空戌
    z = _stars(hour="子")
    assert z["地劫"] == z["地空"] == "亥"
    c = _stars(hour="丑")
    assert c["地劫"] == "子" and c["地空"] == "戌"


def test_tiankui_tianyue_by_year_stem():
    # 主流斗数表 (丙丁同为 魁亥/钺酉; 甲戊庚牛羊; 辛逢马虎)
    kui = {
        "甲": "丑", "乙": "子", "丙": "亥", "丁": "亥", "戊": "丑",
        "己": "子", "庚": "丑", "辛": "午", "壬": "卯", "癸": "卯",
    }
    yue = {
        "甲": "未", "乙": "申", "丙": "酉", "丁": "酉", "戊": "未",
        "己": "申", "庚": "未", "辛": "寅", "壬": "巳", "癸": "巳",
    }
    for stem in HEAVENLY_STEMS:
        s = _stars(stem=stem)
        assert s["天魁"] == kui[stem], f"{stem} 天魁应在 {kui[stem]}"
        assert s["天钺"] == yue[stem], f"{stem} 天钺应在 {yue[stem]}"
        # 魁钺配对集合 (流派无关的硬约束)
        assert {s["天魁"], s["天钺"]} == {kui[stem], yue[stem]}
