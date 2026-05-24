"""
八字命理分析引擎 — Bazi (Four Pillars) Analysis

八字核心分析:
1. 日主强弱/旺衰
2. 十神排布 (Ten Gods)
3. 用神/忌神推断
4. 格局初步判断
5. 流年与大运交互

与紫微斗数的关系:
- 八字为体, 斗数为用
- 八字看先天格局, 斗数看后天运程
- 本模块补充八字维度的分析
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from ..calendar.constants import (
    HEAVENLY_STEMS, EARTHLY_BRANCHES,
    STEM_WUXING, BRANCH_WUXING,
    STEM_YINYANG, BRANCH_YINYANG,
    BRANCH_HIDDEN_STEMS,
    WUXING_SHENG, WUXING_KE,
    ZODIAC, SEXAGENARY_CYCLE,
)


# ════════════════════════════════════
# 十神定义
# ════════════════════════════════════

TEN_GODS = [
    "比肩", "劫财",   # 同我
    "食神", "伤官",   # 我生
    "正财", "偏财",   # 我克
    "正官", "七杀",   # 克我
    "正印", "偏印",   # 生我
]

TEN_GOD_EMOJI = {
    "比肩": "🤝", "劫财": "⚔️",
    "食神": "🍀", "伤官": "💡",
    "正财": "💰", "偏财": "🎲",
    "正官": "👔", "七杀": "⚡",
    "正印": "📚", "偏印": "🦉",
}

TEN_GOD_NATURE = {
    "比肩": "同类助力, 朋友兄弟",
    "劫财": "竞争关系, 主动进取",
    "食神": "才华输出, 享福安闲",
    "伤官": "聪明傲气, 创新突破",
    "正财": "稳定收入, 踏实积累",
    "偏财": "意外之财, 投机冒险",
    "正官": "规矩约束, 事业名声",
    "七杀": "挑战压力, 权威决断",
    "正印": "学习庇荫, 贵人助力",
    "偏印": "特殊才能, 宗教玄学",
}


@dataclass
class PillarAnalysis:
    """单柱分析."""
    stem: str           # 天干
    branch: str         # 地支
    hidden: List[str]   # 藏干
    ten_gods: Dict[str, str]  # {干/藏干: 十神名}
    wuxing_stem: str    # 天干五行
    wuxing_branch: str  # 地支五行
    
    
@dataclass
class BaziAnalysis:
    """八字完整分析."""
    # 四柱
    year: PillarAnalysis
    month: PillarAnalysis
    day: PillarAnalysis
    hour: PillarAnalysis
    
    # 日主
    day_master: str              # 日干
    day_master_wuxing: str       # 日主五行
    day_master_strength: str     # 强弱判断: 强/中/弱
    day_master_score: float      # 强弱得分 0-100
    
    # 十神全局
    ten_god_counts: Dict[str, int]  # 各十神出现次数
    
    # 用神/忌神
    favorable_god: str           # 用神五行
    unfavorable_god: str         # 忌神五行
    favorable_gods: List[str]    # 喜神列表
    unfavorable_gods: List[str]  # 忌神列表
    
    # 格局
    pattern_hint: str            # 格局提示
    
    # 五行平衡
    wuxing_balance: Dict[str, int]  # 各五行出现次数
    
    # 原始数据
    four_pillars: Dict[str, str]  # {year, month, day, hour}


@dataclass 
class LiunianBazi:
    """八字流年分析."""
    year: int
    year_ganzhi: str
    year_stem: str
    year_branch: str
    zodiac: str
    
    # 流年天干十神 (相对于日主)
    stem_ten_god: str
    
    # 流年地支十神 (以藏干主气)
    branch_main_ten_god: str
    
    # 与大运/命局关系
    day_master_clash: bool    # 冲克日主
    tai_sui_branch: bool      # 犯太岁
    
    # 评分
    rating: int               # -5 到 +5
    summary: str


# ════════════════════════════════════
# 核心计算函数
# ════════════════════════════════════

def year_ganzhi(year: int) -> str:
    """计算公历年的干支."""
    return SEXAGENARY_CYCLE[(year - 4) % 60]


def analyze_bazi(
    year_pillar: str,
    month_pillar: str,
    day_pillar: str,
    hour_pillar: str,
) -> BaziAnalysis:
    """
    分析八字.
    
    Args:
        year_pillar: 年柱干支, e.g. "甲子"
        month_pillar: 月柱干支
        day_pillar: 日柱干支
        hour_pillar: 时柱干支
    
    Returns:
        BaziAnalysis
    """
    pillars = {
        "年": year_pillar,
        "月": month_pillar,
        "日": day_pillar,
        "时": hour_pillar,
    }
    day_stem = day_pillar[0]
    
    # 分析每柱
    pillar_results = {}
    wuxing_count = {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}
    
    for name, gz in pillars.items():
        stem, branch = gz[0], gz[1]
        hidden = BRANCH_HIDDEN_STEMS.get(branch, [])
        
        # 十神
        ten_gods = {"天干" + stem: _get_ten_god(day_stem, stem)}
        for i, h in enumerate(hidden):
            ten_gods[f"藏干{i+1}" + h] = _get_ten_god(day_stem, h)
        
        # 五行统计
        wuxing_count[STEM_WUXING[stem]] += 1
        wuxing_count[BRANCH_WUXING[branch]] += 1
        for h in hidden:
            wuxing_count[STEM_WUXING[h]] += 1
        
        pillar_results[name] = PillarAnalysis(
            stem=stem,
            branch=branch,
            hidden=hidden,
            ten_gods=ten_gods,
            wuxing_stem=STEM_WUXING[stem],
            wuxing_branch=BRANCH_WUXING[branch],
        )
    
    # 日主强弱
    strength, score = _day_master_strength(day_stem, pillars, wuxing_count)
    
    # 十神全局统计
    god_counts = {}
    for p in pillar_results.values():
        for god in p.ten_gods.values():
            god_counts[god] = god_counts.get(god, 0) + 1
    
    # 用神推断
    favorable, unfavorable, fav_list, unfav_list = _determine_favorable(
        day_stem, strength, wuxing_count
    )
    
    # 格局提示
    pattern = _detect_pattern(day_stem, god_counts, strength)
    
    return BaziAnalysis(
        year=pillar_results["年"],
        month=pillar_results["月"],
        day=pillar_results["日"],
        hour=pillar_results["时"],
        day_master=day_stem,
        day_master_wuxing=STEM_WUXING[day_stem],
        day_master_strength=strength,
        day_master_score=score,
        ten_god_counts=god_counts,
        favorable_god=favorable,
        unfavorable_god=unfavorable,
        favorable_gods=fav_list,
        unfavorable_gods=unfav_list,
        pattern_hint=pattern,
        wuxing_balance=wuxing_count,
        four_pillars=pillars,
    )


# ════════════════════════════════════
# 十神计算
# ════════════════════════════════════

def _get_ten_god(day_stem: str, target_stem: str) -> str:
    """
    以日干为基准, 计算目标天干的十神.
    
    规则:
    - 同五行: 同阴阳=比肩, 异阴阳=劫财
    - 我生: 同阴阳=食神, 异阴阳=伤官
    - 我克: 同阴阳=偏财, 异阴阳=正财
    - 克我: 同阴阳=七杀, 异阴阳=正官
    - 生我: 同阴阳=偏印, 异阴阳=正印
    """
    dw = STEM_WUXING[day_stem]
    tw = STEM_WUXING[target_stem]
    same_yinyang = STEM_YINYANG[day_stem] == STEM_YINYANG[target_stem]
    
    if dw == tw:  # 同我
        return "比肩" if same_yinyang else "劫财"
    
    # 五行相生: 我生 → 食神/伤官
    if WUXING_SHENG.get(dw) == tw:
        return "食神" if same_yinyang else "伤官"
    
    # 我克 → 正财/偏财
    if WUXING_KE.get(dw) == tw:
        return "偏财" if same_yinyang else "正财"
    
    # 克我 → 七杀/正官
    for k, v in WUXING_KE.items():
        if v == dw and k == tw:
            return "七杀" if same_yinyang else "正官"
    
    # 生我 → 偏印/正印
    for k, v in WUXING_SHENG.items():
        if v == dw and k == tw:
            return "偏印" if same_yinyang else "正印"
    
    return "未知"


# ════════════════════════════════════
# 日主强弱
# ════════════════════════════════════

def _day_master_strength(
    day_stem: str,
    pillars: Dict[str, str],
    wuxing_count: Dict[str, int],
) -> Tuple[str, float]:
    """
    判断日主强弱.
    
    依据:
    1. 月令是否得令 (月支五行是否生日主五行)
    2. 全局五行分布
    3. 印星(生我)和比劫(同我)总数
    """
    dw = STEM_WUXING[day_stem]
    month_branch = pillars["月"][1]
    month_wx = BRANCH_WUXING[month_branch]
    
    score = 40.0  # 基准分
    
    # 得令: 月支五行生日主
    for k, v in WUXING_SHENG.items():
        if v == dw and k == month_wx:
            score += 25  # 月令生我, 强
            break
    else:
        if month_wx == dw:
            score += 15  # 月令同我
        elif WUXING_KE.get(month_wx) == dw:
            score -= 10  # 月令克我
        elif WUXING_SHENG.get(dw) == month_wx:
            score -= 5  # 我生月令 (泄)
    
    # 全局同五行和生我的五行占比
    support_wx = set()
    support_wx.add(dw)  # 同我
    for k, v in WUXING_SHENG.items():
        if v == dw:
            support_wx.add(k)  # 生我
    
    support_count = sum(wuxing_count.get(w, 0) for w in support_wx)
    total_count = sum(wuxing_count.values())
    
    if total_count > 0:
        ratio = support_count / total_count
        score += (ratio - 0.35) * 50
    
    score = max(10, min(95, score))
    
    if score >= 65:
        return "身强", score
    elif score >= 40:
        return "中和", score
    else:
        return "身弱", score


# ════════════════════════════════════
# 用神推断
# ════════════════════════════════════

def _determine_favorable(
    day_stem: str,
    strength: str,
    wuxing_count: Dict[str, int],
) -> Tuple[str, str, List[str], List[str]]:
    """
    推断用神/忌神.
    
    原则: 身强喜克泄耗, 身弱喜生扶
    """
    dw = STEM_WUXING[day_stem]
    dw_idx = ["木", "火", "土", "金", "水"].index(dw)
    
    # 生我者
    sheng_my = []
    for k, v in WUXING_SHENG.items():
        if v == dw:
            sheng_my.append(k)
    
    # 我生者
    wo_sheng = WUXING_SHENG.get(dw, "")
    
    # 克我者
    ke_my = []
    for k, v in WUXING_KE.items():
        if v == dw:
            ke_my.append(k)
    
    # 我克者
    wo_ke = WUXING_KE.get(dw, "")
    
    if strength == "身强":
        fav = [wo_sheng, wo_ke] + ke_my
        unfav = [dw] + sheng_my
    elif strength == "身弱":
        fav = [dw] + sheng_my
        unfav = [wo_sheng, wo_ke] + ke_my
    else:  # 中和
        fav = [dw, sheng_my[0] if sheng_my else ""]
        unfav = [wo_sheng, wo_ke]
    
    # 去空
    fav = [f for f in fav if f]
    unfav = [f for f in unfav if f]
    
    # 按当前八字中出现的频率调序
    fav.sort(key=lambda x: wuxing_count.get(x, 0), reverse=True)
    unfav.sort(key=lambda x: wuxing_count.get(x, 0), reverse=True)
    
    primary_fav = fav[0] if fav else "?"
    primary_unfav = unfav[0] if unfav else "?"
    
    return primary_fav, primary_unfav, fav, unfav


# ════════════════════════════════════
# 格局判断
# ════════════════════════════════════

def _detect_pattern(
    day_stem: str,
    god_counts: Dict[str, int],
    strength: str,
) -> str:
    """识别常见格局."""
    # 身强常见格局
    if strength == "身强":
        if god_counts.get("正官", 0) >= 2:
            return "正官格 — 身强喜官杀约束, 自律自控, 宜入公门或管理层"
        if god_counts.get("七杀", 0) >= 2:
            return "七杀格 — 身强以杀为权, 有魄力决断, 适合军警/外科/创业者"
        if god_counts.get("正财", 0) + god_counts.get("偏财", 0) >= 3:
            return "财格 — 身强财旺, 富贵可期, 宜经商理财"
        if god_counts.get("食神", 0) >= 2:
            return "食神格 — 才华横溢, 宜艺术/写作/设计"
        if god_counts.get("伤官", 0) >= 2:
            return "伤官格 — 聪慧机敏, 宜技术/创新领域"
    
    # 身弱常见格局
    if strength == "身弱":
        if god_counts.get("正印", 0) + god_counts.get("偏印", 0) >= 2:
            return "印绶格 — 身弱有印, 得长辈贵人扶持, 宜学术/教育/研究"
        if god_counts.get("比肩", 0) + god_counts.get("劫财", 0) >= 3:
            return "建禄格 — 比劫帮扶, 宜合作创业/团队协作"
    
    # 特殊格局
    if god_counts.get("七杀", 0) >= 3 and strength == "身弱":
        return "从杀格 — 特殊格局, 以杀为用, 逆境中崛起"
    if god_counts.get("正财", 0) + god_counts.get("偏财", 0) >= 4 and strength == "身弱":
        return "从财格 — 弃命从财, 宜全力求财, 忌印比帮扶"
    
    if god_counts.get("七杀", 0) >= 1 and god_counts.get("食神", 0) >= 1:
        return "食神制杀 — 以才华化解压力, 变挑战为机遇"
    
    return "中和之格 — 八字平和, 大运为关键"


# ════════════════════════════════════
# 流年八字分析
# ════════════════════════════════════

def analyze_liunian_bazi(
    year: int,
    day_stem: str,
    year_branch_birth: str,
    bazi: BaziAnalysis,
) -> LiunianBazi:
    """
    以八字视角分析流年.
    
    Args:
        year: 流年
        day_stem: 命主日干
        year_branch_birth: 出生年年支
        bazi: 八字分析结果
    
    Returns:
        LiunianBazi
    """
    gz = year_ganzhi(year)
    y_stem, y_branch = gz[0], gz[1]
    
    # 流年天干十神
    stem_god = _get_ten_god(day_stem, y_stem)
    
    # 流年地支主气十神
    hidden = BRANCH_HIDDEN_STEMS.get(y_branch, [])
    main_hidden = hidden[0] if hidden else y_stem
    branch_god = _get_ten_god(day_stem, main_hidden)
    
    # 冲克日主
    day_master_clash = WUXING_KE.get(y_stem) == STEM_WUXING[day_stem]
    
    # 犯太岁
    tai_sui = (y_branch == year_branch_birth or 
              (EARTHLY_BRANCHES.index(y_branch) - EARTHLY_BRANCHES.index(year_branch_birth)) % 12 == 6)
    
    # 评分
    rating = _score_liunian_bazi(stem_god, branch_god, bazi, y_stem, day_master_clash)
    
    # 概述
    summary = _build_liunian_summary(stem_god, branch_god, day_master_clash, tai_sui, bazi.favorable_god)
    
    return LiunianBazi(
        year=year,
        year_ganzhi=gz,
        year_stem=y_stem,
        year_branch=y_branch,
        zodiac=ZODIAC.get(y_branch, ""),
        stem_ten_god=stem_god,
        branch_main_ten_god=branch_god,
        day_master_clash=day_master_clash,
        tai_sui_branch=tai_sui,
        rating=rating,
        summary=summary,
    )


def _score_liunian_bazi(
    stem_god: str,
    branch_god: str,
    bazi: BaziAnalysis,
    year_stem: str,
    day_master_clash: bool,
) -> int:
    """对流年评分."""
    score = 0
    
    # 吉十神
    good_gods = {"正印", "正财", "正官", "食神"}
    ok_gods = {"偏印", "偏财", "比肩"}
    bad_gods = {"七杀", "伤官", "劫财"}
    
    for god, base in [(stem_god, 2), (branch_god, 1)]:
        if god in good_gods:
            score += base
        elif god in ok_gods:
            score += base // 2
        elif god in bad_gods:
            score -= base
    
    # 流年干五行是喜神?
    yw = STEM_WUXING[year_stem]
    if yw in bazi.favorable_gods:
        score += 2
    elif yw in bazi.unfavorable_gods:
        score -= 2
    
    # 冲克日主
    if day_master_clash:
        score -= 3
    
    return max(-5, min(5, score))


def _build_liunian_summary(
    stem_god: str,
    branch_god: str,
    clash: bool,
    tai_sui: bool,
    favorable: str,
) -> str:
    """构建流年概述."""
    parts = []
    parts.append(f"天干{TEN_GOD_EMOJI.get(stem_god,'')}{stem_god}")
    parts.append(f"地支{TEN_GOD_EMOJI.get(branch_god,'')}{branch_god}")
    
    nature_s = TEN_GOD_NATURE.get(stem_god, "")
    nature_b = TEN_GOD_NATURE.get(branch_god, "")
    if nature_s:
        parts.append(f"天干: {nature_s}")
    if nature_b and nature_b != nature_s:
        parts.append(f"地支: {nature_b}")
    
    if clash:
        parts.append("⚠️ 流年天干冲克日主, 需特别谨慎")
    if tai_sui:
        parts.append("🔴 今年犯太岁, 宜低调守成")
    
    return " | ".join(parts)


def analyze_multi_years_bazi(
    bazi: BaziAnalysis,
    year_branch_birth: str,
    start_year: int,
    count: int = 3,
) -> List[LiunianBazi]:
    """分析多年八字流年."""
    results = []
    for y in range(start_year, start_year + count):
        results.append(analyze_liunian_bazi(
            y, bazi.day_master, year_branch_birth, bazi
        ))
    return results


# ════════════════════════════════════
# 序列化
# ════════════════════════════════════

def bazi_to_dict(analysis: BaziAnalysis) -> dict:
    """Bazi分析转为字典."""
    def pillar_to_dict(p: PillarAnalysis) -> dict:
        return {
            "stem": p.stem,
            "branch": p.branch,
            "hidden": p.hidden,
            "ten_gods": p.ten_gods,
            "wuxing_stem": p.wuxing_stem,
            "wuxing_branch": p.wuxing_branch,
        }
    
    return {
        "year": pillar_to_dict(analysis.year),
        "month": pillar_to_dict(analysis.month),
        "day": pillar_to_dict(analysis.day),
        "hour": pillar_to_dict(analysis.hour),
        "day_master": analysis.day_master,
        "day_master_wuxing": analysis.day_master_wuxing,
        "day_master_strength": analysis.day_master_strength,
        "day_master_score": round(analysis.day_master_score, 1),
        "ten_god_counts": analysis.ten_god_counts,
        "favorable_god": analysis.favorable_god,
        "unfavorable_god": analysis.unfavorable_god,
        "favorable_gods": analysis.favorable_gods,
        "unfavorable_gods": analysis.unfavorable_gods,
        "pattern_hint": analysis.pattern_hint,
        "wuxing_balance": analysis.wuxing_balance,
        "four_pillars": analysis.four_pillars,
    }


def liunian_bazi_to_dict(l: LiunianBazi) -> dict:
    """流年分析转为字典."""
    return {
        "year": l.year,
        "year_ganzhi": l.year_ganzhi,
        "year_stem": l.year_stem,
        "year_branch": l.year_branch,
        "zodiac": l.zodiac,
        "stem_ten_god": l.stem_ten_god,
        "branch_main_ten_god": l.branch_main_ten_god,
        "day_master_clash": l.day_master_clash,
        "tai_sui_branch": l.tai_sui_branch,
        "rating": l.rating,
        "summary": l.summary,
        "ten_god_emoji": TEN_GOD_EMOJI.get(l.stem_ten_god, "?"),
    }
