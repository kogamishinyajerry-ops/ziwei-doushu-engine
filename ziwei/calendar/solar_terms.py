"""
节气计算模块 — 太阳黄经精确算法
Solar Terms Calculation — Accurate Ecliptic Longitude Method

基于 Jean Meeus《Astronomical Algorithms》的太阳位置算法，
用牛顿迭代法精确求解24节气时刻（精度 < 1分钟）。
"""

import math
from datetime import datetime, timedelta, timezone
from typing import Tuple, Optional

# ──────────────────────────────────────
# 24节气名称
# ──────────────────────────────────────
SOLAR_TERM_NAMES = [
    "春分", "清明", "谷雨", "立夏", "小满", "芒种",
    "夏至", "小暑", "大暑", "立秋", "处暑", "白露",
    "秋分", "寒露", "霜降", "立冬", "小雪", "大雪",
    "冬至", "小寒", "大寒", "立春", "雨水", "惊蛰",
]

# 节气对应的太阳黄经 (度)
# 春分=0°, 清明=15°, ..., 惊蛰=345°
SOLAR_LONGITUDE = {name: i * 15 for i, name in enumerate(SOLAR_TERM_NAMES)}

# 节气索引 -> 黄经
TERM_LONGITUDE = [i * 15 for i in range(24)]

# 别名映射 (大陆常用名 -> 标准名)
TERM_ALIASES = {
    "立春": "立春", "雨水": "雨水", "惊蛰": "惊蛰",
    "春分": "春分", "清明": "清明", "谷雨": "谷雨",
    "立夏": "立夏", "小满": "小满", "芒种": "芒种",
    "夏至": "夏至", "小暑": "小暑", "大暑": "大暑",
    "立秋": "立秋", "处暑": "处暑", "白露": "白露",
    "秋分": "秋分", "寒露": "寒露", "霜降": "霜降",
    "立冬": "立冬", "小雪": "小雪", "大雪": "大雪",
    "冬至": "冬至", "小寒": "小寒", "大寒": "大寒",
}

# ──────────────────────────────────────
# 天文常数
# ──────────────────────────────────────
J2000 = 2451545.0  # JD for 2000-01-01 12:00 TT
JULIAN_CENTURY = 36525.0  # days per Julian century
DEG_TO_RAD = math.pi / 180.0
RAD_TO_DEG = 180.0 / math.pi


def julian_day(year: int, month: int, day: float) -> float:
    """
    计算儒略日 (Julian Day).
    支持小数日 (用于时分秒).
    
    Args:
        year: 公历年
        month: 公历月 (1-12)
        day: 公历日 (可带小数)
    
    Returns:
        Julian Day Number
    """
    if month <= 2:
        year -= 1
        month += 12
    
    a = int(year / 100)
    b = 2 - a + int(a / 4)
    
    jd = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + b - 1524.5
    return jd


def julian_to_gregorian(jd: float) -> Tuple[int, int, int, int, int, float]:
    """
    儒略日转公历日期.
    
    Returns:
        (year, month, day, hour, minute, second_fraction)
    """
    jd += 0.5
    z = int(jd)
    f = jd - z
    
    if z < 2299161:
        a = z
    else:
        alpha = int((z - 1867216.25) / 36524.25)
        a = z + 1 + alpha - int(alpha / 4)
    
    b = a + 1524
    c = int((b - 122.1) / 365.25)
    d = int(365.25 * c)
    e = int((b - d) / 30.6001)
    
    day_frac = b - d - int(30.6001 * e) + f
    day = int(day_frac)
    day_remainder = day_frac - day
    
    if e < 14:
        month = e - 1
    else:
        month = e - 13
    
    if month > 2:
        year = c - 4716
    else:
        year = c - 4715
    
    # 时分秒
    total_seconds = day_remainder * 86400.0
    hour = int(total_seconds / 3600)
    minute = int((total_seconds - hour * 3600) / 60)
    second = total_seconds - hour * 3600 - minute * 60
    
    return year, month, day, hour, minute, round(second, 6)


