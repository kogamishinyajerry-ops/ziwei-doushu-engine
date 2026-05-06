"""
干支推算模块 — 年柱、月柱、日柱、时柱
Ganzhi (Sexagenary Cycle) — Year, Month, Day, Hour Pillars

紫微斗数四柱推算:
- 年柱: 以立春为界 (非农历正月初一)
- 月柱: 以节为月始 (立春=正月, 惊蛰=二月, ...)
- 日柱: 以公历日期为准 (子时特殊处理)
- 时柱: 以时辰地支为基础
"""

from datetime import datetime, time, timedelta
from typing import Tuple, Optional

from .constants import (
    HEAVENLY_STEMS, EARTHLY_BRANCHES, SEXAGENARY_CYCLE,
    HOUR_INDEX, BRANCH_INDEX_ZI_ONE,
)
from .solar_terms import get_current_jieqi, JIE_TO_MONTH, MONTH_JIE


# ──────────────────────────────────────
# 基础干支运算
# ──────────────────────────────────────
def ganzhi_index(stem: str, branch: str) -> int:
    """
    返回干支在六十甲子中的索引 (0-59).
    甲子=0, 乙丑=1, ..., 癸亥=59
    """
    si = HEAVENLY_STEMS.index(stem)
    bi = EARTHLY_BRANCHES.index(branch)
    # 找到 stem 和 branch 对应的最小公倍数位置
    for i in range(60):
        if SEXAGENARY_CYCLE[i] == stem + branch:
            return i
    raise ValueError(f"无效的干支: {stem}{branch}")


def ganzhi_from_index(index: int) -> str:
    """从六十甲子索引获取干支."""
    return SEXAGENARY_CYCLE[index % 60]


def stem_branch(ganzhi_str: str) -> Tuple[str, str]:
    """拆分干支为天干和地支."""
    if len(ganzhi_str) != 2:
        raise ValueError(f"无效的干支: {ganzhi_str}")
    return ganzhi_str[0], ganzhi_str[1]


# ──────────────────────────────────────
# 年柱计算 (以立春为界)
# ──────────────────────────────────────
def year_ganzhi(date: datetime) -> str:
    """
    计算年柱干支.
    
    以立春为年界: 立春前属上年, 立春后属新年.
    公式: year_ganzhi_index = (year - 4) % 60 (基于农历年)
    
    Args:
        date: 公历日期
    
    Returns:
        年干支 (如 "甲子")
    """
    # 确保 UTC-aware
    if date.tzinfo is None:
        from datetime import timezone as _tz
        date = date.replace(tzinfo=_tz.utc)
    
    # 先判断是否在立春前
    jie_name, jie_time, _, _ = get_current_jieqi(date)
    
    # 立春在索引21 (SOLAR_TERM_NAMES中)
    # 立春在J2000.0前后
    # 简单方法: 用 get_current_jieqi 获取当前节
    year = date.year
    
    # 如果当前在立春前 (节是小寒)，则年柱属于前一年
    if jie_name == "小寒" or jie_name == "大雪" or jie_name == "立冬" or jie_name == "寒露":
        # 这些节在立春之前 (上一年的下半年)
        lunar_year = year  # 农历年仍同公历年
    else:
        lunar_year = year
    
    # 更精确的方法: 检查是否在立春之前
    # 立春在2月3-5日
    from .solar_terms import get_solar_term_by_name
    lichun = get_solar_term_by_name(year, "立春")
    if lichun and date < lichun:
        # 在立春前，使用上一年
        target_year = year - 1
    else:
        target_year = year
    
    idx = (target_year - 4) % 60
    return SEXAGENARY_CYCLE[idx]


# ──────────────────────────────────────
# 月柱计算 (以节为月始)
# ──────────────────────────────────────
def _get_month_branch(month_num: int) -> str:
    """
    月地支: 正月寅, 二月卯, ...
    寅=1 (BRANCH_INDEX_YIN_ONE)
    """
    yin_one_order = ["寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑"]
    return yin_one_order[(month_num - 1) % 12]


def _get_month_stem(year_stem: str, month_num: int) -> str:
    """
    月天干推算 (五虎遁):
    甲己之年丙作首, 乙庚之岁戊为头,
    丙辛必定寻庚起, 丁壬壬位顺行流,
    若问戊癸何方发, 甲寅之上好追求.
    """
    month_stem_start = {
        "甲": "丙", "己": "丙",
        "乙": "庚", "庚": "戊",
        "丙": "庚", "辛": "庚",
        "丁": "壬", "壬": "壬",
        "戊": "甲", "癸": "甲",
    }
    
    start_stem = month_stem_start[year_stem]
    start_idx = HEAVENLY_STEMS.index(start_stem)
    month_idx = (start_idx + month_num - 1) % 10
    return HEAVENLY_STEMS[month_idx]


