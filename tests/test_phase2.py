"""
Phase 2 安星排盘引擎验证测试
"""

from datetime import datetime
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from ziwei.calendar.ganzhi import calculate_four_pillars, chinese_hour_from_time
from ziwei.calendar.constants import EARTHLY_BRANCHES, PALACE_NAMES


def test_palace_layout():
    """测试十二宫排布."""
    from ziwei.chart.palaces import place_palaces, place_stems_branches, determine_wuxing_ju
    
    # 测试用例: 正月子时生人
    layout = place_palaces(lunar_month=1, hour_branch="子")
    assert layout.ming_index is not None
    assert layout.shen_index is not None
    assert len(layout.palaces) == 12
    
    # 正月子时应为命宫在寅
    assert layout.ming_index == 2, f"正月子时命宫应在寅(2), 实为{layout.ming_index} ({EARTHLY_BRANCHES[layout.ming_index]})"
    
    # 身宫: 正月子时 = 寅+0+0 = 寅 (index 2)
    assert layout.shen_index == 2, f"正月子时身宫应在寅(2), 实为{layout.shen_index}"
    
    print(f"  正月子时: 命宫={EARTHLY_BRANCHES[layout.ming_index]}, 身宫={EARTHLY_BRANCHES[layout.shen_index]}")
    
    # 测试: 五月辰时
    layout2 = place_palaces(lunar_month=5, hour_branch="辰")
    # 命宫: (2 + 5 - 1 - 5 + 1) % 12 = 2 → 寅
    # Actually: hour_count=5 (辰=index 4 + 1 = 5)
    # ming_idx = (2 + 4 - 4) % 12 = 2 → 寅
    
    # 六月午时
    layout3 = place_palaces(lunar_month=6, hour_branch="午")
    # 午=index 6, hour_count=7
    # ming_idx = (2 + 5 - 6) % 12 = 1 → 丑
    print(f"  六月午时: 命宫={EARTHLY_BRANCHES[layout3.ming_index]}")
    
    print("✅ place_palaces: 通过")


def test_stems_and_wuxing_ju():
    """测试天干地支和五行局."""
    from ziwei.chart.palaces import place_palaces, place_stems_branches, determine_wuxing_ju
    
    # 甲年生人, 正月子时
    layout = place_palaces(1, "子")
    layout = place_stems_branches(layout, "甲")
    
    assert layout.stems["命宫"] is not None
    # 甲年寅宫天干 = 丙, 命宫在寅 → 命宫天干 = 丙
    assert layout.stems["命宫"] == "丙", f"甲年寅宫命宫天干应为丙, 实为{layout.stems['命宫']}"
    print(f"  甲年正月子时: 命宫干支={layout.ming_stem}{layout.ming_branch}")
    
    # 五行局
    layout = determine_wuxing_ju(layout)
    assert layout.wuxing_ju > 0
    print(f"  五行局: {layout.wuxing_ju_name} ({layout.ming_nayin})")
    
    print("✅ stems & wuxing_ju: 通过")


def test_ziwei_placement():
    """测试紫微星安放."""
    from ziwei.chart.stars import place_ziwei, _compute_ziwei_position
    
    # 水二局, 生日=1 → 紫微应在寅
    pos = _compute_ziwei_position(2, 1)
    assert EARTHLY_BRANCHES[pos] == "寅", f"水二局生日1紫微应在寅, 实为{EARTHLY_BRANCHES[pos]}"
    
    # 水二局, 生日=2 → 紫微在寅
    pos = _compute_ziwei_position(2, 2)
    assert EARTHLY_BRANCHES[pos] == "寅", f"水二局生日2紫微应在寅, 实为{EARTHLY_BRANCHES[pos]}"
    
    # 水二局, 生日=3 → 紫微在卯
    pos = _compute_ziwei_position(2, 3)
    assert EARTHLY_BRANCHES[pos] == "卯", f"水二局生日3紫微应在卯, 实为{EARTHLY_BRANCHES[pos]}"
    
    # 水二局, 生日=29 → 紫微位置
    pos = _compute_ziwei_position(2, 29)
    # ceil(29/2) = 15, 寅+14 = (2+14)%12 = 4 → 辰
    assert EARTHLY_BRANCHES[pos] == "辰", f"水二局生日29紫微应在辰, 实为{EARTHLY_BRANCHES[pos]}"
    
    # 火六局, 生日=15
    pos = _compute_ziwei_position(6, 15)
    # ceil(15/6) = 3, 寅+2 = 4 → 辰
    assert EARTHLY_BRANCHES[pos] == "辰", f"火六局生日15紫微应在辰, 实为{EARTHLY_BRANCHES[pos]}"
    
    # 木三局, 生日=10
    pos = _compute_ziwei_position(3, 10)
    # ceil(10/3) = 4, 寅+3 = 5 → 巳
    assert EARTHLY_BRANCHES[pos] == "巳", f"木三局生日10紫微应在巳, 实为{EARTHLY_BRANCHES[pos]}"
    
    print("✅ ziwei_placement: 通过")


