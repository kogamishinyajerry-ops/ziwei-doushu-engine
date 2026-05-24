"""
星曜安放模块 — Star Placement Engine

紫微斗数核心算法: 安紫微、天府系、紫微系、辅星
"""

import math
from typing import Dict, List, Optional
from dataclasses import dataclass, field

from ..calendar.constants import (
    HEAVENLY_STEMS, EARTHLY_BRANCHES,
    BRANCH_INDEX_ZI_ONE, BRANCH_INDEX_YIN_ONE,
    ZIWEI_SERIES, TIANFU_SERIES, AUXILIARY_STARS,
    MONTH_STARS, YEAR_STARS, MONTH_HOUR_STARS,
    SEXAGENARY_CYCLE,
)


@dataclass
class StarLayout:
    """星曜布局结果."""
    # 紫微所在宫位的地支索引 (0=子, ..., 11=亥)
    ziwei_index: int = 0
    
    # 天府所在宫位的地支索引
    tianfu_index: int = 0
    
    # 所有星曜: dict[星名] = 地支索引
    stars: Dict[str, int] = field(default_factory=dict)
    
    # 星曜的五行属性: dict[星名] = 五行
    star_wuxing: Dict[str, str] = field(default_factory=dict)


# ──────────────────────────────────────
# 安紫微星
# ──────────────────────────────────────

def _compute_ziwei_position(wuxing_ju: int, lunar_day: int) -> int:
    """
    计算紫微星的地支位置.
    
    算法:
    以五行局数为除数, 农历生日为被除数.
    从寅宫起1, 顺数至商数(整除)或商数+1(有余数).
    
    Args:
        wuxing_ju: 五行局数 (2,3,4,5,6)
        lunar_day: 农历生日 (1-30)
    
    Returns:
        地支索引 (0=子, 1=丑, ..., 11=亥)
    """
    # ceil(day / ju) = 从寅起数
    positions_from_yin = math.ceil(lunar_day / wuxing_ju)
    
    # 寅的索引 = 2 (在子=0的坐标系中)
    yin_idx = 2
    
    # 紫微位置 = 寅 + (positions_from_yin - 1)
    ziwei_idx = (yin_idx + positions_from_yin - 1) % 12
    
    return ziwei_idx


def place_ziwei(wuxing_ju: int, lunar_day: int) -> StarLayout:
    """
    安紫微星.
    
    紫微是诸星之首, 其位置决定了天府系和紫微系所有星的分布.
    
    Args:
        wuxing_ju: 五行局数
        lunar_day: 农历生日
    
    Returns:
        StarLayout (仅含紫微位置)
    """
    ziwei_idx = _compute_ziwei_position(wuxing_ju, lunar_day)
    
    layout = StarLayout(ziwei_index=ziwei_idx)
    layout.stars["紫微"] = ziwei_idx
    layout.star_wuxing["紫微"] = "土"
    
    return layout


# ──────────────────────────────────────
# 安天府系八星
# ──────────────────────────────────────

# 天府系星序: 天府 → 太阴 → 贪狼 → 巨门 → 天相 → 天梁 → 七杀 → 破军
#
# 天府与紫微关于"寅申"连线对称 (紫微斗数铁律, 无流派分歧:
# 紫微、天府永远同宫于寅宫或申宫)。圆周上关于过 寅(idx 2)/申(idx 8)
# 轴的反射即: 天府_idx = (4 - 紫微_idx) % 12。
#
# 锚点验证:
#   紫微寅(2) → 天府寅(2)   (同宫)
#   紫微申(8) → 天府申(8)   (同宫)
#   紫微子(0) → 天府辰(4)
#   紫微午(6) → 天府戌(10)
#
# 注: 历史实现误用"卯酉"轴 ((6 - 紫微) % 12), 导致全盘天府系 8 颗主星
#     (天府/太阴/贪狼/巨门/天相/天梁/七杀/破军) 错位, 已修正为寅申轴。
ZIWEI_IDX_TO_TIANFU_IDX = {z: (4 - z) % 12 for z in range(12)}


