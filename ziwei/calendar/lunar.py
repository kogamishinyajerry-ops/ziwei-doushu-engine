"""
农历转换模块 — 公历 ↔ 农历 (基于 ephem 天文计算)
Lunar Calendar Conversion — Solar ↔ Lunar

使用 ephem 库进行高精度天文计算:
- 朔日 (新月) 通过 ephem 的 next_new_moon/previous_new_moon 精确获取
- 结合已有节气计算模块确定月序和闰月
- 遵循紫金山天文台农历编算规则:
  1. 冬至必须在冬月 (十一月)
  2. 不含中气的月份为闰月 (闰前月)
  3. 从冬月固定为十一月, 反推正月位置
"""

import ephem
from datetime import datetime, timezone, timedelta
from typing import Tuple, Optional, NamedTuple, List

from .solar_terms import (
    julian_day, julian_to_gregorian,
    get_solar_term_for_longitude,
)
from .constants import (
    HEAVENLY_STEMS, EARTHLY_BRANCHES, SEXAGENARY_CYCLE,
    LUNAR_MONTH_NAMES,
)


class LunarDate(NamedTuple):
    """农历日期."""
    year: int
    month: int        # 1-12
    day: int           # 1-30
    is_leap: bool
    year_ganzhi: str
    month_name: str

    def __repr__(self):
        leap_str = "闰" if self.is_leap else ""
        return f"农历{self.year}年{leap_str}{LUNAR_MONTH_NAMES[self.month-1]}第{self.day}日"


# ──────────────────────────────────────
# 朔日 (新月) 计算
# ──────────────────────────────────────

def _find_new_moons_between(start_jd: float, end_jd: float) -> List[float]:
    """使用 ephem 计算两个儒略日之间的所有朔日时刻 (标准 JD)."""
    new_moons = []
    
    # ephem 内部使用 Dublin JD (epoch: 1899-12-31 12:00 UT = JD 2415020.0)
    DUBLIN_OFFSET = 2415020.0
    
    t = ephem.Date(start_jd - DUBLIN_OFFSET)
    end = ephem.Date(end_jd - DUBLIN_OFFSET)
    
    # 从 start 之前的第一个朔日开始
    nm = ephem.previous_new_moon(t)
    
    while True:
        nm_jd = float(nm) + DUBLIN_OFFSET
        if nm_jd > end_jd:
            break
        if nm_jd >= start_jd - 1:  # 容忍1天边界
            new_moons.append(nm_jd)
        nm = ephem.next_new_moon(nm)
    
    return new_moons


def _find_winter_solstice_jd(year: int) -> float:
    """获取指定年份12月的冬至精确时刻 (JD).
    
    注: get_solar_term_for_longitude 对 target_lon >= 270 使用 year-1 为基年,
    所以传 year+1 来获取 year 年12月的冬至.
    """
    ws = get_solar_term_for_longitude(year + 1, 270.0)
    return julian_day(ws.year, ws.month, ws.day + ws.hour / 24.0 + ws.minute / 1440.0)


def _find_major_solar_terms(start_jd: float, end_jd: float) -> List[Tuple[float, float]]:
    """获取两个儒略日之间的所有中气 (太阳黄经为 30° 倍数)."""
    zhong_qi_lons = [30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330, 0]
    
    start_y, _, _ = julian_to_gregorian(start_jd)[:3]
    end_y, _, _ = julian_to_gregorian(end_jd)[:3]
    
    results = []
    for y in range(start_y - 1, end_y + 2):
        for lon in zhong_qi_lons:
            try:
                zq = get_solar_term_for_longitude(y, lon)
                zq_jd = julian_day(zq.year, zq.month, zq.day + zq.hour / 24.0 + zq.minute / 1440.0)
                if start_jd <= zq_jd <= end_jd:
                    results.append((zq_jd, lon))
            except Exception:
                pass
    
    results.sort()
    return results


# ──────────────────────────────────────
# 农历年构建 — 核心算法
# ──────────────────────────────────────

class _LunarMonth:
    __slots__ = ('month_num', 'is_leap', 'days', 'start_jd', 'has_zhong_qi')
    def __init__(self, month_num, is_leap, days, start_jd, has_zhong_qi):
        self.month_num = month_num
        self.is_leap = is_leap
        self.days = days
        self.start_jd = start_jd
        self.has_zhong_qi = has_zhong_qi


