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
from ziwei.chart.engine import generate_chart
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


def test_huoxing_lingxing_mainstream_zhongzhou():
    # 主流中州派/全书安火铃: 按年支三合局起子时位, 顺行至生时, 不分阳男阴女。
    # (Codex gpt-5.5 web 检索独立确认, 2026-05-24; 代码本就匹配, 无需改动。)
    start = {  # 年支 -> (火星子时起宫, 铃星子时起宫)
        "申": ("寅", "戌"), "子": ("寅", "戌"), "辰": ("寅", "戌"),
        "寅": ("丑", "卯"), "午": ("丑", "卯"), "戌": ("丑", "卯"),
        "巳": ("卯", "戌"), "酉": ("卯", "戌"), "丑": ("卯", "戌"),
        "亥": ("酉", "戌"), "卯": ("酉", "戌"), "未": ("酉", "戌"),
    }
    for yb, (huo0, ling0) in start.items():
        # 子时起宫
        z = _stars(year_branch=yb, hour="子")
        assert z["火星"] == huo0, f"{yb}年 火星子时起宫应 {huo0}"
        assert z["铃星"] == ling0, f"{yb}年 铃星子时起宫应 {ling0}"
        # 顺行: 丑时 = 起宫 + 1
        c = _stars(year_branch=yb, hour="丑")
        assert c["火星"] == B[(B.index(huo0) + 1) % 12], f"{yb}年 火星应顺行"
        assert c["铃星"] == B[(B.index(ling0) + 1) % 12], f"{yb}年 铃星应顺行"


def _engine_pos(year, variant="mainstream"):
    c = generate_chart(year, 6, 1, 0, 0, "T", "男", huoling_variant=variant)
    return {s: p.branch for p in c.palaces for s in p.stars}, c


def test_huoling_default_is_mainstream_no_regression():
    # 默认 (不传 variant) 必须等于显式 mainstream
    a = {s: p.branch for p in generate_chart(1989, 6, 1, 0, 0, "T", "男").palaces for s in p.stars}
    b, _ = _engine_pos(1989, "mainstream")
    assert a["火星"] == b["火星"] and a["铃星"] == b["铃星"]


def test_huoling_songban_swaps_only_siyouchou_group():
    # 1989 己巳 (巳酉丑组): songban 火星戌/铃星卯; mainstream 火星卯/铃星戌
    m, cm = _engine_pos(1989, "mainstream")
    s, cs = _engine_pos(1989, "songban")
    assert cm.year_pillar[1] in ("巳", "酉", "丑")
    assert (m["火星"], m["铃星"]) == ("卯", "戌")
    assert (s["火星"], s["铃星"]) == ("戌", "卯")
    # quality_flags.school 记录变体
    assert cs.quality_flags["school"]["huoling"] == "songban"


def test_huoling_songban_does_not_affect_other_groups():
    # 1992 壬申 (申子辰组, 非巳酉丑): variant 不应改变火铃
    m, _ = _engine_pos(1992, "mainstream")
    s, _ = _engine_pos(1992, "songban")
    assert m["火星"] == s["火星"] and m["铃星"] == s["铃星"]