def place_tianfu_series(layout: StarLayout) -> StarLayout:
    """
    安天府系八星.
    
    天府与紫微的位置有固定对应关系.
    天府系星从天府开始, 顺时针(顺数)排列:
    天府 → 太阴 → 贪狼 → 巨门 → 天相 → 天梁 → 七杀 → 破军
    
    Args:
        layout: StarLayout (已有紫微)
    
    Returns:
        更新后的 StarLayout
    """
    ziwei_idx = layout.ziwei_index
    
    # 天府位置
    tianfu_idx = ZIWEI_IDX_TO_TIANFU_IDX[ziwei_idx]
    layout.tianfu_index = tianfu_idx
    layout.stars["天府"] = tianfu_idx
    layout.star_wuxing["天府"] = "土"
    
    # 天府系相对天府的顺时针偏移。
    # 天府→太阴→贪狼→巨门→天相→天梁→七杀 为连续 (+1..+6),
    # 但"七杀空三破军" — 七杀之后空三宫才是破军, 故 破军 = 天府+10。
    # 校验铁律: 破军永远与天相对宫 (天相+10-4=+6, 差6); 七杀与天府对宫 (+6)。
    tf_offsets = {
        "太阴": 1, "贪狼": 2, "巨门": 3, "天相": 4,
        "天梁": 5, "七杀": 6, "破军": 10,
    }
    tf_wuxing = {
        "太阴": "水", "贪狼": "木", "巨门": "水",
        "天相": "水", "天梁": "土", "七杀": "金", "破军": "水",
    }

    for star_name, offset in tf_offsets.items():
        layout.stars[star_name] = (tianfu_idx + offset) % 12
        layout.star_wuxing[star_name] = tf_wuxing.get(star_name, "")

    return layout


# ──────────────────────────────────────
# 安紫微系六星
# ──────────────────────────────────────

def place_ziwei_series(layout: StarLayout) -> StarLayout:
    """
    安紫微系六星.
    
    紫微系星从紫微开始, 逆时针(逆数)排列, gap 结构为"隔一/隔二/空三":
    紫微 →天机(逆1)→[隔一]→太阳(逆3)→武曲(逆4)→天同(逆5)→[隔二]→廉贞(逆8)→[空三]→紫微

    即紫微系五曜相对于紫微的逆时针偏移:
    天机: -1
    太阳: -3
    武曲: -4
    天同: -5
    廉贞: -8 (天同后空二位; 校验铁律: 紫微在申时廉贞天相同宫于子)

    Args:
        layout: StarLayout (已有紫微)

    Returns:
        更新后的 StarLayout
    """
    ziwei_idx = layout.ziwei_index

    # 紫微系星相对于紫微的逆时针偏移
    zw_offsets = {
        "天机": -1,
        "太阳": -3,
        "武曲": -4,
        "天同": -5,
        "廉贞": -8,
    }
    
    zw_wuxing = {
        "天机": "木", "太阳": "火", "武曲": "金",
        "天同": "水", "廉贞": "火",
    }
    
    for star_name, offset in zw_offsets.items():
        star_idx = (ziwei_idx + offset) % 12
        layout.stars[star_name] = star_idx
        layout.star_wuxing[star_name] = zw_wuxing.get(star_name, "")
    
    return layout


# ──────────────────────────────────────
# 安辅星
# ──────────────────────────────────────

