"""
流年分析引擎 — Yearly Fortune Analysis

紫微斗数流年体系:
1. 流年命宫: 太岁(年支)所在宫位
2. 流年四化: 流年天干触发的四化
3. 流年辅星: 流禄/流羊/流陀(流昌/流曲)
4. 与大限叠合: 大限宫 + 流年宫的交互影响
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field

from ..calendar.constants import (
    EARTHLY_BRANCHES, HEAVENLY_STEMS,
    PALACE_NAMES, OPPOSITE_PALACE,
    TRIAD_OFFSET, GAN_SIHUA_TABLE,
    SEXAGENARY_CYCLE, SIHUA_NAMES,
)


@dataclass
class LiunianInfo:
    """单个流年信息."""
    year: int               # 公历年
    year_ganzhi: str        # 流年干支
    year_stem: str          # 流年天干
    year_branch: str        # 流年地支
    zodiac: str             # 生肖
    
    # 流年命宫
    liunian_ming_palace: str       # 流年命宫名
    liunian_ming_branch: str       # 流年命宫地支
    
    # 流年四化 (流年天干决定)
    liunian_sihua: Dict[str, str]  # {星名: 四化类型}
    
    # 流年禄存/擎羊/陀罗
    liunian_lucun: str      # 流禄所在支
    liunian_qingyang: str   # 流羊所在支
    liunian_tuoluo: str     # 流陀所在支
    
    # 大限叠合
    daxian_palace: str = ""        # 当前大限所在的宫
    daxian_age_range: str = ""     # 大限年龄范围
    
    # 年龄
    age: int = 0


@dataclass  
class LiunianAnalysis:
    """流年解读结果."""
    year: int
    year_ganzhi: str
    overview: str           # 年度总览
    career: str             # 事业运势
    wealth: str             # 财运
    relationship: str       # 感情运势
    health: str             # 健康提示
    key_months: List[str]   # 关键月份
    rating: int             # 吉凶评分 (-5到+5)
    advice: str             # 年度建议


# ══════════════════════════════════════
# 流年计算核心
# ══════════════════════════════════════

def year_ganzhi(year: int) -> str:
    """计算指定公历年的干支."""
    return SEXAGENARY_CYCLE[(year - 4) % 60]


def calculate_liunian_info(
    year: int,
    chart_data,            # ChartData
    ming_index: int,        # 命宫地支索引
    palace_branch_map: Dict[str, int],  # {宫名: 地支索引}
) -> LiunianInfo:
    """
    计算指定年份的流年信息.
    
    Args:
        year: 目标公历年
        chart_data: 完整命盘
        ming_index: 命宫地支索引
        palace_branch_map: 十二宫→地支索引映射
    
    Returns:
        LiunianInfo
    """
    gz = year_ganzhi(year)
    stem = gz[0]
    branch = gz[1]
    
    # 流年命宫 = 太岁(年支)所在宫位
    branch_idx = EARTHLY_BRANCHES.index(branch)
    liunian_palace = None
    for pname, bidx in palace_branch_map.items():
        if bidx == branch_idx:
            liunian_palace = pname
            break
    
    if liunian_palace is None:
        # 降级: 查 PALACE_NAMES
        offset = (branch_idx - ming_index) % 12
        liunian_palace = PALACE_NAMES[(12 - offset) % 12]
    
    # 流年四化 = 流年天干决定的四化
    liunian_sihua = dict(GAN_SIHUA_TABLE.get(stem, {}))
    
    # 流年禄存 (根据流年天干)
    lucun_map = {
        "甲": "寅", "乙": "卯", "丙": "巳", "丁": "午",
        "戊": "巳", "己": "午", "庚": "申", "辛": "酉",
        "壬": "亥", "癸": "子",
    }
    lucun_branch = lucun_map.get(stem, "寅")
    lucun_idx = EARTHLY_BRANCHES.index(lucun_branch)
    
    # 流年擎羊 = 流禄前一位
    qingyang_idx = (lucun_idx + 1) % 12
    # 流年陀罗 = 流禄后一位
    tuoluo_idx = (lucun_idx - 1) % 12
    
    # 大限信息
    birth_year = chart_data.birth_date.split("-")[0] if chart_data.birth_date else "1990"
    age = year - int(birth_year)
    
    daxian_palace = ""
    daxian_range = ""
    for pname, dx_str in chart_data.daxian.items():
        if "-" in dx_str:
            parts = dx_str.split("-")
            try:
                start = int(parts[0])
                end = int(parts[1].replace("岁", ""))
                if start <= age <= end:
                    daxian_palace = pname
                    daxian_range = dx_str
                    break
            except ValueError:
                pass
    
    # 生肖
    from ..calendar.constants import ZODIAC
    zodiac = ZODIAC.get(branch, "")
    
    return LiunianInfo(
        year=year,
        year_ganzhi=gz,
        year_stem=stem,
        year_branch=branch,
        zodiac=zodiac,
        liunian_ming_palace=liunian_palace,
        liunian_ming_branch=branch,
        liunian_sihua=liunian_sihua,
        liunian_lucun=lucun_branch,
        liunian_qingyang=EARTHLY_BRANCHES[qingyang_idx],
        liunian_tuoluo=EARTHLY_BRANCHES[tuoluo_idx],
        daxian_palace=daxian_palace,
        daxian_age_range=daxian_range,
        age=age,
    )


# ══════════════════════════════════════
# 流年解读生成
# ══════════════════════════════════════

def _rate_liunian(liunian: LiunianInfo, palace_stars: Dict[str, List[str]]) -> int:
    """对流年进行吉凶评分."""
    rating = 0
    mp = liunian.liunian_ming_palace
    stars = palace_stars.get(mp, [])
    
    # 吉星加分
    ji_stars = {"文昌","文曲","左辅","右弼","天魁","天钺","禄存","天马"}
    rating += sum(2 for s in stars if s in ji_stars)
    
    # 煞星减分
    sha_stars = {"擎羊","陀罗","火星","铃星","地劫","地空"}
    rating -= sum(2 for s in stars if s in sha_stars)
    
    # 流年四化在流年命宫
    for star, stype in liunian.liunian_sihua.items():
        if star in stars:
            if stype == "化禄": rating += 3
            elif stype == "化权": rating += 2
            elif stype == "化科": rating += 2
            elif stype == "化忌": rating -= 3
    
    # 禄存/擎羊/陀罗位置影响
    mp_branch = liunian.liunian_ming_branch
    if liunian.liunian_lucun == mp_branch: rating += 3
    if liunian.liunian_qingyang == mp_branch: rating -= 2
    if liunian.liunian_tuoluo == mp_branch: rating -= 2
    
    return max(-5, min(5, rating))


def analyze_liunian(
    liunian: LiunianInfo,
    palace_stars: Dict[str, List[str]],
    sihua_map: Dict[str, str],
    chart_data,
) -> LiunianAnalysis:
    """
    生成流年详细解读.
    
    Args:
        liunian: 流年信息
        palace_stars: {宫名: [星曜列表]}
        sihua_map: 生年四化
        chart_data: 完整命盘
    
    Returns:
        LiunianAnalysis
    """
    mp = liunian.liunian_ming_palace
    mp_stars = palace_stars.get(mp, [])
    rating = _rate_liunian(liunian, palace_stars)
    
    # ── 年度总览 ──
    overview_parts = []
    overview_parts.append(f"{liunian.year}年({liunian.year_ganzhi}年, 生肖{liunian.zodiac}), 流年命宫在{mp}。")
    
    if liunian.daxian_palace:
        overview_parts.append(f"当前大限在{liunian.daxian_palace}({liunian.daxian_age_range}), 与流年宫{mp}叠合。")
    
    # 流年四化简述
    sihua_brief = []
    for star, stype in liunian.liunian_sihua.items():
        sihua_brief.append(f"{star}{stype}")
    if sihua_brief:
        overview_parts.append(f"流年四化: {'、'.join(sihua_brief)}")
    
    if rating >= 4:
        overview_parts.append("此年为吉运之年, 机遇较多, 宜积极进取。")
    elif rating >= 2:
        overview_parts.append("此年为平稳发展之年, 宜稳扎稳打。")
    elif rating >= 0:
        overview_parts.append("此年为中平之年, 喜忧参半, 需灵活应对。")
    elif rating >= -2:
        overview_parts.append("此年多有波折, 宜守不宜攻, 谨慎行事。")
    else:
        overview_parts.append("此年挑战较多, 宜韬光养晦, 以待时机。")
    
    overview = "\n".join(overview_parts)
    
    # ── 事业运势 ──
    career_parts = []
    guanlu = palace_stars.get("官禄", [])
    if guanlu:
        career_parts.append(f"官禄宫{'、'.join(guanlu[:3])}影响事业发展基调。")
    
    # 检查流年禄存在官禄宫
    mp_branch = liunian.liunian_ming_branch
    gl_branch = None
    for pname, bidx in {}:  # will be filled
        pass
    
    # 简化: 检查流年四化是否影响事业宫
    for star, stype in liunian.liunian_sihua.items():
        if star in guanlu:
            if stype == "化禄":
                career_parts.append(f"流年{star}化禄入官禄宫, 事业上有良好机遇, 宜把握。")
            elif stype == "化权":
                career_parts.append(f"流年{star}化权入官禄宫, 事业上可展现领导力, 有升职机会。")
            elif stype == "化科":
                career_parts.append(f"流年{star}化科入官禄宫, 专业能力得到认可, 名声提升。")
            elif stype == "化忌":
                career_parts.append(f"流年{star}化忌入官禄宫, 事业上需谨防失误, 不宜做重大决策。")
    
    if liunian.liunian_lucun in [mp_branch]:  # 简化判断
        career_parts.append("流年禄星照命, 事业财运均有增益。")
    
    if not career_parts:
        career_parts.append("事业上宜按部就班, 保持稳定发展。")
    
    career = "\n".join(career_parts)
    
    # ── 财运 ──
    wealth_parts = []
    caibo = palace_stars.get("财帛", [])
    if caibo:
        wealth_parts.append(f"财帛宫{'、'.join(caibo[:2])}主财务基调。")
    
    for star, stype in liunian.liunian_sihua.items():
        if star in caibo:
            if stype in ("化禄", "化权"):
                wealth_parts.append(f"流年{star}{stype}入财帛, 财运亨通, 可适度投资。")
            elif stype == "化忌":
                wealth_parts.append(f"流年{star}化忌入财帛, 财务状况需谨慎管理, 避免大额支出。")
    
    if liunian.liunian_lucun == mp_branch:
        wealth_parts.append("流禄临命, 正财稳定, 亦有偏财机会。")
    
    if not wealth_parts:
        wealth_parts.append("财运平稳, 宜以储蓄为主。")
    
    wealth = "\n".join(wealth_parts)
    
    # ── 感情运势 ──
    rel_parts = []
    fuqi = palace_stars.get("夫妻", [])
    if fuqi:
        rel_parts.append(f"夫妻宫{'、'.join(fuqi[:2])}影响感情生活。")
    
    peach_stars = {"贪狼","廉贞","太阴","天同"}
    for star in mp_stars:
        if star in peach_stars:
            rel_parts.append(f"流年命宫有{star}, 桃花运旺盛, 单身者有机会, 已婚者需保持界限。")
    
    for star, stype in liunian.liunian_sihua.items():
        if star in fuqi:
            if stype == "化忌":
                rel_parts.append(f"流年{star}化忌入夫妻宫, 感情上易有误会摩擦, 需多沟通。")
            elif stype in ("化禄", "化科"):
                rel_parts.append(f"流年{star}{stype}入夫妻宫, 感情关系和谐升温。")
    
    if not rel_parts:
        rel_parts.append("感情运势平稳, 适合维系现有关系。")
    
    relationship = "\n".join(rel_parts)
    
    # ── 健康提示 ──
    health_parts = []
    jier = palace_stars.get("疾厄", [])
    sha_in_jier = [s for s in jier if s in {"擎羊","陀罗","火星","铃星","地劫","地空"}]
    
    if sha_in_jier:
        health_parts.append(f"疾厄宫有煞星{'、'.join(sha_in_jier[:2])}, 需注意{'意外伤害' if '擎羊' in sha_in_jier or '火星' in sha_in_jier else '慢性疾病'}。")
    
    # 流年擎羊在疾厄宫需要获取疾厄宫地支
    # 简化: 这里跳过精确计算
    if not health_parts:
        health_parts.append("健康运势良好, 保持规律作息即可。")
    
    health = "\n".join(health_parts)
    
    # ── 关键月份 ──
    key_months = []
    
    # 流年四化星所在宫的原局月份推算
    for star, stype in liunian.liunian_sihua.items():
        star_palace = None
        for pname, stars in palace_stars.items():
            if star in stars:
                star_palace = pname
                break
        if star_palace and stype == "化禄":
            key_months.append(f"流年{star}化禄在{star_palace}, {star_palace}相关事务有良机。")
        elif star_palace and stype == "化忌":
            key_months.append(f"流年{star}化忌在{star_palace}, 此领域需谨慎行事。")
    
    # 太岁月份提示
    if liunian.zodiac:
        key_months.append(f"{liunian.zodiac}年值太岁, 农历正月、七月需格外注意。")
    
    # ── 年度建议 ──
    advice_parts = []
    if rating >= 3:
        advice_parts.append("吉星高照之年, 宜: 1) 把握机遇大胆行动; 2) 拓展人脉资源; 3) 适度投资理财。")
    elif rating >= 0:
        advice_parts.append("平稳之年, 宜: 1) 巩固现有基础; 2) 学习新技能; 3) 维护人际关系。")
    else:
        advice_parts.append("挑战之年, 宜: 1) 保守稳健行事; 2) 减少不必要的变动; 3) 注意身心健康。")
    
    advice = "\n".join(advice_parts)
    
    return LiunianAnalysis(
        year=liunian.year,
        year_ganzhi=liunian.year_ganzhi,
        overview=overview,
        career=career,
        wealth=wealth,
        relationship=relationship,
        health=health,
        key_months=key_months[:5],
        rating=rating,
        advice=advice,
    )


def analyze_multi_years(
    chart_data,
    palace_stars: Dict[str, List[str]],
    palace_branch_map: Dict[str, int],
    ming_index: int,
    start_year: int,
    count: int = 3,
) -> List[LiunianAnalysis]:
    """
    批量分析多年的流年运势.
    
    Returns:
        [{year, overview, career, ...}, ...]
    """
    results = []
    sihua_map = chart_data.sihua_map if hasattr(chart_data, 'sihua_map') else {}
    
    for y in range(start_year, start_year + count):
        liunian = calculate_liunian_info(y, chart_data, ming_index, palace_branch_map)
        analysis = analyze_liunian(liunian, palace_stars, sihua_map, chart_data)
        results.append(analysis)
    
    return results


def liunian_to_dict(analysis: LiunianAnalysis) -> dict:
    """将流年分析转为可序列化的字典."""
    return {
        "year": analysis.year,
        "year_ganzhi": analysis.year_ganzhi,
        "overview": analysis.overview,
        "career": analysis.career,
        "wealth": analysis.wealth,
        "relationship": analysis.relationship,
        "health": analysis.health,
        "key_months": analysis.key_months,
        "rating": analysis.rating,
        "advice": analysis.advice,
    }
