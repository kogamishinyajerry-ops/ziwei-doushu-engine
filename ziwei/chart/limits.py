"""
大限/小限/流年模块 — Limits (大限、小限、流年、流月)

紫微斗数的动态时间层次:
- 大限 (10年一限): 从命宫起, 按五行局定起始年龄, 阴阳顺逆排列
- 小限 (1年一限): 按生年支定起始宫位, 男女顺逆
- 流年 (太岁): 以流年支所在宫为流年命宫
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field

from ..calendar.constants import (
    EARTHLY_BRANCHES, HEAVENLY_STEMS,
    PALACE_NAMES, JU_TO_DAXIAN_START,
    STEM_YINYANG,
)


@dataclass
class LimitsLayout:
    """大限小限布局."""
    # 大限: {宫名: (起始年龄, 结束年龄)}
    daxian: Dict[str, tuple] = field(default_factory=dict)
    
    # 小限: {年龄: 宫名}
    xiaoxian: Dict[int, str] = field(default_factory=dict)
    
    # 流年命宫: {流年支: 宫名}
    liunian_ming: Dict[str, str] = field(default_factory=dict)


def calculate_daxian(
    ming_index: int,
    wuxing_ju: int,
    year_stem: str,
    is_male: bool = True,
) -> LimitsLayout:
    """
    起大限.
    
    规则:
    1. 起始年龄根据五行局定: 水2局从2岁起, 木3局从3岁起, ...
    2. 阳男阴女顺行 (顺时针), 阴男阳女逆行 (逆时针)
    3. 每个大限管10年
    
    Args:
        ming_index: 命宫地支索引 (0=子, 1=丑, ...)
        wuxing_ju: 五行局数
        year_stem: 年干 (用于判断阴阳)
        is_male: 是否男性
    
    Returns:
        LimitsLayout (含大限信息)
    """
    layout = LimitsLayout()
    
    # 起始年龄
    start_age = JU_TO_DAXIAN_START[wuxing_ju]
    
    # 判断顺逆行
    # 年干阴阳
    yin_yang = STEM_YINYANG.get(year_stem, "阳")
    
    if yin_yang == "阳":
        if is_male:
            direction = 1   # 阳男顺行
        else:
            direction = -1  # 阳女逆行
    else:  # 阴
        if is_male:
            direction = -1  # 阴男逆行
        else:
            direction = 1   # 阴女顺行
    
    # 从命宫开始, 按方向排12个大限
    # 每个大限10年
    age = start_age
    for i in range(12):
        palace_idx = (ming_index + direction * i) % 12
        palace_name = PALACE_NAMES[(palace_idx - ming_index) % 12]  # 找到该位置的宫名
        
        # 实际上大限是 assigned to each palace in order
        # 从命宫起, 顺或逆行, 每宫管10年
        # But we need to map the palace index back to palace name
        # 宫名从命宫逆排: ming=命宫, (ming-1)=兄弟, ...
        
        # Find which palace is at this branch index
        branch = EARTHLY_BRANCHES[palace_idx]
        
        # 我们需要知道每个地支上是什么宫
        # 暂时用反向映射
        
        layout.daxian[i] = (age, age + 9, palace_idx)
        age += 10
    
    return layout


def calculate_xiaoxian(
    year_branch: str,
    is_male: bool = True,
) -> Dict[int, str]:
    """
    起小限.
    
    规则:
    1. 生年支决定起始宫位
    2. 男顺女逆, 一年一宫
    
    Args:
        year_branch: 年支
        is_male: 是否男性
    
    Returns:
        {年龄: 宫名} (1岁到N岁)
    """
    # 小限起始宫位: 根据年支
    # 申子辰年生人, 男从戌起, 女从辰起
    # 寅午戌年生人, 男从辰起, 女从戌起
    # 亥卯未年生人, 男从丑起, 女从未起
    # 巳酉丑年生人, 男从未起, 女从丑起
    
    trio_map = {
        "申": 0, "子": 0, "辰": 0,
        "巳": 1, "酉": 1, "丑": 1,
        "寅": 2, "午": 2, "戌": 2,
        "亥": 3, "卯": 3, "未": 3,
    }
    
    trio = trio_map[year_branch]
    
    # 男顺数, 女逆数
    if is_male:
        start_branches = ["戌", "丑", "辰", "未"]   # 男
        start_branch = start_branches[trio]
        direction = 1
    else:
        start_branches = ["辰", "未", "戌", "丑"]   # 女
        start_branch = start_branches[trio]
        direction = -1
    
    start_idx = EARTHLY_BRANCHES.index(start_branch)
    
    xiaoxian = {}
    for age in range(1, 101):  # 支持到100岁
        idx = (start_idx + direction * (age - 1)) % 12
        branch = EARTHLY_BRANCHES[idx]
        xiaoxian[age] = branch
    
    return xiaoxian


def calculate_liunian(liunian_branch: str, ming_index: int) -> int:
    """
    流年命宫.
    
    以流年支所在宫为流年命宫.
    
    Args:
        liunian_branch: 流年地支
        ming_index: 原命宫地支索引
    
    Returns:
        流年命宫的地支索引
    """
    return EARTHLY_BRANCHES.index(liunian_branch)