def place_auxiliary_stars(
    layout: StarLayout,
    year_branch: str,
    month_branch: str,
    hour_branch: str,
    lunar_month: int,
    huoling_variant: str = "mainstream",
) -> StarLayout:
    """
    安辅星 (月系、时系、年系).
    
    包含: 左辅、右弼、文昌、文曲、天魁、天钺、
          禄存、擎羊、陀罗、火星、铃星、天马、
          地劫、地空
    
    Args:
        layout: StarLayout
        year_branch: 年支 (子/丑/...)
        month_branch: 月支
        hour_branch: 时支
        lunar_month: 农历月数 (1-12)
    
    Returns:
        更新后的 StarLayout
    """
    yi = EARTHLY_BRANCHES.index  # 地支→索引
    
    # ── 左辅、右弼 (月系星, 从辰/戌起) ──
    # 左辅: 辰上起正月, 顺数至生月
    zuofu_idx = (yi("辰") + lunar_month - 1) % 12
    layout.stars["左辅"] = zuofu_idx
    
    # 右弼: 戌上起正月, 逆数至生月
    youbi_idx = (yi("戌") - (lunar_month - 1)) % 12
    layout.stars["右弼"] = youbi_idx
    
    # ── 文昌、文曲 (时系星, 从戌/辰起) ──
    h_idx = yi(hour_branch)
    # 文昌: 戌上起子时, 逆数至生时
    wenchang_idx = (yi("戌") - h_idx) % 12
    layout.stars["文昌"] = wenchang_idx
    
    # 文曲: 辰上起子时, 顺数至生时
    wenqu_idx = (yi("辰") + h_idx) % 12
    layout.stars["文曲"] = wenqu_idx
    
    # ── 天魁、天钺 (年系星) ──
    # 天魁: 根据年干
    # 天钺: 根据年干
    # 这里简化: 需要年干, 但目前只有年支
    # 天魁天钺由年干决定, 通过调用者传入
    # 暂时跳过, 由 place_all_stars 补充
    
    # ── 禄存、擎羊、陀罗 (年系星) ──
    # 禄存: 根据年干 (甲→寅, 乙→卯, ...)
    # 同样需要年干, 在 place_all_stars 中处理
    
    # ── 火星、铃星 (年支+时支) ──
    # 火星铃星由年支和时支共同决定
    # 火星起法: 亥卯未年人, 子时火星在丑...
    # 铃星: 亥卯未年人, 子时铃星在戌...
    
    # 三星组: 申子辰, 巳酉丑, 寅午戌, 亥卯未
    trio_map = {
        "申": 0, "子": 0, "辰": 0,  # 申子辰
        "巳": 1, "酉": 1, "丑": 1,  # 巳酉丑
        "寅": 2, "午": 2, "戌": 2,  # 寅午戌
        "亥": 3, "卯": 3, "未": 3,  # 亥卯未
    }
    
    trio = trio_map[year_branch]

    # 火星/铃星起宫 (trio 顺序: 申子辰=0, 巳酉丑=1, 寅午戌=2, 亥卯未=3)。
    # mainstream = 主流中州派/全书 (Codex 异源确认); songban = 少数"宋版"异本,
    # 仅巳酉丑组不同 (火星戌起/铃星卯起), 仍顺行。流派可切换且显式标注。
    if huoling_variant == "songban":
        huo_starts = [yi("寅"), yi("戌"), yi("丑"), yi("酉")]
        ling_starts = [yi("戌"), yi("卯"), yi("卯"), yi("戌")]
    else:  # mainstream (default)
        huo_starts = [yi("寅"), yi("卯"), yi("丑"), yi("酉")]
        ling_starts = [yi("戌"), yi("戌"), yi("卯"), yi("戌")]

    layout.stars["火星"] = (huo_starts[trio] + h_idx) % 12
    layout.stars["铃星"] = (ling_starts[trio] + h_idx) % 12
    
    # ── 地劫、地空 (时系星) ──
    # 口诀: "亥上起子顺安劫, 逆回安空" → 地劫顺行、地空逆行。
    # (历史实现把两者顺逆颠倒, 已修正; 子时两者同宫于亥, 不受影响。)
    # 地劫: 亥上起子时, 顺行至生时
    dijie_idx = (yi("亥") + h_idx) % 12
    layout.stars["地劫"] = dijie_idx

    # 地空: 亥上起子时, 逆行至生时
    dikong_idx = (yi("亥") - h_idx) % 12
    layout.stars["地空"] = dikong_idx
    
    # ── 天马 (年支) ──
    # 亥卯未年, 天马在巳; 寅午戌年, 天马在申; 巳酉丑年, 天马在亥; 申子辰年, 天马在寅
    tianma_map = {
        "亥": "巳", "卯": "巳", "未": "巳",
        "寅": "申", "午": "申", "戌": "申",
        "巳": "亥", "酉": "亥", "丑": "亥",
        "申": "寅", "子": "寅", "辰": "寅",
    }
    layout.stars["天马"] = yi(tianma_map[year_branch])
    
    return layout