def _build_lunar_year_months(lunar_year: int) -> List[_LunarMonth]:
    """
    构建指定农历年的所有月份 (12或13个).
    
    算法:
    1. 找到去年和今年的冬至
    2. 朔日覆盖范围: 从去年冬至前两个月到今年冬至后两个月
    3. 定位冬月: 包含今年冬至的朔日 ≡ 冬月初一
    4. 从冬月向前回溯: 尝试从 -12, -11 个朔日开始, 选择使正月最合理的那个
    5. 检查中气, 标记不含中气的月份 → 闰前月
    6. 确保冬至在冬月 (月份11)
    """
    # 1. 冬至
    ws_prev_jd = _find_winter_solstice_jd(lunar_year - 1)
    ws_curr_jd = _find_winter_solstice_jd(lunar_year)
    ws_next_jd = _find_winter_solstice_jd(lunar_year + 1)
    
    # 2. 收集所有朔日 (覆盖约28个月)
    start_jd = ws_prev_jd - 65
    end_jd = ws_next_jd + 65
    new_moons = _find_new_moons_between(start_jd, end_jd)
    
    if len(new_moons) < 24:
        raise ValueError(f"朔日数量不足: {len(new_moons)}")
    
    # 3. 找到冬月 (包含今年冬至的第一个朔日)
    #    即: 今年冬至之前的最后一个朔日
    winter_nm_idx = None
    for i in range(len(new_moons) - 1):
        if new_moons[i] <= ws_curr_jd < new_moons[i + 1]:
            winter_nm_idx = i
            break
    
    if winter_nm_idx is None:
        winter_nm_idx = min(range(len(new_moons)),
                           key=lambda i: abs(new_moons[i] - ws_curr_jd))
    
    # 4. 判断是否有闰月: 数两个冬至之间的朔日数量
    #    如果 ws_prev_jd 到 ws_curr_jd 之间有12个朔日 → 平年 (无闰, offset=10)
    #    如果有13个朔日 → 闰年 (offset=11)
    
    moons_between_winters = [
        nm for nm in new_moons 
        if ws_prev_jd < nm < ws_curr_jd
    ]
    
    is_leap_year = len(moons_between_winters) == 13
    offset = 11 if is_leap_year else 10
    
    first_idx = winter_nm_idx - offset
    if first_idx < 0:
        # 朔日范围不够, 强制调整
        first_idx = max(0, winter_nm_idx - 10)
        offset = winter_nm_idx - first_idx
    
    # 收集所有中气用于闰月判断
    all_zhong_qi = _find_major_solar_terms(start_jd, end_jd)
    
    # 5. 构建月份 (12或13个月)
    total_months = 13 if is_leap_year else 12
    raw_months = []  # list of (start_jd, days, has_zq)
    
    for mi in range(total_months):
        idx = first_idx + mi
        if idx >= len(new_moons) - 1:
            break
        start = new_moons[idx]
        end = new_moons[idx + 1]
        days = round(end - start)
        days = max(29, min(30, days))
        has_zq = any(start <= zq_jd < end for zq_jd, _ in all_zhong_qi)
        raw_months.append((start, days, has_zq))
    
    if len(raw_months) < 12:
        raise ValueError(f"月份不足: {len(raw_months)}")
    
    # 6. 找出闰月 (不含中气的月份, 且不是第一个月)
    #    闰月闰前一个月
    leap_idx = -1
    if is_leap_year and len(raw_months) >= 13:
        for i in range(1, len(raw_months)):
            if not raw_months[i][2]:  # 不含中气
                leap_idx = i
                break
    
    # 7. 组装最终月份列表, 标注月号
    result = []
    month_counter = 1
    
    for i, (start, days, has_zq) in enumerate(raw_months):
        if i == leap_idx:
            # 闰月: 月号与前一个月相同
            prev_month_num = month_counter - 1
            result.append(_LunarMonth(
                month_num=prev_month_num, is_leap=True,
                days=days, start_jd=start, has_zhong_qi=False
            ))
        else:
            result.append(_LunarMonth(
                month_num=month_counter, is_leap=False,
                days=days, start_jd=start, has_zhong_qi=has_zq
            ))
            month_counter += 1
    
    return result


# ──────────────────────────────────────
# 月份缓存
# ──────────────────────────────────────

_MONTHS_CACHE = {}

def _get_lunar_months_for_year(lunar_year: int) -> List[_LunarMonth]:
    """获取指定农历年的月份 (带缓存)."""
    if lunar_year not in _MONTHS_CACHE:
        _MONTHS_CACHE[lunar_year] = _build_lunar_year_months(lunar_year)
    return _MONTHS_CACHE[lunar_year]


# ──────────────────────────────────────
# 公历 ↔ 农历 转换
# ──────────────────────────────────────

