"""
安星"为什么"解释层 —— 透明可验证的差异化内核。

给定一张已排好的命盘, 为每颗星产出: 规则名 + 索引公式 + 代入实际索引的推导
+ 出处。设计原则: **解释盘面的真实结果**, 不重新实现排盘——读取每颗星的实际
落宫, 再说明产生它的规则。配套测试交叉验证 "公式(输入) == 实际落宫", 保证
explain 与 engine 不漂移, 且不臆造未经验证的规则。

SSOT: 安星算法在 ziwei/chart/stars.py; 本模块只做人类可读的推导陈述。
"""

from typing import Dict, List, Optional

from ..calendar.constants import EARTHLY_BRANCHES, HEAVENLY_STEMS

B = EARTHLY_BRANCHES
SRC_MAIN = "紫微斗数全书 / 中州派 安星诀"

# 紫微系逆布偏移 (相对紫微)
ZIWEI_SERIES_OFFSET = {"天机": -1, "太阳": -3, "武曲": -4, "天同": -5, "廉贞": -8}
# 天府系顺布偏移 (相对天府)
TIANFU_SERIES_OFFSET = {
    "太阴": 1, "贪狼": 2, "巨门": 3, "天相": 4, "天梁": 5, "七杀": 6, "破军": 10,
}
# 禄存 (年干 → 地支)
LUCUN_BY_STEM = {
    "甲": "寅", "乙": "卯", "丙": "巳", "丁": "午", "戊": "巳",
    "己": "午", "庚": "申", "辛": "酉", "壬": "亥", "癸": "子",
}
# 天马 (年支 → 地支, 四马)
TIANMA_BY_BRANCH = {
    "申": "寅", "子": "寅", "辰": "寅", "寅": "申", "午": "申", "戌": "申",
    "巳": "亥", "酉": "亥", "丑": "亥", "亥": "巳", "卯": "巳", "未": "巳",
}
# 四化 (年干 → {星: 化})  —— 仅用于出处陈述, 真值取自 chart.sihua_map
SIHUA_RULE = "四化由生年天干起例 (禄权科忌)"


def _branch_index_map(chart) -> Dict[str, int]:
    """star -> 地支索引 (取自盘面真实落宫)。"""
    pos: Dict[str, int] = {}
    for p in chart.palaces:
        for s in p.stars:
            pos[s] = B.index(p.branch)
    return pos


def _entry(star, idx, category, rule, formula, derivation, source=SRC_MAIN):
    return {
        "star": star,
        "branch": B[idx],
        "branch_index": idx,
        "category": category,
        "rule": rule,
        "formula": formula,
        "derivation": derivation,
        "source": source,
    }