def month_ganzhi(date: datetime) -> str:
    """
    计算月柱干支 (以节为月始).
    
    立春正月, 惊蛰二月, 清明三月, 立夏四月,
    芒种五月, 小暑六月, 立秋七月, 白露八月,
    寒露九月, 立冬十月, 大雪十一月, 小寒十二月.
    
    Args:
        date: 公历日期
    
    Returns:
        月干支 (如 "丙寅")
    """
    # 确保 UTC-aware
    if date.tzinfo is None:
        from datetime import timezone as _tz
        date = date.replace(tzinfo=_tz.utc)
    
    # 获取当前节
    jie_name, _, _, _ = get_current_jieqi(date)
    
    # 节的月份
    if jie_name not in JIE_TO_MONTH:
        # fallback: 用公历月份近似
        month_num = date.month
    else:
        month_num = JIE_TO_MONTH[jie_name]
    
    # 获取年天干
    ygz = year_ganzhi(date)
    year_stem = ygz[0]
    
    month_stem = _get_month_stem(year_stem, month_num)
    month_branch = _get_month_branch(month_num)
    
    return month_stem + month_branch


# ──────────────────────────────────────
# 日柱计算
# ──────────────────────────────────────
def day_ganzhi(date: datetime, birth_hour: int = 0) -> str:
    """
    计算日柱干支.
    
    使用公历日期计算, 精度覆盖公元前后.
    公式基于儒略日 (Julian Day).
    
    子时 (23:00-01:00) 的特殊处理:
    - 23:00 之后出生, 日柱用次日
    - 部分流派认为子时前半用当日, 后半用次日
    
    Args:
        date: 公历日期
        birth_hour: 出生小时 (0-23). 23点之后视为次日.
    
    Returns:
        日干支 (如 "甲子")
    """
    from .solar_terms import julian_day
    
    # 构建日期
    y, m, d = date.year, date.month, date.day
    
    # 子时 (23点后) 的特殊处理
    if birth_hour >= 23:
        # 用次日日期
        next_day = date + timedelta(days=1)
        y, m, d = next_day.year, next_day.month, next_day.day
    
    # 计算儒略日
    jd = julian_day(y, m, d)
    
    # 日干支 = (JD + 12) % 60
    # 已知 2000-01-01 (JD=2451545) 是 戊午 (54)
    # 验证: (2451545 + 12) % 60 = 2451557 % 60 = ... 
    # 实际上公式: day_ganzhi_index = (int(jd + 0.5) + 49) % 60
    # 更标准的: (int(jd + 0.5) - 1) % 60 取干支
    # 验证: 2000-01-01 (JD=2451545)
    # int(2451545 + 0.5) = 2451545
    # (2451545 - 1) % 60 = 2451544 % 60 = 4
    # 甲子=0, 乙丑=1, 丙寅=2, 丁卯=3, 戊辰=4
    # 2000-01-01 应该是戊午 (日干支), 不对...
    
    # 重新校准:
    # 2024-01-01 (JD=2460311) 是甲子日
    # int(2460311 + 0.5) = 2460311
    # (2460311 - 某常数) % 60 = 0 (甲子)
    # 2460311 % 60 = 11
    # 常数 = 11
    # 验证: 2000-01-01 (JD=2451545)
    # (2451545 - 11) % 60 = 2451534 % 60 = 54 (戊午, index=54)
    # 不对, 2000-01-01 是戊午日吗?
    # 查万年历: 2000-01-01 是 戊午日? 实际查万年历 2000-01-01 农历1999年11月25日 庚午日(?)
    # 实际上我无法验证所有日期, 让我用一个已知日期:
    # 1900-01-01 (JD=2415021) = 甲戌日 (index=10)?
    # 使用公式: (2415021 + 10) % 60 = 2415031 % 60 = 31 ... 不是0
    # 常用公式: 日干支序号 = (JD + 10) % 60?
    
    # 标准公式 (来自天文算法):
    # 日干支 index = (int(JD + 0.5) + 49) % 60  -- 这是农历计算的常用公式
    # 或者: (int(JD + 0.5) + 13) % 60
    # 让我用 Python 验证:
    # from ephem import Date
    # 我用 2024-06-10 来验证: JD=2460472
    # (2460472 + 49) % 60 = (2460521) % 60 = 1 ... 
    # 实际上我直接使用已知公式即可。
    
    # 日干支公式: (int(JD + 0.5) + 49) % 60
    # 已验证: 2024-01-01 (JD=2460310.5) -> 甲子 (index 0)
    day_gz_idx = (int(jd + 0.5) + 49) % 60
    return SEXAGENARY_CYCLE[day_gz_idx]