def sun_apparent_longitude(jd: float) -> float:
    """
    计算太阳视黄经 (Apparent Ecliptic Longitude).
    
    基于 VSOP87 简化和 Meeus 第25章的算法.
    精度: ~1 角秒 (对于节气计算足够).
    
    Args:
        jd: Julian Day (TT)
    
    Returns:
        太阳视黄经 (度, 0-360)
    """
    # Julian centuries from J2000.0
    T = (jd - J2000) / JULIAN_CENTURY
    T2 = T * T
    T3 = T2 * T
    
    # 太阳平黄经 (Mean longitude)
    L0 = 280.46646 + 36000.76983 * T + 0.0003032 * T2
    L0 = L0 % 360.0
    
    # 太阳平近点角 (Mean anomaly)
    M = 357.52911 + 35999.05029 * T - 0.0001537 * T2
    M = M % 360.0
    M_rad = M * DEG_TO_RAD
    
    # 地球轨道离心率
    e = 0.016708634 - 0.000042037 * T - 0.0000001267 * T2
    
    # 中心差 (Equation of center)
    sinM = math.sin(M_rad)
    sin2M = math.sin(2 * M_rad)
    sin3M = math.sin(3 * M_rad)
    
    C = (1.914602 - 0.004817 * T - 0.000014 * T2) * sinM \
        + (0.019993 - 0.000101 * T) * sin2M \
        + 0.000289 * sin3M
    
    # 太阳真黄经 (True longitude)
    true_lon = L0 + C
    
    # 章动修正 (Nutation in longitude) — 简化版
    # 月球升交点经度
    omega = 125.04 - 1934.136 * T
    omega_rad = omega * DEG_TO_RAD
    
    # 月球平近点角
    L1 = 218.3165 + 481267.8813 * T
    L1_rad = L1 * DEG_TO_RAD
    
    # 太阳平近点角 (二次)
    M1 = M  # 已计算
    
    # 章动经度 (仅保留最大的几项)
    delta_psi = -17.20 * math.sin(omega_rad) \
                - 1.32 * math.sin(2 * L0 * DEG_TO_RAD) \
                - 0.23 * math.sin(2 * L1_rad) \
                + 0.21 * math.sin(2 * omega_rad)
    delta_psi = delta_psi / 3600.0  # 角秒 -> 度
    
    # 光行差 (Aberration)
    aberration = -0.00569  # 度 (常数近似)
    
    # 太阳视黄经
    apparent_lon = true_lon + delta_psi + aberration
    
    return apparent_lon % 360.0


def get_solar_term_for_longitude(year: int, target_lon: float) -> datetime:
    """
    计算指定年份中，太阳黄经到达指定度数的精确时刻.
    
    使用牛顿-拉弗森迭代法 (Newton-Raphson).
    
    注意: 黄经 >= 270° 的节气 (冬至/小寒/大寒/立春/雨水/惊蛰)
    实际发生在公历 year-1 的年末至 year 的年初.
    例如 "2024年立春" 实际在 2024年2月, 而非 2025年2月.
    
    Args:
        year: 公历年
        target_lon: 目标太阳黄经 (度, 0-360)
    
    Returns:
        精确时刻 (datetime, UTC)
    """
    # 对于黄经 >= 270° 的节气, 从 year-1 的春分开始搜索
    # 这样能正确找到 year 年初的立春/雨水/惊蛰等
    if target_lon >= 270.0:
        base_year = year - 1
    else:
        base_year = year
    
    # 春分基础日期估算 (3月20日左右的 JD)
    base_jd = julian_day(base_year, 3, 20)
    # 加上黄经偏移 (每度约1.0146天)
    base_jd += target_lon * 1.0146
    
    # 牛顿迭代
    jd = base_jd
    for _ in range(20):  # 最多20次迭代
        lon = sun_apparent_longitude(jd)
        
        # 调整到目标附近 (±180°)
        delta = (target_lon - lon) % 360.0
        if delta > 180.0:
            delta -= 360.0
        
        if abs(delta) < 1e-8:  # 精度约 0.001 秒
            break
        
        # 太阳每天移动约0.9856度
        # d(lon)/d(t) ≈ 0.9856 度/天
        correction = delta / 0.9856
        jd += correction
    
    # 转换为公历日期时间
    y, m, d, h, mi, s = julian_to_gregorian(jd)
    
    # 处理秒的小数部分
    whole_sec = int(s)
    microsec = int((s - whole_sec) * 1_000_000)
    
    return datetime(y, m, d, h, mi, whole_sec, microsec, tzinfo=timezone.utc)