def explain_chart(chart) -> Dict[str, List[dict]]:
    """产出整盘安星解释 (只解释盘面实际存在的星)。"""
    pos = _branch_index_map(chart)
    stems = chart.year_pillar  # 年柱干支, e.g. "甲子"
    year_stem = stems[0] if stems else ""
    year_branch = stems[1] if len(stems) >= 2 else ""
    hour_branch = chart.hour_pillar[1] if len(chart.hour_pillar) >= 2 else ""
    h_idx = B.index(hour_branch) if hour_branch in B else 0
    lunar_month = chart.lunar_month or 0

    stars: List[dict] = []

    # ── 紫微 (诸星之首) ──
    if "紫微" in pos:
        zw = pos["紫微"]
        stars.append(_entry(
            "紫微", zw, "主星·紫微系",
            "紫微星诀: 由五行局数与农历生日定位",
            "查表(五行局, 农历日) → 紫微宫",
            f"五行局={chart.wuxing_ju_name or chart.wuxing_ju}, 农历{chart.lunar_day}日 "
            f"→ 紫微落{B[zw]}({zw})",
        ))

    # ── 天府 (寅申轴对称) ──
    if "天府" in pos and "紫微" in pos:
        zw = pos["紫微"]
        tf = pos["天府"]
        stars.append(_entry(
            "天府", tf, "主星·天府系",
            "天府与紫微关于寅申轴对称 (紫府永远同宫于寅或申)",
            "天府_idx = (4 - 紫微_idx) % 12",
            f"紫微在{B[zw]}({zw}) → 天府=(4-{zw})%12={tf}={B[tf]}",
        ))

    # ── 紫微系五曜 (逆布) ──
    if "紫微" in pos:
        zw = pos["紫微"]
        for star, off in ZIWEI_SERIES_OFFSET.items():
            if star in pos:
                idx = pos[star]
                stars.append(_entry(
                    star, idx, "主星·紫微系",
                    f"紫微系逆布: {star}在紫微逆行{abs(off)}宫",
                    f"{star}_idx = (紫微_idx {off:+d}) % 12",
                    f"紫微{B[zw]}({zw}) {off:+d} → {idx}={B[idx]}",
                ))

    # ── 天府系七曜 (顺布) ──
    if "天府" in pos:
        tf = pos["天府"]
        for star, off in TIANFU_SERIES_OFFSET.items():
            if star in pos:
                idx = pos[star]
                note = " (七杀空三→破军)" if star == "破军" else ""
                stars.append(_entry(
                    star, idx, "主星·天府系",
                    f"天府系顺布: {star}在天府顺行{off}宫{note}",
                    f"{star}_idx = (天府_idx + {off}) % 12",
                    f"天府{B[tf]}({tf}) +{off} → {idx}={B[idx]}",
                ))

    # ── 禄存 / 擎羊 / 陀罗 ──
    if "禄存" in pos:
        lc = pos["禄存"]
        stars.append(_entry(
            "禄存", lc, "辅星·年干系",
            "禄存按生年天干起例",
            "查表(年干) → 禄存宫",
            f"{year_stem}年 → 禄存落{B[lc]} (口诀: {year_stem}禄在{LUCUN_BY_STEM.get(year_stem, '?')})",
        ))
        if "擎羊" in pos:
            stars.append(_entry(
                "擎羊", pos["擎羊"], "辅星·年干系",
                "禄前羊刃: 擎羊居禄存前一宫", "擎羊_idx = (禄存_idx + 1) % 12",
                f"禄存{B[lc]}({lc}) +1 → {B[pos['擎羊']]}",
            ))
        if "陀罗" in pos:
            stars.append(_entry(
                "陀罗", pos["陀罗"], "辅星·年干系",
                "后陀罗: 陀罗居禄存后一宫", "陀罗_idx = (禄存_idx - 1) % 12",
                f"禄存{B[lc]}({lc}) -1 → {B[pos['陀罗']]}",
            ))

    # ── 天魁 / 天钺 ──
    for star in ("天魁", "天钺"):
        if star in pos:
            stars.append(_entry(
                star, pos[star], "辅星·年干系",
                f"{star} (天乙贵人) 按生年天干起例",
                "查表(年干) → 贵人宫",
                f"{year_stem}年 → {star}落{B[pos[star]]}",
            ))

    # ── 左辅 / 右弼 (月系) ──
    if "左辅" in pos:
        stars.append(_entry(
            "左辅", pos["左辅"], "辅星·月系",
            "左辅: 辰宫起正月, 顺数至生月",
            "左辅_idx = (辰_idx + 农历月 - 1) % 12",
            f"辰(4) +({lunar_month}-1) → {B[pos['左辅']]}",
        ))
    if "右弼" in pos:
        stars.append(_entry(
            "右弼", pos["右弼"], "辅星·月系",
            "右弼: 戌宫起正月, 逆数至生月",
            "右弼_idx = (戌_idx - (农历月 - 1)) % 12",
            f"戌(10) -({lunar_month}-1) → {B[pos['右弼']]}",
        ))

    # ── 文昌 / 文曲 (时系) ──
    if "文昌" in pos:
        stars.append(_entry(
            "文昌", pos["文昌"], "辅星·时系",
            "文昌: 戌宫起子时, 逆数至生时",
            "文昌_idx = (戌_idx - 时支_idx) % 12",
            f"戌(10) -{h_idx}({hour_branch}时) → {B[pos['文昌']]}",
        ))
    if "文曲" in pos:
        stars.append(_entry(
            "文曲", pos["文曲"], "辅星·时系",
            "文曲: 辰宫起子时, 顺数至生时",
            "文曲_idx = (辰_idx + 时支_idx) % 12",
            f"辰(4) +{h_idx}({hour_branch}时) → {B[pos['文曲']]}",
        ))

    # ── 地劫 / 地空 (时系) ──
    if "地劫" in pos:
        stars.append(_entry(
            "地劫", pos["地劫"], "辅星·时系·煞",
            "地劫: 亥宫起子时, 顺行至生时 (亥上起子顺安劫)",
            "地劫_idx = (亥_idx + 时支_idx) % 12",
            f"亥(11) +{h_idx}({hour_branch}时) → {B[pos['地劫']]}",
        ))
    if "地空" in pos:
        stars.append(_entry(
            "地空", pos["地空"], "辅星·时系·煞",
            "地空: 亥宫起子时, 逆行至生时",
            "地空_idx = (亥_idx - 时支_idx) % 12",
            f"亥(11) -{h_idx}({hour_branch}时) → {B[pos['地空']]}",
        ))

    # ── 火星 / 铃星 (年支三合局 + 时) ──
    for star in ("火星", "铃星"):
        if star in pos:
            stars.append(_entry(
                star, pos[star], "辅星·年支时系·煞",
                f"{star}: 按年支三合局起子时位, 顺行至生时 (主流中州派/全书)",
                f"{star}_idx = (起宫(年支三合局) + 时支_idx) % 12",
                f"{year_branch}年三合局起宫 +{h_idx}({hour_branch}时) → {B[pos[star]]}",
            ))

    # ── 天马 (年支四马) ──
    if "天马" in pos:
        stars.append(_entry(
            "天马", pos["天马"], "辅星·年支系",
            "天马 (驿马): 按年支三合局落四马地 (寅申巳亥)",
            "查表(年支) → 四马地",
            f"{year_branch}年 → 天马落{B[pos['天马']]} (口诀: {year_branch}马在{TIANMA_BY_BRANCH.get(year_branch, '?')})",
        ))

    # ── 四化 ──
    sihua: List[dict] = []
    for star, hua in (chart.sihua_map or {}).items():
        sihua.append({
            "star": star,
            "type": hua,
            "rule": SIHUA_RULE,
            "derivation": f"{year_stem}年 → {star}{hua}",
            "source": SRC_MAIN,
        })

    return {
        "stars": stars,
        "sihua": sihua,
        "notes": [
            "本解释陈述盘面真实落宫的产生规则; 采用主流中州派/全书安星法。",
            "流派差异 (如火铃宋版异本) 不在默认解释内。",
        ],
    }
