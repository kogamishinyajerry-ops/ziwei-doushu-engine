"""
合盘分析引擎 — Compatibility Analysis Engine

两人命盘合婚分析:
- 生肖年支合婚
- 八字四柱配对
- 命宫/身宫/夫妻宫合盘
- 五行局相生克
- 星曜共享度与投射分析
- 四化飞星互动
- 综合评分 & 详细解读
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from ..calendar.constants import (
    EARTHLY_BRANCHES, HEAVENLY_STEMS, ZODIAC,
    OPPOSITE_PALACE, PALACE_NAMES,
    SIHUA_NAMES,
)

# ═══════════════════════════════════════════════════
# 数据模型
# ═══════════════════════════════════════════════════

@dataclass
class HepanDimension:
    """合盘单维度分析."""
    name: str           # 维度名称
    score: int          # 1-5 星
    label: str          # 评价标签
    good: List[str]     # 有利因素
    bad: List[str]      # 不利因素
    detail: str         # 详细解读


@dataclass
class HepanResult:
    """合盘完整结果."""
    person1: dict           # 命主1基本信息
    person2: dict           # 命主2基本信息
    dimensions: List[HepanDimension]  # 各维度分析
    total_score: int        # 总分 10-50
    total_stars: int        # 星级 1-5
    summary: str            # 总结
    verdict: str            # 一句话判词
    compatibility_tags: List[str]  # 配对标签
    shared_stars: List[dict]       # 共享星曜
    sihua_interactions: List[dict] # 四化互动
    key_strengths: List[str]       # 核心优势
    key_challenges: List[str]      # 核心挑战


# ═══════════════════════════════════════════════════
# 主分析函数
# ═══════════════════════════════════════════════════

def analyze_hepan(
    chart1: dict,
    chart2: dict,
) -> HepanResult:
    """
    两人命盘合盘分析.
    
    Args:
        chart1: chart_to_dict(chart, include_analysis=True) 输出
        chart2: 同上
    
    Returns:
        HepanResult 完整合盘分析
    """
    result = HepanResult(
        person1={
            "name": chart1.get("name", "命主甲"),
            "gender": chart1.get("gender", ""),
            "birth_date": chart1.get("birth_date", ""),
            "zodiac": chart1.get("zodiac", ""),
            "ming_palace": chart1.get("ming_palace", ""),
            "wuxing_ju": chart1.get("wuxing_ju", ""),
        },
        person2={
            "name": chart2.get("name", "命主乙"),
            "gender": chart2.get("gender", ""),
            "birth_date": chart2.get("birth_date", ""),
            "zodiac": chart2.get("zodiac", ""),
            "ming_palace": chart2.get("ming_palace", ""),
            "wuxing_ju": chart2.get("wuxing_ju", ""),
        },
        dimensions=[],
        total_score=0,
        total_stars=0,
        summary="",
        verdict="",
        compatibility_tags=[],
        shared_stars=[],
        sihua_interactions=[],
        key_strengths=[],
        key_challenges=[],
    )

    # ── 预处理 ──
    palaces1 = {p["name"]: p for p in chart1.get("palaces", [])} if chart1.get("palaces") else {}
    palaces2 = {p["name"]: p for p in chart2.get("palaces", [])} if chart2.get("palaces") else {}
    fp1 = chart1.get("four_pillars", {})
    fp2 = chart2.get("four_pillars", {})

    main_stars_set = {"紫微","天机","太阳","武曲","天同","廉贞",
                      "天府","太阴","贪狼","巨门","天相","天梁","七杀","破军"}

    # ── 维度一: 生肖合婚 ──
    dim_zodiac = _analyze_zodiac(chart1.get("zodiac", ""), chart2.get("zodiac", ""))
    result.dimensions.append(dim_zodiac)

    # ── 维度二: 四柱配对 ──
    dim_pillars = _analyze_four_pillars(fp1, fp2)
    result.dimensions.append(dim_pillars)

    # ── 维度三: 命宫合婚 ──
    dim_ming = _analyze_ming_palace(chart1, chart2, palaces1, palaces2)
    result.dimensions.append(dim_ming)

    # ── 维度四: 五行局 ──
    dim_wuxing = _analyze_wuxing_ju(chart1.get("wuxing_ju", ""), chart2.get("wuxing_ju", ""))
    result.dimensions.append(dim_wuxing)

    # ── 维度五: 身宫 ──
    dim_shen = _analyze_shen_palace(chart1, chart2, palaces1, palaces2)
    result.dimensions.append(dim_shen)

    # ── 维度六: 夫妻宫-命宫投射 ──
    dim_projection = _analyze_fuqi_ming_projection(palaces1, palaces2, main_stars_set)
    result.dimensions.append(dim_projection)

    # ── 维度七: 四化互动 ──
    dim_sihua = _analyze_sihua_interaction(chart1, chart2, palaces1, palaces2, main_stars_set)
    result.dimensions.append(dim_sihua)

    # ── 星曜共享分析 ──
    result.shared_stars = _analyze_shared_stars(palaces1, palaces2, main_stars_set)

    # ── 四化详细互动 ──
    result.sihua_interactions = _build_sihua_interactions(chart1, chart2, palaces1, palaces2)

    # ── 综合评分 ──
    scores = [d.score for d in result.dimensions]
    result.total_score = sum(scores)
    avg_score = result.total_score / len(scores)
    result.total_stars = _score_to_stars(avg_score)

    # ── 标签 ──
    tags = []
    if dim_zodiac.score >= 4:
        tags.append("生肖六合")
    elif dim_zodiac.score >= 3:
        tags.append("生肖相合")
    if dim_projection.score >= 4:
        tags.append("命定之缘")
    if dim_wuxing.score >= 4:
        tags.append("五行相生")
    if len(result.shared_stars) >= 5:
        tags.append("星曜密织")
    if dim_shen.score >= 4:
        tags.append("白头偕老")
    result.compatibility_tags = tags

    # ── 核心优势/挑战 ──
    for d in result.dimensions:
        if d.score >= 4:
            result.key_strengths.append(f"{d.name}({d.score}星): {d.label}")
        elif d.score <= 2:
            result.key_challenges.append(f"{d.name}({d.score}星): {d.label}")

    # ── 判词与总结 ──
    result.verdict = _generate_verdict(result)
    result.summary = _generate_summary(result)

    return result


# ═══════════════════════════════════════════════════
# 各维度分析
# ═══════════════════════════════════════════════════

def _analyze_zodiac(z1: str, z2: str) -> HepanDimension:
    """生肖合婚分析."""
    # 地支映射
    zodiac_to_branch = {
        "鼠":"子","牛":"丑","虎":"寅","兔":"卯",
        "龙":"辰","蛇":"巳","马":"午","羊":"未",
        "猴":"申","鸡":"酉","狗":"戌","猪":"亥",
    }
    b1 = zodiac_to_branch.get(z1, "")
    b2 = zodiac_to_branch.get(z2, "")

    # 六合
    liuhe = {"子":"丑","丑":"子","寅":"亥","亥":"寅","卯":"戌","戌":"卯",
             "辰":"酉","酉":"辰","巳":"申","申":"巳","午":"未","未":"午"}

    # 三合
    sanhe_groups = [
        {"申","子","辰"}, {"亥","卯","未"}, {"寅","午","戌"}, {"巳","酉","丑"}
    ]

    # 六冲
    liuchong = {"子":"午","午":"子","丑":"未","未":"丑","寅":"申","申":"寅",
                "卯":"酉","酉":"卯","辰":"戌","戌":"辰","巳":"亥","亥":"巳"}

    # 六害
    liuhai = {"子":"未","未":"子","丑":"午","午":"丑","寅":"巳","巳":"寅",
              "卯":"辰","辰":"卯","申":"亥","亥":"申","酉":"戌","戌":"酉"}

    good, bad = [], []

    # 六合
    if liuhe.get(b1) == b2:
        good.append(f"{z1}{z2}六合，天地之配，最理想的生肖组合")
        return HepanDimension("生肖年支", 5, "天作之合",
                              good, bad,
                              f"{z1}({b1})与{z2}({b2})为六合关系，十二生肖中最强的配对组合。两人气场天然和谐，互相吸引，相处融洽。")

    # 三合
    for group in sanhe_groups:
        if b1 in group and b2 in group:
            good.append(f"{z1}{z2}三合半合，志趣相投，互相扶持")
            return HepanDimension("生肖年支", 4, "佳偶天成",
                                  good, bad,
                                  f"{z1}({b1})与{z2}({b2})同属三合局，感情基础牢固，价值观接近，是极佳的婚配。")

    # 同生肖
    if b1 == b2:
        return HepanDimension("生肖年支", 3, "同舟共济",
                              [f"{z1}{z2}同生肖，互相理解但也容易互不相让"],
                              [],
                              f"两人同属{z1}({b1})，有相似的处事风格和价值观。但需注意双方都强势时容易产生摩擦。")

    # 六冲
    if liuchong.get(b1) == b2:
        bad.append(f"{z1}{z2}六冲，性格对立，矛盾较多")
        return HepanDimension("生肖年支", 1, "先冲后合",
                              [f"冲也为动，若彼此包容可转化为互补"],
                              bad,
                              f"{z1}({b1})与{z2}({b2})六冲，性格和处事方式差异极大。虽有吸引力但冲突明显，需要极大的包容和磨合。")

    # 六害
    if liuhai.get(b1) == b2:
        bad.append(f"{z1}{z2}六害，暗中不和，容易互相消耗")
        return HepanDimension("生肖年支", 1, "暗礁潜伏",
                              [],
                              bad,
                              f"{z1}({b1})与{z2}({b2})六害，看似无大冲突但暗中相互消耗，长期相处需警惕情感磨损。")

    # 其他
    return HepanDimension("生肖年支", 2, "平和普通",
                          [],
                          [f"{z1}{z2}无特殊合冲关系，生肖层面影响不大"],
                          f"{z1}({b1})与{z2}({b2})无六合六冲关系，生肖层面中性，需结合其他维度综合判断。")


def _analyze_four_pillars(fp1: dict, fp2: dict) -> HepanDimension:
    """八字四柱配对分析."""
    good, bad = [], []
    detail_parts = []
    pillar_score = 0

    pillars = [
        ("年柱", "year"),
        ("月柱", "month"),
        ("日柱", "day"),
        ("时柱", "hour"),
    ]

    liuchong = {"子":"午","午":"子","丑":"未","未":"丑","寅":"申","申":"寅",
                "卯":"酉","酉":"卯","辰":"戌","戌":"辰","巳":"亥","亥":"巳"}
    liuhe = {"子":"丑","丑":"子","寅":"亥","亥":"寅","卯":"戌","戌":"卯",
             "辰":"酉","酉":"辰","巳":"申","申":"巳","午":"未","未":"午"}

    for pname, pkey in pillars:
        gz1 = fp1.get(pkey, "")
        gz2 = fp2.get(pkey, "")
        if len(gz1) >= 2 and len(gz2) >= 2:
            stem1, branch1 = gz1[0], gz1[1]
            stem2, branch2 = gz2[0], gz2[1]

            # 地支关系
            if liuhe.get(branch1) == branch2:
                good.append(f"{pname}{gz1}vs{gz2}地支六合")
                pillar_score += 2
                detail_parts.append(f"{pname}{gz1}与{gz2}地支六合，此柱能量和谐。")
            elif liuchong.get(branch1) == branch2:
                bad.append(f"{pname}{gz1}vs{gz2}地支六冲")
                pillar_score -= 1
                detail_parts.append(f"{pname}{gz1}与{gz2}地支六冲，此柱存在根本分歧。")
            elif branch1 == branch2:
                good.append(f"{pname}{gz1}vs{gz2}地支相同")
                pillar_score += 1
                detail_parts.append(f"{pname}{gz1}与{gz2}地支相同，此柱步调一致。")
            else:
                # 天干关系
                stem_rel = _stem_relation(stem1, stem2)
                if "克" in stem_rel:
                    bad.append(f"{pname}天干{stem1}克{stem2}")
                    pillar_score -= 0.5
                elif stem1 == stem2:
                    pillar_score += 0.5

    # 评分映射
    if pillar_score >= 5:
        score, label = 5, "四柱和谐"
    elif pillar_score >= 2:
        score, label = 4, "大体相合"
    elif pillar_score >= 0:
        score, label = 3, "有合有冲"
    elif pillar_score >= -2:
        score, label = 2, "冲合参半"
    else:
        score, label = 1, "多柱相冲"

    detail = "\n".join(detail_parts) if detail_parts else "四柱无特殊组合。"
    return HepanDimension("八字四柱", score, label, good, bad, detail)


def _analyze_ming_palace(chart1, chart2, palaces1, palaces2) -> HepanDimension:
    """命宫合婚分析."""
    good, bad = [], []
    detail_parts = []

    ming1 = chart1.get("ming_palace", "")
    ming2 = chart2.get("ming_palace", "")

    main_set = {"紫微","天机","太阳","武曲","天同","廉贞",
                "天府","太阴","贪狼","巨门","天相","天梁","七杀","破军"}

    ming_stars1 = [s for s in palaces1.get("命宫", {}).get("stars", []) if s in main_set]
    ming_stars2 = [s for s in palaces2.get("命宫", {}).get("stars", []) if s in main_set]

    # 地支关系
    if len(ming1) >= 2 and len(ming2) >= 2:
        b1, b2 = ming1[1], ming2[1]

        liuhe = {"子":"丑","丑":"子","寅":"亥","亥":"寅","卯":"戌","戌":"卯",
                 "辰":"酉","酉":"辰","巳":"申","申":"巳","午":"未","未":"午"}
        liuhai = {"子":"未","未":"子","丑":"午","午":"丑","寅":"巳","巳":"寅",
                  "卯":"辰","辰":"卯","申":"亥","亥":"申","酉":"戌","戌":"酉"}
        liuchong = {"子":"午","午":"子","丑":"未","未":"丑","寅":"申","申":"寅",
                    "卯":"酉","酉":"卯","辰":"戌","戌":"辰","巳":"亥","亥":"巳"}

        if liuhe.get(b1) == b2:
            good.append(f"命宫{b1}{b2}六合，天性契合度高")
            detail_parts.append(f"命宫{b1}与{b2}六合，两人天性相投，相处融洽。")
        elif liuhai.get(b1) == b2:
            bad.append(f"命宫{b1}{b2}六害，本质性格有冲突")
            detail_parts.append(f"命宫{b1}与{b2}六害，两人有深层的性格差异，需要更多理解和包容。")
        elif liuchong.get(b1) == b2:
            bad.append(f"命宫{b1}{b2}六冲，行事风格对立")
            detail_parts.append(f"命宫{b1}与{b2}六冲，行事风格截然不同。初期可能有强烈吸引，但长期相处摩擦较大。")
        elif b1 == b2:
            good.append(f"命宫同坐{b1}，想法一致")
            detail_parts.append(f"命宫同临{b1}地支，两人思维模式相似，容易达成一致。")
        else:
            detail_parts.append(f"命宫{b1}与{b2}无特殊冲合关系。")

    # 星曜
    shared_ming_stars = set(ming_stars1) & set(ming_stars2)
    if shared_ming_stars:
        good.append(f"命宫共有{'、'.join(shared_ming_stars)}，性格共鸣")
        detail_parts.append(f"两人命宫共有{'、'.join(shared_ming_stars)}，这是极强的性格共鸣信号。")
    elif ming_stars1 and ming_stars2:
        detail_parts.append(f"命宫主星{'、'.join(ming_stars1)}与{'、'.join(ming_stars2)}各有特色，性格互补或互补冲突并存。")

    # 评分
    n_good = len(good)
    n_bad = len(bad)
    if n_good >= 2 and n_bad == 0:
        score, label = 5, "心灵相通"
    elif n_good >= 1 and n_bad == 0:
        score, label = 4, "性格相投"
    elif n_good >= 1 and n_bad >= 1:
        score, label = 3, "有合有克"
    elif n_good == 0 and n_bad == 1:
        score, label = 2, "性格分歧"
    elif n_bad >= 2:
        score, label = 1, "水火难容"
    else:
        score, label = 3, "中规中矩"

    return HepanDimension("命宫合配", score, label, good, bad,
                          "；".join(detail_parts) if detail_parts else "命宫无显著互动。")


def _analyze_wuxing_ju(wx1: str, wx2: str) -> HepanDimension:
    """五行局相生克分析."""
    # 提取五行和局数
    element_map = {"水":0,"木":1,"火":2,"土":3,"金":4}
    wx_name1 = wx1[0] if wx1 else ""
    wx_name2 = wx2[0] if wx2 else ""

    e1 = element_map.get(wx_name1, -1)
    e2 = element_map.get(wx_name2, -1)

    if e1 < 0 or e2 < 0:
        return HepanDimension("五行局", 3, "未知", [], [], "五行局数据不足。")

    # 生克关系
    # 相生: (生者, 被生者) 相差1 (木生火, 火生土, 土生金, 金生水, 水生木)
    e1_sheng_e2 = (e1 + 1) % 5 == e2
    e2_sheng_e1 = (e2 + 1) % 5 == e1

    e1_ke_e2 = (e1 + 2) % 5 == e2
    e2_ke_e1 = (e2 + 2) % 5 == e1

    if e1 == e2:
        return HepanDimension("五行局", 3, "同气相求",
                              [f"{wx1}={wx2}，五行相同"],
                              ["同五行可能缺乏互补性"],
                              f"两人同为{wx_name1}局，性格和节奏相近。优势在于互相理解，但可能缺少互补的张力。")

    if e1_sheng_e2:
        return HepanDimension("五行局", 5, "天作之合",
                              [f"{wx1}生{wx2}，命主1旺命主2"],
                              [],
                              f"{wx1}生{wx2}，五行相生顺遂。命主1的能量滋养命主2，在传统合婚中这是上等配置——给予方心甘情愿，接受方如沐春风。")

    if e2_sheng_e1:
        return HepanDimension("五行局", 4, "良缘相生",
                              [f"{wx2}生{wx1}，命主2旺命主1"],
                              [],
                              f"{wx2}生{wx1}，五行逆行相生。命主2滋养命主1，虽然方向非传统但效果不减。两人能量互补，互相成就。")

    if e1_ke_e2:
        return HepanDimension("五行局", 2, "相克耗能",
                              [],
                              [f"{wx1}克{wx2}，命主1消耗命主2"],
                              f"{wx1}克{wx2}，命主1的能量压制命主2。长期相处命主2可能感到压抑和消耗，需命主1有意识地收敛和关心对方。")

    if e2_ke_e1:
        return HepanDimension("五行局", 2, "逆克需调",
                              [],
                              [f"{wx2}克{wx1}，命主2消耗命主1"],
                              f"{wx2}克{wx1}，命主2强势克制命主1。需命主2学会包容退让，否则命主1容易感到压抑。")

    return HepanDimension("五行局", 3, "中平", [], [], "五行无特殊生克。")


def _analyze_shen_palace(chart1, chart2, palaces1, palaces2) -> HepanDimension:
    """身宫合盘分析 — 身宫主后半生."""
    shen_palace1 = chart1.get("shen_palace", "")
    shen_palace2 = chart2.get("shen_palace", "")

    if len(shen_palace1) < 2 or len(shen_palace2) < 2:
        return HepanDimension("身宫合配", 3, "数据不足", [], [], "身宫数据不完整。")

    b1, b2 = shen_palace1[1], shen_palace2[1]

    liuhe = {"子":"丑","丑":"子","寅":"亥","亥":"寅","卯":"戌","戌":"卯",
             "辰":"酉","酉":"辰","巳":"申","申":"巳","午":"未","未":"午"}
    liuchong = {"子":"午","午":"子","丑":"未","未":"丑","寅":"申","申":"寅",
                "卯":"酉","酉":"卯","辰":"戌","戌":"辰","巳":"亥","亥":"巳"}

    if liuhe.get(b1) == b2:
        return HepanDimension("身宫合配", 5, "白头偕老",
                              [f"身宫{b1}{b2}六合，越老越默契"],
                              [],
                              f"身宫主后半生命运走向。两人身宫{b1}与{b2}六合，意味着随着时间推移，默契和情感深度会持续增长。是'先磨合，后契合'的经典信号。")

    if liuchong.get(b1) == b2:
        return HepanDimension("身宫合配", 2, "晚年分歧",
                              [],
                              [f"身宫{b1}{b2}六冲，晚年可能各走各路"],
                              f"身宫{b1}与{b2}六冲，意味着两人后半生的重心和追求可能分道扬镳。需要在中年前建立起牢固的共识和共同目标。")

    if b1 == b2:
        return HepanDimension("身宫合配", 4, "同心同德",
                              [f"身宫同坐{b1}，人生方向一致"],
                              [],
                              f"身宫同位{b1}，两人后半生的追求和重心高度一致，是伴侣也是战友。")

    return HepanDimension("身宫合配", 3, "各行其道",
                          [],
                          [],
                          f"身宫{b1}与{b2}无显著冲合，后半生的方向各自发展，互不冲突也互不强化。")


def _analyze_fuqi_ming_projection(palaces1, palaces2, main_set) -> HepanDimension:
    """夫妻宫 ↔ 命宫投射分析."""
    good, bad = [], []
    detail_parts = []

    # 命主1的夫妻宫星 → 命主2的命宫
    fuqi1_stars = [s for s in palaces1.get("夫妻", {}).get("stars", []) if s in main_set]
    ming2_stars = [s for s in palaces2.get("命宫", {}).get("stars", []) if s in main_set]
    proj1_to_2 = set(fuqi1_stars) & set(ming2_stars)

    # 命主2的夫妻宫星 → 命主1的命宫
    fuqi2_stars = [s for s in palaces2.get("夫妻", {}).get("stars", []) if s in main_set]
    ming1_stars = [s for s in palaces1.get("命宫", {}).get("stars", []) if s in main_set]
    proj2_to_1 = set(fuqi2_stars) & set(ming1_stars)

    if proj1_to_2:
        good.append(f"命主1的配偶星{'、'.join(proj1_to_2)}出现在命主2命宫")
        detail_parts.append(f"命主1命盘中的理想伴侣特质（夫妻宫{'、'.join(proj1_to_2)}），精准投射到命主2的命宫。这意味着命主2天然符合命主1对伴侣的期待。")

    if proj2_to_1:
        good.append(f"命主2的配偶星{'、'.join(proj2_to_1)}出现在命主1命宫")
        detail_parts.append(f"命主2命盘中的理想伴侣特质（夫妻宫{'、'.join(proj2_to_1)}），精准投射到命主1的命宫。这是双向的命定之缘信号。")

    if proj1_to_2 and proj2_to_1:
        return HepanDimension("夫妻-命宫投射", 5, "命中注定",
                              list(good), [],
                              "双向投射——两颗命盘的配偶原型精准落入对方的命宫。这是合盘中最强的缘分信号之一，不是普通相遇，是命盘结构层面的共振。")

    if proj1_to_2 or proj2_to_1:
        return HepanDimension("夫妻-命宫投射", 4, "一方情深",
                              list(good), [],
                              "；".join(detail_parts) + "虽为单向投射，但已是相当难得的缘分信号。")

    # 没有投射但检查夫妻宫是否有共有星曜
    fuqi_shared = set(fuqi1_stars) & set(fuqi2_stars)
    if fuqi_shared:
        return HepanDimension("夫妻-命宫投射", 3, "夫妻星同源",
                              [f"双方夫妻宫共有{'、'.join(fuqi_shared)}"],
                              [],
                              f"两人夫妻宫共有{'、'.join(fuqi_shared)}，意味着对婚姻的期待和模式相近。虽不如正投射强烈，但也是良好的配对基础。")

    return HepanDimension("夫妻-命宫投射", 2, "各自独立",
                          [],
                          [],
                          "双方夫妻宫的星曜没有直接投射到对方命宫。婚姻关系的建立更多依赖后天磨合和经营，而非先天命盘的共振。")


def _analyze_sihua_interaction(chart1, chart2, palaces1, palaces2, main_set) -> HepanDimension:
    """四化飞星互动分析."""
    good, bad = [], []
    sihua1 = chart1.get("sihua", {})
    sihua2 = chart2.get("sihua", {})

    # 找出对方四化星在命盘中的对应
    interactions = []

    for stype1, star1 in sihua1.items():
        # 找star1在chart2中的位置
        for pname, pdata in palaces2.items():
            if star1 in pdata.get("stars", []):
                interactions.append((star1, stype1, pname, "1→2"))

    for stype2, star2 in sihua2.items():
        for pname, pdata in palaces1.items():
            if star2 in pdata.get("stars", []):
                interactions.append((star2, stype2, pname, "2→1"))

    score = 3
    for star, stype, palace, direction in interactions:
        if stype in ("化禄", "化权", "化科"):
            good.append(f"{star}{stype}→{'对方' if direction.startswith('1') else '命主1'}{palace}")
            score += 0.5
        elif stype == "化忌":
            bad.append(f"{star}化忌冲击{'对方' if direction.startswith('1') else '命主1'}{palace}")
            score -= 0.5

    score = max(1, min(5, int(score)))

    if score >= 4:
        label = "四化和谐"
    elif score == 3:
        label = "有吉有忌"
    else:
        label = "忌星冲击"

    detail = "四化能量流在两人命盘间的交互情况。"
    if good:
        detail += f" 有利流:{'; '.join(good)}。"
    if bad:
        detail += f" 需注意:{'; '.join(bad)}。"

    return HepanDimension("四化互动", score, label, good, bad, detail)


# ═══════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════

def _analyze_shared_stars(palaces1, palaces2, main_set) -> List[dict]:
    """分析星曜共享度."""
    shared = []
    for pname in PALACE_NAMES:
        stars1 = set(palaces1.get(pname, {}).get("stars", []))
        stars2 = set(palaces2.get(pname, {}).get("stars", []))
        # 只在主星层面做共享
        mains1 = stars1 & main_set
        mains2 = stars2 & main_set
        shared_mains = mains1 & mains2
        shared_aux = (stars1 & stars2) - main_set

        if shared_mains or shared_aux:
            shared.append({
                "palace": pname,
                "shared_mains": list(shared_mains),
                "shared_aux": list(shared_aux),
                "significance": _shared_significance(pname, len(shared_mains)),
            })
    return shared


def _shared_significance(palace: str, count: int) -> str:
    """星曜共享的解读."""
    sigs = {
        "命宫": "两人命宫共有星曜，性格深刻共鸣，似曾相识的熟悉感。",
        "夫妻": "夫妻宫共用星曜，对婚姻的期待和模式惊人一致。",
        "官禄": "事业追求和职业风格有共同点，是工作上的好搭档。",
        "福德": "精神世界相通，能深入理解对方的内心。",
        "迁移": "对外处事方式接近，社交场合配合默契。",
    }
    if count >= 1:
        return sigs.get(palace, f"{palace}共有{count}星，此领域有天然默契。")
    return ""


def _build_sihua_interactions(chart1, chart2, palaces1, palaces2) -> List[dict]:
    """构建四化互动详情."""
    result = []
    sihua1 = chart1.get("sihua", {})
    sihua2 = chart2.get("sihua", {})

    for stype, star in sihua1.items():
        for pname, pdata in palaces2.items():
            if star in pdata.get("stars", []):
                impact = "吉" if stype in ("化禄","化权","化科") else "忌"
                result.append({
                    "from": chart1.get("name", "命主1"),
                    "to": chart2.get("name", "命主2"),
                    "star": star,
                    "type": stype,
                    "palace": pname,
                    "impact": impact,
                })

    for stype, star in sihua2.items():
        for pname, pdata in palaces1.items():
            if star in pdata.get("stars", []):
                impact = "吉" if stype in ("化禄","化权","化科") else "忌"
                result.append({
                    "from": chart2.get("name", "命主2"),
                    "to": chart1.get("name", "命主1"),
                    "star": star,
                    "type": stype,
                    "palace": pname,
                    "impact": impact,
                })

    return result


def _stem_relation(s1: str, s2: str) -> str:
    """天干五行关系."""
    stem_wuxing = {
        "甲":"木","乙":"木","丙":"火","丁":"火",
        "戊":"土","己":"土","庚":"金","辛":"金","壬":"水","癸":"水",
    }
    w1 = stem_wuxing.get(s1, "")
    w2 = stem_wuxing.get(s2, "")

    generate = {"木":"火","火":"土","土":"金","金":"水","水":"木"}
    overcome = {"木":"土","土":"水","水":"火","火":"金","金":"木"}

    if w1 == w2:
        return "比和"
    if generate.get(w1) == w2:
        return f"{w1}生{w2}"
    if overcome.get(w1) == w2:
        return f"{w1}克{w2}"
    return ""


def _score_to_stars(avg_score: float) -> int:
    """平均分转星级."""
    if avg_score >= 4.5:
        return 5
    elif avg_score >= 3.5:
        return 4
    elif avg_score >= 2.5:
        return 3
    elif avg_score >= 1.5:
        return 2
    return 1


def _generate_verdict(result: HepanResult) -> str:
    """生成判词."""
    if result.total_stars == 5:
        return "天赐良缘，命中注定。两盘如水乳交融，是紫微斗数中最难得的配对之一。"
    elif result.total_stars == 4:
        return "良缘难得，值得托付。虽非完美无瑕，但强处远超弱处，用心经营必得善果。"
    elif result.total_stars == 3:
        return "有缘有份，亦有功课。吸引力与摩擦力并存，能否走得远取决于双方的包容与成长。"
    elif result.total_stars == 2:
        return "缘分在，但路不平。两人需要极大的理解和妥协，适合的前提是彼此愿意为对方改变。"
    else:
        return "命盘相冲较多，若在一起需要超出常人的毅力和包容心。建议深入了解后再做决定。"


def _generate_summary(result: HepanResult) -> str:
    """生成总结."""
    parts = []

    n_strength = len(result.key_strengths)
    n_challenge = len(result.key_challenges)

    if n_strength >= 4:
        parts.append(f"此对合盘整体表现出色，{n_strength}个维度展现出强契合信号。"
                     f"尤其是{result.key_strengths[0].split(':')[0]}表现突出。")
    elif n_strength >= 2:
        parts.append(f"合盘表现中上，{n_strength}个维度契合，{n_challenge}个维度需要磨合。")
    else:
        parts.append(f"合盘挑战较多，{n_challenge}个维度存在根本分歧。")

    if result.compatibility_tags:
        parts.append(f"配对特征: {'、'.join(result.compatibility_tags)}。")

    parts.append(f"综合评分: {result.total_score}/35 ★{'⭐' * result.total_stars}")

    # 核心建议
    if result.key_strengths and result.key_challenges:
        parts.append(f"核心优势在于{result.key_strengths[0].split(':')[0]}，"
                    f"需重点磨合的是{result.key_challenges[0].split(':')[0]}。")

    return "\n".join(parts)