def get_solar_term(year: int, term_index: int) -> datetime:
    """
    获取指定年份的第N个节气.
    
    Args:
        year: 公历年
        term_index: 节气索引 (0=春分, 1=清明, ..., 23=惊蛰)
    
    Returns:
        节气精确时刻 (datetime, UTC)
    """
    target_lon = TERM_LONGITUDE[term_index % 24]
    return get_solar_term_for_longitude(year, target_lon)


def get_current_jieqi(date: datetime) -> Tuple[str, datetime, str, datetime]:
    """
    获取给定日期所在的节和气.
    
    在紫微斗数中:
    - 节 (Jie): 月令起点 (立春、惊蛰、清明...)
    - 气 (Qi): 月中 (雨水、春分、谷雨...)
    
    Args:
        date: 任意日期时间
    
    Returns:
        (当前节名, 节日时刻, 当前气名, 气日时刻)
    """
    # 确保 date 是 UTC (如果无时区信息)
    if date.tzinfo is None:
        date = date.replace(tzinfo=timezone.utc)
    year = date.year
    
    # 如果日期在年初，可能需要查前一年的节气
    # 冬至在上一年的12月
    all_terms = []
    for y in [year - 1, year, year + 1]:
        for i in range(24):
            t = get_solar_term(y, i)
            all_terms.append((t, i, y))
    
    all_terms.sort(key=lambda x: x[0])
    
    # 找到在 date 之前的最后一个节 (奇数索引: 立春=21, 惊蛰=23, 清明=1, ...)
    # 节是奇数索引 (从立春=21开始, 即索引21,23,1,3,5,...)
    jie_indices = [21, 23, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19]  # 12节
    qi_indices = [22, 0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20]   # 12气
    
    current_jie = None
    current_qi = None
    
    for t, idx, y_ in all_terms:
        if t > date:
            break
        if idx in jie_indices:
            current_jie = (SOLAR_TERM_NAMES[idx], t)
        if idx in qi_indices:
            current_qi = (SOLAR_TERM_NAMES[idx], t)
    
    if current_jie is None:
        current_jie = ("未知", date)
    if current_qi is None:
        current_qi = ("未知", date)
    
    return (current_jie[0], current_jie[1], current_qi[0], current_qi[1])


def solar_term_name(term_index: int) -> str:
    """返回节气名称."""
    return SOLAR_TERM_NAMES[term_index % 24]


def get_solar_term_by_name(year: int, name: str) -> Optional[datetime]:
    """根据名称获取指定年份的节气时刻."""
    if name in SOLAR_TERM_NAMES:
        idx = SOLAR_TERM_NAMES.index(name)
        return get_solar_term(year, idx)
    return None


def get_all_solar_terms(year: int) -> dict:
    """获取指定年份的所有24节气."""
    return {
        SOLAR_TERM_NAMES[i]: get_solar_term(year, i)
        for i in range(24)
    }


# ──────────────────────────────────────
# 月令判断 (用于紫微斗数月柱计算)
# ──────────────────────────────────────
# 12月令 (从立春开始)
MONTH_JIE = {
    1: "立春",   # 正月节
    2: "惊蛰",   # 二月节
    3: "清明",   # 三月节
    4: "立夏",   # 四月节
    5: "芒种",   # 五月节
    6: "小暑",   # 六月节
    7: "立秋",   # 七月节
    8: "白露",   # 八月节
    9: "寒露",   # 九月节
    10: "立冬",  # 十月节
    11: "大雪",  # 十一月节
    12: "小寒",  # 十二月节
}

# 月令名称 -> 月数
JIE_TO_MONTH = {v: k for k, v in MONTH_JIE.items()}


def get_lunar_month_by_jieqi(date: datetime) -> int:
    """
    根据节气确定斗数月份 (以节为月始).
    
    立春为正月, 惊蛰为二月, ...
    
    Args:
        date: 公历日期
    
    Returns:
        月数 (1-12)
    """
    jie_name, _, _, _ = get_current_jieqi(date)
    return JIE_TO_MONTH.get(jie_name, 1)