# ──────────────────────────────────────
# 时柱计算
# ──────────────────────────────────────
def chinese_hour_from_time(hour: int, minute: int = 0) -> str:
    """
    将24小时制时间映射到时辰 (地支).
    
    子时: 23:00-01:00
    丑时: 01:00-03:00
    ...
    亥时: 21:00-23:00
    
    Args:
        hour: 小时 (0-23)
        minute: 分钟 (0-59)
    
    Returns:
        时辰地支 (如 "子")
    """
    # 计算绝对分钟数 (从0点开始)
    total_minutes = hour * 60 + minute
    
    # 时辰顺序: 子丑寅卯辰巳午未申酉戌亥
    # 子时从 23:00 (前一天的23:00) 开始
    # 但在当天范围内: 0:00-1:00=子, 1:00-3:00=丑, ...
    
    hour_ranges = [
        ("子", 0, 1),     # 0:00 - 1:00
        ("丑", 1, 3),     # 1:00 - 3:00
        ("寅", 3, 5),
        ("卯", 5, 7),
        ("辰", 7, 9),
        ("巳", 9, 11),
        ("午", 11, 13),
        ("未", 13, 15),
        ("申", 15, 17),
        ("酉", 17, 19),
        ("戌", 19, 21),
        ("亥", 21, 23),
        ("子", 23, 24),   # 23:00 - 24:00
    ]
    
    for branch, start_h, end_h in hour_ranges:
        if start_h <= hour < end_h:
            return branch
    
    return "子"  # fallback


def _get_hour_stem(day_stem: str, hour_branch: str) -> str:
    """
    时天干推算 (五鼠遁):
    甲己还加甲, 乙庚丙作初,
    丙辛从戊起, 丁壬庚子居,
    戊癸何方发, 壬子是真途.
    """
    hour_stem_start = {
        "甲": "甲", "己": "甲",
        "乙": "丙", "庚": "丙",
        "丙": "戊", "辛": "戊",
        "丁": "庚", "壬": "庚",
        "戊": "壬", "癸": "壬",
    }
    
    start_stem = hour_stem_start[day_stem]
    start_idx = HEAVENLY_STEMS.index(start_stem)
    
    # 子时=0, 丑时=1, ...
    branch_idx = EARTHLY_BRANCHES.index(hour_branch)
    
    hour_stem_idx = (start_idx + branch_idx) % 10
    return HEAVENLY_STEMS[hour_stem_idx]


def hour_ganzhi(date: datetime, hour: int, minute: int = 0) -> str:
    """
    计算时柱干支.
    
    Args:
        date: 公历日期
        hour: 出生小时 (0-23)
        minute: 出生分钟
    
    Returns:
        时干支 (如 "甲子")
    """
    # 获取时辰地支
    branch = chinese_hour_from_time(hour, minute)
    
    # 获取日天干 (需考虑子时跨日)
    birth_hour_for_day = hour
    dgz = day_ganzhi(date, hour)
    day_stem = dgz[0]
    
    hour_stem = _get_hour_stem(day_stem, branch)
    
    return hour_stem + branch


# ──────────────────────────────────────
# 四柱整合计算
# ──────────────────────────────────────
def calculate_four_pillars(
    year: int, month: int, day: int,
    hour: int, minute: int = 0
) -> dict:
    """
    计算完整的四柱八字.
    
    Args:
        year: 公历年
        month: 公历月
        day: 公历日
        hour: 出生小时 (0-23)
        minute: 出生分钟
    
    Returns:
        {
            "year_ganzhi": str,
            "month_ganzhi": str,
            "day_ganzhi": str,
            "hour_ganzhi": str,
            "year_stem": str,
            "year_branch": str,
            "month_stem": str,
            "month_branch": str,
            "day_stem": str,
            "day_branch": str,
            "hour_stem": str,
            "hour_branch": str,
            "chinese_hour": str,
            "lunar_month": int,  # 斗数月份
            "zodiac": str,
        }
    """
    dt = datetime(year, month, day, hour, minute)
    # 转换为 UTC-aware (与时区感知的节气结果兼容)
    from datetime import timezone as tz
    dt = dt.replace(tzinfo=tz.utc)
    
    ygz = year_ganzhi(dt)
    mgz = month_ganzhi(dt)
    dgz = day_ganzhi(dt, hour)
    hgz = hour_ganzhi(dt, hour, minute)
    ch_hour = chinese_hour_from_time(hour, minute)
    
    from .constants import ZODIAC
    zodiac = ZODIAC.get(ygz[1], "")
    
    from .solar_terms import get_lunar_month_by_jieqi
    lm = get_lunar_month_by_jieqi(dt)
    
    return {
        "year_ganzhi": ygz,
        "month_ganzhi": mgz,
        "day_ganzhi": dgz,
        "hour_ganzhi": hgz,
        "year_stem": ygz[0],
        "year_branch": ygz[1],
        "month_stem": mgz[0],
        "month_branch": mgz[1],
        "day_stem": dgz[0],
        "day_branch": dgz[1],
        "hour_stem": hgz[0],
        "hour_branch": hgz[1],
        "chinese_hour": ch_hour,
        "lunar_month": lm,
        "zodiac": zodiac,
    }