# ──────────────────────────────────────
# 整合安星
# ──────────────────────────────────────

def place_all_stars(
    wuxing_ju: int,
    lunar_day: int,
    year_stem: str,
    year_branch: str,
    month_branch: str,
    hour_branch: str,
    lunar_month: int,
    huoling_variant: str = "mainstream",
) -> StarLayout:
    """
    一次性安放所有星曜.
    
    Args:
        wuxing_ju: 五行局数
        lunar_day: 农历生日
        year_stem: 年干
        year_branch: 年支
        month_branch: 月支
        hour_branch: 时支
        lunar_month: 农历月数
    
    Returns:
        完整的 StarLayout
    """
    # 1. 安紫微
    layout = place_ziwei(wuxing_ju, lunar_day)
    
    # 2. 安天府系
    layout = place_tianfu_series(layout)
    
    # 3. 安紫微系
    layout = place_ziwei_series(layout)
    
    # 4. 安辅星
    layout = place_auxiliary_stars(
        layout, year_branch, month_branch, hour_branch, lunar_month,
        huoling_variant=huoling_variant,
    )
    
    # 5. 安禄存/擎羊/陀罗 (年干决定)
    yi = EARTHLY_BRANCHES.index
    
    # 禄存: 甲→寅, 乙→卯, 丙→巳, 丁→午, 戊→巳, 己→午, 庚→申, 辛→酉, 壬→亥, 癸→子
    lucun_map = {
        "甲": "寅", "乙": "卯", "丙": "巳", "丁": "午",
        "戊": "巳", "己": "午", "庚": "申", "辛": "酉",
        "壬": "亥", "癸": "子",
    }
    lucun_idx = yi(lucun_map[year_stem])
    layout.stars["禄存"] = lucun_idx
    
    # 擎羊: 禄存前一位 (顺时针)
    qingyang_idx = (lucun_idx + 1) % 12
    layout.stars["擎羊"] = qingyang_idx
    
    # 陀罗: 禄存后一位 (逆时针)
    tuoluo_idx = (lucun_idx - 1) % 12
    layout.stars["陀罗"] = tuoluo_idx
    
    # 6. 安天魁/天钺 (年干决定)
    # 天魁(阳贵)/天钺(阴贵) 按年干。口诀"丙丁猪鸡位": 丙丁同为 魁亥/钺酉。
    # (历史实现把丁的魁/钺对调, 已对齐主流斗数表; 配对集合本就正确。)
    tiankui_map = {
        "甲": "丑", "戊": "丑", "庚": "丑",
        "乙": "子", "己": "子",
        "丙": "亥", "丁": "亥",
        "辛": "午", "壬": "卯",
        "癸": "卯",
    }
    tianyue_map = {
        "甲": "未", "戊": "未", "庚": "未",
        "乙": "申", "己": "申",
        "丙": "酉", "丁": "酉",
        "辛": "寅", "壬": "巳",
        "癸": "巳",
    }
    layout.stars["天魁"] = yi(tiankui_map.get(year_stem, "丑"))
    layout.stars["天钺"] = yi(tianyue_map.get(year_stem, "未"))
    
    return layout
