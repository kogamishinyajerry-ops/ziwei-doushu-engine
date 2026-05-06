"""
十二宫排布模块 — Palace Layout

安命宫、身宫、十二宫排列、天干地支、五行局
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass, field

from ..calendar.constants import (
    HEAVENLY_STEMS, EARTHLY_BRANCHES,
    BRANCH_INDEX_ZI_ONE, BRANCH_INDEX_YIN_ONE,
    PALACE_NAMES, NAYIN_FULL, NAYIN_TO_JU,
    WUXING_JU_NUMBER,
)


@dataclass
class PalaceLayout:
    """十二宫排布结果."""
    # 命宫地支索引 (0=子, 1=丑, ..., 11=亥)
    ming_index: int
    
    # 身宫地支索引
    shen_index: int
    
    # 十二宫: dict[宫名] = 地支索引
    palaces: Dict[str, int] = field(default_factory=dict)
    
    # 各宫天干: dict[宫名] = 天干
    stems: Dict[str, str] = field(default_factory=dict)
    
    # 五行局数 (2,3,4,5,6)
    wuxing_ju: int = 0
    
    # 五行局名
    wuxing_ju_name: str = ""
    
    # 命宫天干
    ming_stem: str = ""
    
    # 命宫地支
    ming_branch: str = ""
    
    # 命宫纳音
    ming_nayin: str = ""


def place_palaces(lunar_month: int, hour_branch: str) -> PalaceLayout:
    """
    安命宫、身宫，排列十二宫.
    
    紫微斗数安命宫法:
    以寅宫起正月, 顺时针数至生月之宫,
    再以此宫起子时, 逆时针数至生时, 即为命宫.
    
    安身宫法:
    以寅宫起正月, 顺时针数至生月之宫,
    再以此宫起子时, 顺时针数至生时, 即为身宫.
    
    Args:
        lunar_month: 农历生月 (1=正月, 2=二月, ..., 12=腊月)
        hour_branch: 出生时辰地支 (子/丑/寅/卯/...)
    
    Returns:
        PalaceLayout with ming_index, shen_index, palaces
    """
    # 地支索引: 子=0, 丑=1, 寅=2, ..., 亥=11
    hour_idx = EARTHLY_BRANCHES.index(hour_branch)  # 子=0
    
    # 寅的索引 = 2
    yin_idx = 2
    
    # 命宫地支索引
    # 从寅顺数月数, 再逆数时数
    # ming_idx = (yin_idx + (lunar_month - 1) - (hour_idx)) % 12
    # 简化为: (2 + lunar_month - 1 - hour_idx) % 12
    # 但 hour_idx for 子=0, 而中文时辰子=1...
    # 实际上子时在逆数时应计为1
    # 修正: hour_count = hour_idx + 1 (因为子时=第1个时辰)
    hour_count = hour_idx + 1  # 子=1, 丑=2, ..., 亥=12
    
    ming_idx = (yin_idx + (lunar_month - 1) - (hour_count - 1)) % 12
    
    # 身宫地支索引
    # 从寅顺数月数, 再顺数时数
    shen_idx = (yin_idx + (lunar_month - 1) + (hour_count - 1)) % 12
    
    # 十二宫逆排 (从命宫逆时针排列)
    palaces = {}
    for i, name in enumerate(PALACE_NAMES):
        # 兄弟宫在命宫逆1位, 夫妻逆2位, ...
        palace_idx = (ming_idx - i) % 12
        palaces[name] = palace_idx
    
    return PalaceLayout(
        ming_index=ming_idx,
        shen_index=shen_idx,
        palaces=palaces,
    )


def place_stems_branches(layout: PalaceLayout, year_stem: str) -> PalaceLayout:
    """
    定十二宫天干 (五虎遁).
    
    以寅宫天干为基准, 用五虎遁法确定,
    然后顺排十二宫天干.
    
    五虎遁诀:
    甲己之年丙作首 (寅宫=丙)
    乙庚之岁戊为头 (寅宫=戊)
    丙辛必定寻庚起 (寅宫=庚)
    丁壬壬位顺行流 (寅宫=壬)
    戊癸何方发, 甲寅之上好追求 (寅宫=甲)
    
    Args:
        layout: PalaceLayout (已有 palaces)
        year_stem: 生年天干
    
    Returns:
        更新后的 PalaceLayout (包含 stems)
    """
    # 五虎遁: 年干 → 寅宫天干
    yin_stem_map = {
        "甲": "丙", "己": "丙",
        "乙": "戊", "庚": "戊",
        "丙": "庚", "辛": "庚",
        "丁": "壬", "壬": "壬",
        "戊": "甲", "癸": "甲",
    }
    
    yin_stem = yin_stem_map[year_stem]
    yin_stem_idx = HEAVENLY_STEMS.index(yin_stem)
    
    # 各宫天干: 从寅宫开始, 顺排
    # 宫位地支索引: 子=0, 寅=2
    stems = {}
    for name, branch_idx in layout.palaces.items():
        # 从寅到该宫位的偏移
        offset = (branch_idx - 2) % 12  # 寅=2
        stem_idx = (yin_stem_idx + offset) % 10
        stems[name] = HEAVENLY_STEMS[stem_idx]
    
    layout.stems = stems
    
    # 命宫干支
    layout.ming_branch = EARTHLY_BRANCHES[layout.ming_index]
    layout.ming_stem = stems["命宫"]
    
    return layout


def determine_wuxing_ju(layout: PalaceLayout) -> PalaceLayout:
    """
    定五行局.
    
    根据命宫的天干地支, 查纳音表确定五行局.
    五行局数: 水2, 木3, 金4, 土5, 火6
    
    Args:
        layout: PalaceLayout (已有命宫天干地支)
    
    Returns:
        更新后的 PalaceLayout (包含 wuxing_ju)
    """
    ganzhi = layout.ming_stem + layout.ming_branch
    
    # 查找纳音
    nayin = None
    for i, n in enumerate(NAYIN_FULL):
        if i * 2 <= 59 and SEXAGENARY_CYCLE_LOOKUP.get(ganzhi) == i // 2:
            nayin = n
            break
    
    # 从六十甲子直接查纳音
    from ..calendar.constants import SEXAGENARY_CYCLE
    gz_idx = SEXAGENARY_CYCLE.index(ganzhi)
    nayin_idx = gz_idx // 2  # 每两个干支共用一个纳音
    nayin = NAYIN_FULL[nayin_idx]
    
    # 纳音 → 五行局数
    ju = NAYIN_TO_JU.get(nayin, 4)  # 默认金四局
    ju_name = WUXING_JU_NUMBER.get(ju, f"局{ju}")
    
    layout.wuxing_ju = ju
    layout.wuxing_ju_name = ju_name
    layout.ming_nayin = nayin
    
    return layout


# 用于快速查找六十甲子中的位置
SEXAGENARY_CYCLE_LOOKUP = {}
from ..calendar.constants import SEXAGENARY_CYCLE as _SC
for _i, _gz in enumerate(_SC):
    SEXAGENARY_CYCLE_LOOKUP[_gz] = _i // 2
