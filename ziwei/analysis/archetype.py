"""
人格原型 + 稀有度分数系统 — Archetype & Rarity Engine

实现:
- 14主星 → Jungian/中国文化原型映射
- 多星组合原型融合
- 每盘唯一稀有度分数 (SSR/SR/R/UC/C 五档)
- 抽卡式展示数据
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
import hashlib

from ..calendar.constants import EARTHLY_BRANCHES, PALACE_NAMES

# ══════════════════════════════════════════════════════════════
# 主星 → 原型映射
# ══════════════════════════════════════════════════════════════

@dataclass
class Archetype:
    name: str               # 原型名称
    element: str            # 所属五行
    tagline: str            # 一句话标语
    description: str        # 详细描述
    strengths: List[str]    # 3个优势
    shadows: List[str]      # 2个阴影面
    emoji: str              # 图标


ARCHETYPE_MAP: Dict[str, Archetype] = {
    "紫微": Archetype("君王", "土",
        "天生领袖，星辰之主",
        "紫微为众星之首，坐命者天生具有帝王气质。举止端庄，自尊心极强，行事光明磊落，一生贵人运佳。好面子，追求卓越，不轻易向人低头。宜担任领导职位，格局高者可至公卿。",
        ["统御力强，天生领袖气质", "贵人运佳，得道多助", "格局宏大，志存高远"],
        ["自尊过强，难以妥协", "高处不胜寒，内心孤独"],
        "👑"),
    "天机": Archetype("策士", "木",
        "神机妙算，智谋无双",
        "天机为谋略之星，坐命者思维敏捷，好奇心旺盛，善于谋划布局。如同军师一般，能在复杂局势中洞悉先机。想法多变，兴趣广泛，但有时难以专注。宜策划、咨询、技术研发。",
        ["思维敏捷，善于谋划", "适应力强，随机应变", "博学多闻，见解独到"],
        ["想法多变，难以专注", "思虑过重，精神内耗"],
        "🧠"),
    "太阳": Archetype("太阳", "火",
        "光芒万丈，普照四方",
        "太阳坐命者如同正午的烈日，热情开朗，乐于助人，人缘极佳。胸怀坦荡，有强烈的正义感和社会责任感。适合公共事业、教育、公益等需要曝光度的工作。女命有男子气概。",
        ["热情大方，人缘极佳", "正义感强，光明磊落", "感染力强，激励他人"],
        ["过于外放，忽略内心", "锋芒太露，易招嫉妒"],
        "☀️"),
    "武曲": Archetype("武将", "金",
        "刚毅果断，财星归位",
        "武曲为刚星亦是财星，坐命者刚毅果断，理财能力出众。做事雷厉风行，坚持到底，不轻易放弃。性格刚硬，原则性强。适合金融、管理、技术等实干型工作，能凭专业能力获得财富。",
        ["刚毅果断，执行力强", "理财能力出众", "原则性强，值得信赖"],
        ["性格刚硬，缺乏柔性", "过于务实，忽略情感"],
        "⚔️"),
    "天同": Archetype("福星", "水",
        "知足常乐，福泽绵长",
        "天同为福德之星，坐命者性情温和，知足常乐。善于协调人际关系，是团队中的润滑剂。不喜争斗，追求安逸舒适的生活。人缘好，但有时缺乏进取心。晚年福运尤佳。",
        ["性情温和，善于协调", "知足常乐，心态平和", "人缘好，受人喜爱"],
        ["缺乏进取心，安于现状", "回避冲突，不够果断"],
        "🌟"),
    "廉贞": Archetype("才子", "火",
        "才华横溢，至情至性",
        "廉贞为才华之星，坐命者个性鲜明，才华横溢。情感丰富且强烈，做事追求极致。魅力四射，容易成为人群焦点。但情绪波动较大，宜修心养性，将才情导入正途。适合艺术、设计、文职。",
        ["才华横溢，创意无限", "魅力四射，引人注目", "至情至性，真诚待人"],
        ["情绪波动大，容易极端", "锋芒毕露，招人忌惮"],
        "🎭"),
    "天府": Archetype("宰相", "土",
        "稳重务实，财库丰盈",
        "天府为库星，坐命者稳重务实，善于经营和理财。如同宰相治理国家，有条不紊，深谋远虑。一生衣食无忧，善于积累。但有时过于保守谨慎，缺乏冒险精神。适合管理、金融、地产。",
        ["稳重务实，值得信赖", "理财经营能力出众", "处事周全，考虑长远"],
        ["过于保守，错失良机", "控制欲强，不够放手"],
        "🏛️"),
    "太阴": Archetype("月亮", "水",
        "温润如玉，静水流深",
        "太阴为阴柔之星，坐命者温柔细腻，审美力强。如同月光般静谧柔和，内心世界丰富多彩。注重生活品质，追求优雅。女命端庄贤淑，男命温文尔雅。适合艺术、设计、护理等发挥细腻感受的工作。",
        ["温柔细腻，善解人意", "审美力强，有艺术天赋", "内心丰富，思想深邃"],
        ["过于敏感，容易受伤", "优柔寡断，行动迟缓"],
        "🌙"),
    "贪狼": Archetype("魅影", "木",
        "多才多艺，魅力无边",
        "贪狼为桃花星，坐命者多才多艺，善于交际，魅力四射。对各种事物充满好奇心，学习能力强。桃花运极旺，异性缘好。但需节制欲望，避免为情所困。适合艺术、演艺、公关、贸易。",
        ["多才多艺，学习力强", "社交手腕高超", "魅力四射，桃花运旺"],
        ["欲望强烈，难以节制", "浮华不实，根基不稳"],
        "💫"),
    "巨门": Archetype("辩士", "水",
        "口若悬河，明辨是非",
        "巨门为口舌之星，坐命者口才出众，善于思辨。对事物有深刻见解，不盲从权威。适合教育、法律、传媒等以口才见长的工作。但需慎言慎行，避免口舌是非。内心有强烈的求真欲。",
        ["口才出众，善于表达", "思辨力强，见解深刻", "不盲从，有独立思想"],
        ["口舌是非，容易树敌", "过于较真，不善变通"],
        "🗣️"),
    "天相": Archetype("辅臣", "水",
        "正直善良，辅佐之才",
        "天相为印星，坐命者正直善良，人缘极好。天生具有服务精神，善于辅佐他人。处事公正，深受上下信任。不适合独当一面，但作为二把手或团队成员极为出色。适合行政、管理、服务行业。",
        ["正直善良，值得信任", "服务精神强，善于协作", "处事公正，深得人心"],
        ["缺乏主见，依赖他人", "过于迁就，委屈自己"],
        "🤝"),
    "天梁": Archetype("长者", "土",
        "德高望重，福寿绵长",
        "天梁为寿星，坐命者有长者之风，乐于助人，有庇护他人的天性。性格固执但心地善良，好为人师。一生多有贵人相助，晚运佳。适合教育、医疗、公益等助人行业。有宗教缘分。",
        ["乐于助人，有保护欲", "稳重可靠，德高望重", "有智慧，能给予他人指导"],
        ["性格固执，好为人师", "过于操心，身心俱疲"],
        "🦉"),
    "七杀": Archetype("战将", "金",
        "勇往直前，所向披靡",
        "七杀为将星，坐命者性格刚烈，敢作敢为。如同独当一面的大将军，遇强则强，不畏艰难。适合开拓性、竞争性强的工作。但需防冲动决策，学会以柔克刚。一生有较大的起伏。",
        ["勇往直前，不畏艰难", "决策果断，行动力强", "遇强则强，越挫越勇"],
        ["冲动易怒，缺乏耐心", "孤独感强，不善表达"],
        "🗡️"),
    "破军": Archetype("破军", "水",
        "破旧立新，天地重塑",
        "破军为变动之星，坐命者个性独立，不喜约束。具有强烈的革新精神，敢于打破常规。一生多变，宜顺势而为，不适合按部就班的工作。创造力和破坏力同样惊人，能在废墟中建立新秩序。",
        ["创新力强，敢于突破", "独立自主，不随波逐流", "行动力强，说做就做"],
        ["破坏性大，难以稳定", "叛逆心强，不善妥协"],
        "💥"),
}

# ══════════════════════════════════════════════════════════════
# 双星组合原型 (命宫/身宫/福德宫)
# ══════════════════════════════════════════════════════════════

FUSION_ARCHETYPES = {
    ("紫微","天府"): ("紫府同辉", "帝王与宰相并肩，至尊至贵。为紫微斗数中最尊贵的组合，天生领袖，格局极大。既能制定战略(紫微)，又能落地执行(天府)，是真正的统帅之才。", "👑🏛️"),
    ("紫微","天相"): ("紫相仪天", "帝王得贤相辅佐，权威与公正并存。既有领导力又善于协调，适合行政管理和公共服务。为人正直，处事公正。", "👑🤝"),
    ("紫微","破军"): ("铁血君王", "帝王挥师破阵，大破大立。霸气外露，敢于打破旧秩序建立新规则。一生大起大落，但每次跌倒都能以更强的姿态站起。", "👑💥"),
    ("紫微","七杀"): ("杀破紫垣", "帝王御驾亲征，威震四方。兼具统御力与战斗力，是创业者和开拓者的典范。事业心极强，不达目的誓不罢休。", "👑🗡️"),
    ("太阳","太阴"): ("日月同辉", "阴阳调和，刚柔并济。既有太阳的热情又有月亮的温柔，性格最为圆融。内外兼修，进退有据。是极佳的平衡型人才。", "☀️🌙"),
    ("太阳","巨门"): ("光芒之舌", "光芒与言辞并耀。口才出众又热情洋溢，适合教育、传媒、演讲等领域。能以语言感染和激励他人。", "☀️🗣️"),
    ("天机","天梁"): ("神机妙算", "智谋与经验完美结合。既有天机的敏捷又有天梁的稳重，是绝佳的谋士和顾问。善于规划长远战略。", "🧠🦉"),
    ("武曲","天府"): ("金玉满堂", "财星汇聚，富甲一方。武曲的行动力配合天府的积累力，理财能力超一流。适合金融投资和实业经营。", "⚔️🏛️"),
    ("武曲","天相"): ("刚柔并济", "刚毅中有柔性，执行力强且能协调。适合大型项目的管理，能在坚持原则的同时照顾各方利益。", "⚔️🤝"),
    ("廉贞","天府"): ("冰火同炉", "才华与端庄并存。廉贞的激情被天府的稳重调和，既能散发魅力又不失分寸。适合需要创造力与执行力的工作。", "🎭🏛️"),
    ("廉贞","贪狼"): ("绝代双骄", "两大桃花星会合，魅力指数爆表。多才多艺，艺术天赋极高。但需管控情感，避免为情所困。适合演艺和创意行业。", "🎭💫"),
    ("七杀","破军"): ("破阵先锋", "最强的开拓者组合。一生充满战斗与变革，适合创业、军事、竞技等高压领域。不是大成就是大败，绝不甘于平庸。", "🗡️💥"),
    ("天同","太阴"): ("温水映月", "温柔的双重奏。性情最为温和，善解人意，人缘极佳。内心世界丰富，适合艺术创作和人文关怀工作。", "🌟🌙"),
    ("贪狼","武曲"): ("贪武同行", "欲望与能力并存。有赚钱的野心也有理财的本事。宜经商创业，但需防过度投机。在商业和社交领域游刃有余。", "💫⚔️"),
    ("天机","巨门"): ("智者之辩", "思维与口才的完美结合。逻辑严谨又善于表达，是天生的问题解决者和思想传播者。适合科研、法律、教育。", "🧠🗣️"),
}


def _get_dominant_archetype(
    ming_stars: List[str], shen_stars: List[str], fude_stars: List[str],
    star_to_branch: Dict[str, str]
) -> Tuple[Optional[Archetype], str]:
    """
    确定主导原型.
    
    优先级: 命宫主星 > 身宫主星 > 福德宫主星
    同宫内按亮度优先
    """
    main_stars = {"紫微","天机","太阳","武曲","天同","廉贞",
                  "天府","太阴","贪狼","巨门","天相","天梁","七杀","破军"}
    
    # 收集候选
    candidates = []
    for star in ming_stars:
        if star in main_stars:
            candidates.append(("命宫", star, star_to_branch.get(star, "")))
    for star in shen_stars:
        if star in main_stars:
            candidates.append(("身宫", star, star_to_branch.get(star, "")))
    for star in fude_stars:
        if star in main_stars:
            candidates.append(("福德宫", star, star_to_branch.get(star, "")))
    
    if not candidates:
        return None, "命无主星"
    
    # 按来源排序: 命宫 > 身宫 > 福德宫
    source_rank = {"命宫": 0, "身宫": 1, "福德宫": 2}
    candidates.sort(key=lambda x: source_rank.get(x[0], 3))
    
    # 取命宫和身宫的主星
    ming_mains = [s for src, s, br in candidates if src == "命宫"]
    shen_mains = [s for src, s, br in candidates if src == "身宫"]
    
    # 尝试组合
    all_primary = ming_mains + shen_mains
    
    if len(all_primary) >= 2:
        # 找最佳融合
        a, b = all_primary[0], all_primary[1]
        key = tuple(sorted([a, b]))
        if key in FUSION_ARCHETYPES:
            name, desc, emoji = FUSION_ARCHETYPES[key]
            # 创建融合原型
            base_a = ARCHETYPE_MAP.get(a)
            base_b = ARCHETYPE_MAP.get(b)
            if base_a and base_b:
                fusion = Archetype(
                    name=name, element=base_a.element,
                    tagline=desc[:24] + "…",
                    description=desc,
                    strengths=base_a.strengths[:2] + base_b.strengths[:1],
                    shadows=base_a.shadows[:1] + base_b.shadows[:1],
                    emoji=emoji,
                )
                return fusion, name
    
    # 单个主星
    primary = all_primary[0] if all_primary else candidates[0][1]
    archetype = ARCHETYPE_MAP.get(primary)
    return archetype, primary if archetype else "未知"


def compute_archetype(
    chart_data,
    palace_stars: Dict[str, List[str]],
    star_to_branch: Dict[str, str],
) -> Dict:
    """
    计算命盘的人格原型.
    
    Args:
        chart_data: ChartData 对象
        palace_stars: {宫名: [星曜列表]}
        star_to_branch: {星名: 地支}
    
    Returns:
        原型分析结果
    """
    ming_stars = palace_stars.get("命宫", [])
    
    # 找身宫
    shen_palace = "命宫"
    for p in chart_data.palaces:
        if p.is_body:
            shen_palace = p.name
            break
    shen_stars = palace_stars.get(shen_palace, [])
    fude_stars = palace_stars.get("福德", [])
    
    archetype, primary_star = _get_dominant_archetype(
        ming_stars, shen_stars, fude_stars, star_to_branch
    )
    
    result: Dict = {
        "primary_archetype": primary_star,
        "archetype_name": archetype.name if archetype else "未定型",
        "tagline": archetype.tagline if archetype else "",
        "description": archetype.description if archetype else "命宫无主星，性格受环境影响较大。",
        "emoji": archetype.emoji if archetype else "❓",
        "element": archetype.element if archetype else "?",
        "strengths": archetype.strengths if archetype else [],
        "shadows": archetype.shadows if archetype else [],
    }
    
    # 添加身宫/福德宫影响
    if shen_palace != "命宫" and shen_stars:
        shen_mains = [s for s in shen_stars 
                      if s in {"紫微","天机","太阳","武曲","天同","廉贞",
                               "天府","太阴","贪狼","巨门","天相","天梁","七杀","破军"}]
        if shen_mains:
            result["shen_influence"] = f"身宫在{shen_palace}，{'、'.join(shen_mains)}能量在后半生逐渐显现。"
    
    fude_mains = [s for s in fude_stars 
                  if s in {"紫微","天机","太阳","武曲","天同","廉贞",
                           "天府","太阴","贪狼","巨门","天相","天梁","七杀","破军"}]
    if fude_mains:
        result["inner_world"] = f"内心世界受{'、'.join(fude_mains)}影响。"
    
    return result


# ══════════════════════════════════════════════════════════════
# 稀有度分数系统
# ══════════════════════════════════════════════════════════════

# 稀有星曜配置 (points scaled for 90-100 range)
RARITY_TIERS = {
    ("紫微","午"): ("S", "紫微在午 — 极星入垣，帝王居正位", 1.8),
    ("天机","午"): ("S", "天机在午 — 智者在正午，日光普照智慧", 1.5),
    ("太阴","亥"): ("S", "太阴在亥 — 月朗天门，最明亮的月光", 1.8),
    ("太阳","卯"): ("S", "太阳在卯 — 日照雷门，旭日东升", 1.8),
    ("廉贞","寅"): ("A", "廉贞在寅 — 雄宿乾元，才华横溢", 1.2),
    ("廉贞","申"): ("A", "廉贞在申 — 雄宿乾元，逆境崛起", 1.2),
    ("七杀","寅"): ("A", "七杀在寅 — 七杀朝斗，大将之才", 1.0),
    ("七杀","申"): ("A", "七杀在申 — 七杀朝斗，权威显赫", 1.0),
    ("天府","子"): ("B", "天府在子 — 财库临旺地", 0.7),
    ("紫微","子"): ("B", "紫微在子 — 极星得地", 0.6),
    ("紫微","辰"): ("B", "紫微在辰 — 极星入墓，厚积薄发", 0.5),
    ("紫微","戌"): ("B", "紫微在戌 — 极星入墓，厚积薄发", 0.5),
    ("太阴","酉"): ("B", "太阴在酉 — 月到中天", 0.7),
    ("太阳","午"): ("B", "太阳在午 — 日丽中天", 0.7),
}

# 同宫稀有组合
RARITY_COMBOS = {
    ("紫微","天府"): ("S", "紫府同宫 — 至尊至贵", 2.0),
    ("紫微","天相"): ("A", "紫相同宫 — 权威辅佐", 1.4),
    ("武曲","天府"): ("A", "武府同宫 — 财星汇聚", 1.3),
    ("廉贞","贪狼"): ("A", "廉贪同宫 — 绝代双骄", 1.2),
    ("七杀","破军"): ("A", "杀破同宫 — 破阵先锋", 1.2),
    ("太阳","巨门"): ("B", "巨日同宫 — 光芒之舌", 0.8),
    ("武曲","天相"): ("B", "武相同宫 — 刚柔并济", 0.7),
    ("天机","天梁"): ("B", "机梁同宫 — 神机妙算", 0.7),
    ("天同","太阴"): ("B", "同阴同宫 — 温水映月", 0.6),
}


def compute_rarity(chart_data) -> Dict:
    """
    计算命盘的稀有度分数 (小红书风格).
    
    使用命盘关键信息的哈希值作为基础分,
    再根据星曜配置的稀有度进行加权调整.
    
    Returns:
        {
            "score": int,           # 0-1000
            "percentile": float,    # 百分位 (0-100)
            "tier": str,            # SSR/SR/R/UC/C
            "tier_label": str,      # 中文标签
            "tier_emoji": str,      # 稀有度emoji
            "color": str,           # 主题色
            "glow": str,            # 发光效果
            "card_bg": str,         # 卡片背景渐变
            "bonuses": [...],       # 稀有加分项
            "rank_text": str,       # "你的命盘稀有度超越 92.7% 的人"
        }
    """
    d = chart_data
    
    # ── 1. 基础哈希分 ──
    seed_str = (
        f"{d.year_pillar}|{d.month_pillar}|{d.day_pillar}|{d.hour_pillar}|"
        f"{d.lunar_month}|{d.lunar_day}|{d.ming_palace}|{d.wuxing_ju_name}"
    )
    # 使用 SHA256 获得稳定但看似随机的哈希
    hash_hex = hashlib.sha256(seed_str.encode()).hexdigest()
    # 基础分: 90-96 + 一点点客户端时间噪声让每次感觉不同
    # 但核心哈希保持稳定(同输入得同分)
    base_score = 90.0 + (int(hash_hex[:8], 16) % 60) / 10.0  # 90.0 - 96.0
    
    # ── 2. 星曜稀有加成 ──
    bonuses = []
    bonus_total = 0.0
    
    # 建立星→地支映射
    star_to_branch = {}
    for p in chart_data.palaces:
        for s in p.stars:
            star_to_branch[s] = p.branch
    
    # 检查单星稀有位置
    for star, branch in star_to_branch.items():
        key = (star, branch)
        if key in RARITY_TIERS:
            tier, desc, pts = RARITY_TIERS[key]
            bonuses.append({"type": "star_position", "tier": tier, "desc": desc, "points": pts})
            bonus_total += pts
    
    # 检查同宫组合
    branch_stars: Dict[str, List[str]] = {}
    for star, branch in star_to_branch.items():
        branch_stars.setdefault(branch, []).append(star)
    
    for branch, stars in branch_stars.items():
        main_stars_here = [s for s in stars if s in {
            "紫微","天机","太阳","武曲","天同","廉贞",
            "天府","太阴","贪狼","巨门","天相","天梁","七杀","破军"
        }]
        for i in range(len(main_stars_here)):
            for j in range(i+1, len(main_stars_here)):
                key = tuple(sorted([main_stars_here[i], main_stars_here[j]]))
                if key in RARITY_COMBOS:
                    tier, desc, pts = RARITY_COMBOS[key]
                    bonuses.append({"type": "star_combo", "tier": tier, "desc": desc, "points": pts})
                    bonus_total += pts
    
    # ── 3. 四化加分 ──
    sihua_count = len(chart_data.sihua_map)
    if sihua_count >= 4:
        bonus_total += 0.8
        bonuses.append({"type": "sihua", "tier": "S", "desc": "四化俱全，命局动力充沛", "points": 0.8})
    elif sihua_count >= 3:
        bonus_total += 0.4
        bonuses.append({"type": "sihua", "tier": "S", "desc": "三化聚气，命局有明确方向", "points": 0.4})
    
    # ── 4. 总分 (90-100 范围, 保证每个人都不低) ──
    final_score = round(min(100.0, max(90.0, base_score + bonus_total)), 1)
    
    # ── 5. 定档 — 所有人至少 S 级 ──
    tier_config = {
        "UR":  ("旷世奇才", "👑", "#ffd700", "0 0 50px rgba(255,215,0,0.6)",
                "linear-gradient(135deg, #1a0800 0%, #2e1000 50%, #1a0a18 100%)",
                "万中无一的绝世命盘。星辰为你重排阵列，此生命格已非凡品", True),
        "SSR": ("天选之命", "🌟", "#f59e0b", "0 0 40px rgba(245,158,11,0.5)",
                "linear-gradient(135deg, #1a0e00 0%, #2e1800 50%, #1a0e2e 100%)",
                "星宿垂青的稀有命盘。命运的齿轮为你转动，注定书写不凡篇章", False),
        "SR":  ("凤毛麟角", "💎", "#c084fc", "0 0 30px rgba(192,132,252,0.4)",
                "linear-gradient(135deg, #0a002e 0%, #1a0a3a 50%, #0a0a2e 100%)",
                "万里挑一的精妙格局。群星以罕见的和谐为你编织命运之网", False),
        "S":   ("独具一格", "✨", "#60a5fa", "0 0 24px rgba(96,165,250,0.35)",
                "linear-gradient(135deg, #0a0a2e 0%, #0d1a3a 50%, #0a1030 100%)",
                "独特的星曜排布映照出独一无二的你。每个人都是一颗独特的星辰", False),
    }
    
    if final_score >= 98.5:
        tier = "UR"
    elif final_score >= 96.0:
        tier = "SSR"
    elif final_score >= 93.0:
        tier = "SR"
    else:
        tier = "S"
    
    tier_label, tier_emoji, color, glow, card_bg, rank_text, unlock_deep = tier_config[tier]
    
    result = {
        "score": final_score,
        "tier": tier,
        "tier_label": tier_label,
        "tier_emoji": tier_emoji,
        "color": color,
        "glow": glow,
        "card_bg": card_bg,
        "rank_text": rank_text,
        "bonuses": bonuses[:8],
    }
    
    # UR 解锁深度命格解析
    if unlock_deep:
        result["deep_unlocked"] = True
        result["deep_analysis"] = _generate_deep_destiny_analysis(chart_data, star_to_branch)
    
    return result


def _generate_deep_destiny_analysis(chart_data, star_to_branch: dict) -> Dict:
    """UR 旷世奇才专属: 深度命格解析."""
    main_set = {"紫微","天机","太阳","武曲","天同","廉贞",
                "天府","太阴","贪狼","巨门","天相","天梁","七杀","破军"}
    ming_stars = chart_data.palaces[0].stars if chart_data.palaces else []
    ming_mains = [s for s in ming_stars if s in main_set]
    shen_stars = []
    for p in chart_data.palaces:
        if p.is_body: shen_stars = [s for s in p.stars if s in main_set]; break
    from .analyzer import detect_patterns
    patterns = detect_patterns(star_to_branch,
        {p.name: p.stars for p in chart_data.palaces},
        chart_data.palaces[0].branch,
        chart_data.year_pillar[0] if chart_data.year_pillar else "甲")
    good_patterns = [p for p in patterns if p.quality == "吉"]
    deep_lines = []
    if ming_mains: deep_lines.append(f"命宫{'、'.join(ming_mains)}坐守，奠定性格核心基调。")
    if shen_stars: deep_lines.append(f"身宫{'、'.join(shen_stars)}的能量在后半生逐渐显现。")
    if good_patterns: deep_lines.append("格局"+"、".join(p.name for p in good_patterns[:3])+"交相辉映，天赋异禀。")
    if chart_data.sihua_map:
        for star, stype in chart_data.sihua_map.items():
            m={"化禄":star+"化禄：财富福泽之源","化权":star+"化权：力量支点","化科":star+"化科：智慧灯塔","化忌":star+"化忌：人生课题，磨砺即成就"}
            if stype in m: deep_lines.append(m[stype])
    deep_lines.append("星曜排布精妙高远。顺势而为，借力而行。")
    return {"title": "👑 旷世奇才 · 深度命格", "content": "\n".join(deep_lines), "pattern_count": len(good_patterns), "unlocked": True}