def solar_to_lunar(year: int, month: int, day: int) -> LunarDate:
    """
    公历转农历.
    
    使用 ephem 进行高精度天文计算, 覆盖 1900-2100 年.
    日期按中国标准时间 (UTC+8) 计算.
    """
    jd = julian_day(year, month, day)
    
    # 辅助: JD → 北京时间日期
    def _china_date(_jd):
        from .solar_terms import julian_to_gregorian as j2g
        y, m, d, _, _, _ = j2g(_jd + 8.0 / 24.0)
        return (y, m, d)
    
    target_cn = _china_date(jd)
    
    # 候选农历年 (公历年初可能还属于上一个农历年)
    for lunar_year in [year, year - 1, year + 1]:
        try:
            months = _get_lunar_months_for_year(lunar_year)
        except Exception:
            continue
        
        if not months:
            continue
        
        first_start = months[0].start_jd
        last_month = months[-1]
        last_end = last_month.start_jd + last_month.days
        
        if first_start <= jd < last_end:
            for i, m in enumerate(months):
                m_end = m.start_jd + m.days
                if m.start_jd <= jd < m_end:
                    start_cn = _china_date(m.start_jd)
                    
                    from datetime import date as _date
                    d0 = _date(*start_cn)
                    d1 = _date(*target_cn)
                    lunar_day = (d1 - d0).days + 1
                    
                    # 边界修正: 如果这是年末最后一个月且目标日期在
                    # 北京时间等于下一年正月初一, 则属于下一年
                    if i == len(months) - 1 and lunar_year < 2100:
                        try:
                            next_months = _get_lunar_months_for_year(lunar_year + 1)
                            if next_months:
                                next_start_cn = _china_date(next_months[0].start_jd)
                                if target_cn == next_start_cn:
                                    # 属于下一年
                                    return LunarDate(
                                        year=lunar_year + 1,
                                        month=1, day=1, is_leap=False,
                                        year_ganzhi=SEXAGENARY_CYCLE[((lunar_year + 1) - 4) % 60],
                                        month_name=LUNAR_MONTH_NAMES[0],
                                    )
                        except Exception:
                            pass
                    
                    return LunarDate(
                        year=lunar_year,
                        month=m.month_num,
                        day=lunar_day,
                        is_leap=m.is_leap,
                        year_ganzhi=SEXAGENARY_CYCLE[(lunar_year - 4) % 60],
                        month_name=f"{'闰' if m.is_leap else ''}{LUNAR_MONTH_NAMES[m.month_num - 1]}",
                    )
    
    # 极端情况下的降级估算
    ly = year if month >= 2 else year - 1
    return LunarDate(
        year=ly, month=max(1, min(12, month - 1)), day=day,
        is_leap=False,
        year_ganzhi=SEXAGENARY_CYCLE[(ly - 4) % 60],
        month_name=LUNAR_MONTH_NAMES[max(0, min(11, month - 2))],
    )


def lunar_to_solar(lunar_year: int, lunar_month: int, lunar_day: int,
                   is_leap: bool = False) -> datetime:
    """农历转公历."""
    months = _get_lunar_months_for_year(lunar_year)
    
    for m in months:
        if m.month_num == lunar_month and m.is_leap == is_leap:
            target_jd = m.start_jd + lunar_day - 1
            y, mo, d, h, mi, s = julian_to_gregorian(target_jd)
            whole_sec = int(s)
            microsec = int((s - whole_sec) * 1_000_000)
            return datetime(y, mo, d, h, mi, whole_sec, microsec, tzinfo=timezone.utc)
    
    raise ValueError(f"未找到农历日期: {lunar_year}年{lunar_month}月{lunar_day}日")


def find_all_new_moons(year: int) -> list:
    """获取指定年份前后的朔日 (用于调试)."""
    start_jd = julian_day(year, 1, 1) - 60
    end_jd = julian_day(year + 1, 1, 1) + 60
    moons = _find_new_moons_between(start_jd, end_jd)
    result = []
    for jd in moons:
        y, m, d, h, mi, s = julian_to_gregorian(jd)
        result.append({"jd": jd, "year": y, "month": m, "day": d, "hour": h, "minute": mi})
    return result


def find_new_moon(jd_approx: float) -> float:
    """兼容旧接口: 找到最接近的朔日."""
    DUBLIN_OFFSET = 2415020.0
    t = ephem.Date(jd_approx - DUBLIN_OFFSET)
    prev = ephem.previous_new_moon(t)
    next_nm = ephem.next_new_moon(t)
    prev_jd = float(prev) + DUBLIN_OFFSET
    next_jd = float(next_nm) + DUBLIN_OFFSET
    return prev_jd if abs(prev_jd - jd_approx) < abs(next_jd - jd_approx) else next_jd
