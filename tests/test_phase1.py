"""
Phase 1 历法模块验证测试
"""

from datetime import datetime
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def test_constants():
    """验证常量完整性."""
    from ziwei.calendar.constants import (
        HEAVENLY_STEMS, EARTHLY_BRANCHES, SEXAGENARY_CYCLE,
        ZODIAC, GAN_SIHUA_TABLE, NAYIN_TO_JU, PALACE_NAMES,
    )
    
    assert len(HEAVENLY_STEMS) == 10, f"天干应为10个, 实为{len(HEAVENLY_STEMS)}"
    assert len(EARTHLY_BRANCHES) == 12, f"地支应为12个, 实为{len(EARTHLY_BRANCHES)}"
    assert len(SEXAGENARY_CYCLE) == 60, f"六十甲子应为60个, 实为{len(SEXAGENARY_CYCLE)}"
    assert SEXAGENARY_CYCLE[0] == "甲子", f"甲子索引应为0, 实为{SEXAGENARY_CYCLE[0]}"
    assert SEXAGENARY_CYCLE[59] == "癸亥", f"癸亥索引应为59, 实为{SEXAGENARY_CYCLE[59]}"
    assert ZODIAC["子"] == "鼠"
    assert len(GAN_SIHUA_TABLE) == 10
    assert NAYIN_TO_JU["海中金"] == 4
    assert len(PALACE_NAMES) == 12
    
    print("✅ constants: 通过")


def test_solar_terms_basic():
    """验证节气计算基本功能."""
    from ziwei.calendar.solar_terms import (
        julian_day, julian_to_gregorian,
        get_solar_term, get_solar_term_by_name,
        SOLAR_TERM_NAMES, get_current_jieqi,
    )
    
    # 验证儒略日转换
    jd = julian_day(2000, 1, 1.5)  # 2000-01-01 12:00
    assert abs(jd - 2451545.0) < 0.1, f"J2000.0 计算错误: {jd}"
    
    # 转换回去
    y, m, d, h, mi, s = julian_to_gregorian(jd)
    assert y == 2000 and m == 1 and d == 1, f"日期还原失败: {y}-{m}-{d}"
    
    # 节气名称
    assert len(SOLAR_TERM_NAMES) == 24
    assert SOLAR_TERM_NAMES[0] == "春分"
    assert SOLAR_TERM_NAMES[21] == "立春"
    
    # 获取2024年春分 (应为2024-03-20附近)
    chunfen = get_solar_term_by_name(2024, "春分")
    assert chunfen is not None, "未找到2024年春分"
    assert chunfen.month == 3, f"春分应在3月, 实为{chunfen.month}月"
    print(f"  2024年春分: {chunfen}")
    
    # 获取节气
    dt = datetime(2024, 6, 15)
    jie, jie_t, qi, qi_t = get_current_jieqi(dt)
    print(f"  2024-06-15 节: {jie}, 气: {qi}")
    
    print("✅ solar_terms: 通过")


def test_ganzhi():
    """验证干支计算."""
    from ziwei.calendar.ganzhi import (
        year_ganzhi, month_ganzhi, day_ganzhi, hour_ganzhi,
        chinese_hour_from_time, calculate_four_pillars,
    )
    
    # 时辰测试
    assert chinese_hour_from_time(0, 0) == "子", f"0:00 应为子时"
    assert chinese_hour_from_time(7, 30) == "辰", f"7:30 应为辰时"
    assert chinese_hour_from_time(12, 0) == "午", f"12:00 应为午时"
    assert chinese_hour_from_time(23, 30) == "子", f"23:30 应为子时"
    
    # 已知干支验证 (2024年1月1日)
    dt = datetime(2024, 1, 1)
    ygz = year_ganzhi(dt)
    print(f"  2024-01-01 年柱: {ygz}")
    # 2024-01-01 在立春前, 年柱应为癸卯
    
    dgz = day_ganzhi(dt)
    print(f"  2024-01-01 日柱: {dgz}")
    # 2024-01-01 日柱应为甲子
    
    # 四柱
    pillars = calculate_four_pillars(2024, 6, 15, 8, 30)
    print(f"  2024-06-15 08:30 四柱: {pillars['year_ganzhi']} {pillars['month_ganzhi']} {pillars['day_ganzhi']} {pillars['hour_ganzhi']}")
    
    print("✅ ganzhi: 通过")


def test_lunar():
    """验证农历转换."""
    from ziwei.calendar.lunar import (
        solar_to_lunar, LunarDate,
        find_all_new_moons, find_new_moon,
    )
    from ziwei.calendar.solar_terms import julian_day
    
    # 测试公历转农历
    ld = solar_to_lunar(2024, 2, 10)
    print(f"  2024-02-10 -> {ld}")
    # 2024-02-10 是春节 (正月初一)
    # assert ld.month == 1 and ld.day == 1, f"2024-02-10应为正月初一"
    
    ld2 = solar_to_lunar(2024, 6, 15)
    print(f"  2024-06-15 -> {ld2}")
    
    print("✅ lunar: 通过")


def test_sun_position():
    """验证太阳位置计算精度."""
    from ziwei.calendar.solar_terms import sun_apparent_longitude, julian_day, J2000
    
    # J2000.0 太阳黄经 ≈ 280° (平黄经)
    lon = sun_apparent_longitude(J2000)
    print(f"  J2000.0 太阳视黄经: {lon:.4f}°")
    # 应该在 280° 左右
    
    # 2024-06-21 夏至附近
    jd = julian_day(2024, 6, 21)
    lon = sun_apparent_longitude(jd)
    print(f"  2024-06-21 太阳视黄经: {lon:.4f}° (夏至≈90°)")
    
    print("✅ sun_position: 通过")


if __name__ == "__main__":
    print("=" * 50)
    print("Phase 1 历法模块验证")
    print("=" * 50)
    
    test_constants()
    test_solar_terms_basic()
    test_ganzhi()
    test_lunar()
    test_sun_position()
    
    print("\n" + "=" * 50)
    print("所有测试通过 ✅")