def test_all_stars():
    """测试完整安星."""
    from ziwei.chart.stars import place_all_stars
    from ziwei.chart.transformations import determine_sihua, get_sihua_stars
    
    # 甲辰年生人, 五月, 午时
    # 四柱: 甲辰 庚午 甲子 庚午 (示意)
    stars = place_all_stars(
        wuxing_ju=4,      # 金四局
        lunar_day=15,
        year_stem="甲",
        year_branch="辰",
        month_branch="午",
        hour_branch="午",
        lunar_month=5,
    )
    
    assert "紫微" in stars.stars
    assert "天府" in stars.stars
    assert "天机" in stars.stars
    assert "太阳" in stars.stars
    assert "武曲" in stars.stars
    assert "天同" in stars.stars
    assert "廉贞" in stars.stars
    assert "太阴" in stars.stars
    assert "贪狼" in stars.stars
    assert "巨门" in stars.stars
    assert "天相" in stars.stars
    assert "天梁" in stars.stars
    assert "七杀" in stars.stars
    assert "破军" in stars.stars
    assert "左辅" in stars.stars
    assert "右弼" in stars.stars
    assert "文昌" in stars.stars
    assert "文曲" in stars.stars
    assert "禄存" in stars.stars
    assert "擎羊" in stars.stars
    assert "陀罗" in stars.stars
    assert "火星" in stars.stars
    assert "铃星" in stars.stars
    assert "天马" in stars.stars
    
    print(f"  紫微在{EARTHLY_BRANCHES[stars.ziwei_index]}, 天府在{EARTHLY_BRANCHES[stars.tianfu_index]}")
    print(f"  星曜数: {len(stars.stars)}")
    
    # 四化
    sihua = determine_sihua("甲")
    assert sihua == {"廉贞": "化禄", "破军": "化权", "武曲": "化科", "太阳": "化忌"}
    print(f"  甲年四化: {get_sihua_stars('甲')}")
    
    print("✅ all_stars: 通过")


def test_four_pillars_integration():
    """测试四柱到排盘的整合."""
    from ziwei.chart.palaces import place_palaces, place_stems_branches, determine_wuxing_ju
    from ziwei.chart.stars import place_all_stars
    
    # 测试一个真实案例: 2024年6月15日 8:30 (甲辰年 庚午月 庚戌日 庚辰时)
    # 农历: 五月初九
    pillars = calculate_four_pillars(2024, 6, 15, 8, 30)
    
    print(f"  四柱: {pillars['year_ganzhi']} {pillars['month_ganzhi']} {pillars['day_ganzhi']} {pillars['hour_ganzhi']}")
    print(f"  时辰: {pillars['chinese_hour']}")
    print(f"  生肖: {pillars['zodiac']}")
    
    # 用农历月5, 日9 (近似)
    lunar_month = 5
    lunar_day = 9
    hour_branch = pillars['hour_branch']
    
    # 排盘
    layout = place_palaces(lunar_month, hour_branch)
    layout = place_stems_branches(layout, pillars['year_stem'])
    layout = determine_wuxing_ju(layout)
    
    print(f"  命宫: {layout.ming_stem}{layout.ming_branch}")
    print(f"  五行局: {layout.wuxing_ju_name}")
    print(f"  纳音: {layout.ming_nayin}")
    
    # 安星
    stars = place_all_stars(
        wuxing_ju=layout.wuxing_ju,
        lunar_day=lunar_day,
        year_stem=pillars['year_stem'],
        year_branch=pillars['year_branch'],
        month_branch=pillars['month_branch'],
        hour_branch=hour_branch,
        lunar_month=lunar_month,
    )
    
    print(f"  紫微在{EARTHLY_BRANCHES[stars.ziwei_index]}")
    print(f"  天府在{EARTHLY_BRANCHES[stars.tianfu_index]}")
    
    # 打印各宫星曜
    for name in PALACE_NAMES:
        palace_idx = layout.palaces[name]
        branch = EARTHLY_BRANCHES[palace_idx]
        stem = layout.stems.get(name, "?")
        stars_here = [s for s, idx in stars.stars.items() if idx == palace_idx]
        if stars_here:
            print(f"    {name}({stem}{branch}): {', '.join(stars_here)}")
    
    print("✅ integration: 通过")


if __name__ == "__main__":
    print("=" * 50)
    print("Phase 2 安星排盘引擎验证")
    print("=" * 50)
    
    test_palace_layout()
    test_stems_and_wuxing_ju()
    test_ziwei_placement()
    test_all_stars()
    test_four_pillars_integration()
    
    print("\n" + "=" * 50)
    print("所有测试通过 ✅")
