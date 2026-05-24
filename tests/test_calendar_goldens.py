"""
Focused calendar golden tests for stable boundary behavior.

External date anchor:
https://www.hko.gov.hk/en/gts/time/calendar/pdf/files/2024e.pdf
"""

from datetime import datetime, timedelta
from pathlib import Path
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def test_golden_chunjie_2024_lunar_anchor_date():
    from ziwei.calendar.lunar import solar_to_lunar

    lunar_date = solar_to_lunar(2024, 2, 10)

    assert lunar_date.year == 2024
    assert lunar_date.month == 1
    assert lunar_date.day == 1
    assert lunar_date.is_leap is False
    assert lunar_date.month_name == "正月"
    assert lunar_date.year_ganzhi == "甲辰"


def test_golden_lichun_boundary_flips_year_ganzhi():
    from ziwei.calendar.ganzhi import year_ganzhi
    from ziwei.calendar.solar_terms import get_solar_term_by_name

    lichun = get_solar_term_by_name(2024, "立春")

    assert lichun is not None
    assert (lichun.month, lichun.day) == (2, 4)

    before = lichun - timedelta(minutes=1)
    after = lichun + timedelta(minutes=1)

    assert year_ganzhi(before) == "癸卯"
    assert year_ganzhi(after) == "甲辰"
    assert year_ganzhi(before) != year_ganzhi(after)


def test_golden_zi_hour_uses_next_day_pillar_after_23():
    from ziwei.calendar.ganzhi import (
        chinese_hour_from_time,
        day_ganzhi,
        hour_ganzhi,
    )

    date = datetime(2024, 1, 31)

    assert day_ganzhi(date, 23) == day_ganzhi(datetime(2024, 2, 1), 0)
    assert day_ganzhi(date, 23) != day_ganzhi(date, 22)
    assert chinese_hour_from_time(23, 0) == "子"
    assert hour_ganzhi(date, 23, 0).endswith("子")


def test_golden_true_solar_time_crosses_hour_for_western_city():
    from ziwei.calendar.solar_time import get_chinese_hour_with_correction

    result = get_chinese_hour_with_correction(2024, 6, 1, 23, 0, "乌鲁木齐")

    assert result["clock_time"] == "23:00"
    assert result["chinese_hour_before"] == "子"
    assert result["true_solar_time"] == "20:52"
    assert result["offset_minutes"] == pytest.approx(-127.3, abs=0.1)
    assert result["corrected_hour"] == 20
    assert result["corrected_minute"] == 52
    assert result["chinese_hour_after"] == "戌"
    assert result["hour_changed"] is True
    assert result["chinese_hour_after"] != result["chinese_hour_before"]


def test_unknown_city_keeps_clock_hour_without_correction():
    from ziwei.calendar.solar_time import get_chinese_hour_with_correction

    result = get_chinese_hour_with_correction(2024, 6, 1, 23, 0, "不存在城市")

    assert result["province"] == "未知"
    assert result["offset_minutes"] == 0.0
    assert result["corrected_hour"] == 23
    assert result["corrected_minute"] == 0
    assert result["chinese_hour_before"] == result["chinese_hour_after"]
    assert result["hour_changed"] is False
