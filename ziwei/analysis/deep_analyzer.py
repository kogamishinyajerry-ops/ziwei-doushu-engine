"""
深度分析引擎 — Deep Analysis Engine

多层递进分析:
1. 星曜互涉 — 同宫/对宫/三合/夹宫组合效应
2. 四化飞星 — 化禄权科忌飞入十二宫详解
3. 多层次解读报告 — 性格/事业/感情/健康/流年

核心原则: 每个分析都基于具体命盘的星曜组合推导, 而非简单模板匹配.
"""

from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field
import math

from ..calendar.constants import (
    EARTHLY_BRANCHES, PALACE_NAMES,
    OPPOSITE_PALACE, TRIAD_OFFSET, FOUR_CARDINAL_OFFSET,
    SIHUA_NAMES,
)

# ──────────────────────────────────────
# 星曜互涉引擎
# ──────────────────────────────────────

@dataclass
class InteractionResult:
    """星曜互涉分析结果."""
    type: str           # 同宫/对宫/三合/夹宫
    stars: List[str]    # 涉及的星曜
    palaces: List[str]  # 涉及的宫位
    effect: str         # 互涉效应描述
    rating: int         # 吉凶评分 (-5到+5)
    detail: str         # 详细解读


def analyze_star_interactions(
    star_to_branch: Dict[str, str],
    star_to_palace: Dict[str, str],
    palace_stars: Dict[str, List[str]],
    sihua_map: Dict[str, str],
) -> List[InteractionResult]:
    """
    分析星曜互涉关系.
    
    检测:
    - 同宫组合 (两个主星在同一宫)
    - 对宫互照 (星曜在对宫)
    - 三合会照 (星曜在三方)
    - 夹宫效应 (两星夹一宫)
    - 四化飞入
    """
    results = []
    
    main_stars = ["紫微","天机","太阳","武曲","天同","廉贞",
                  "天府","太阴","贪狼","巨门","天相","天梁","七杀","破军"]
    
    # Helper
    def branch_of(star): return star_to_branch.get(star)
    def palace_of(star): return star_to_palace.get(star)
    def stars_at(branch): 
        return [s for s,b in star_to_branch.items() if b == branch]
    
    # ── 1. 同宫主星组合 ──
    for palace in PALACE_NAMES:
        stars_here = palace_stars.get(palace, [])
        mains_here = [s for s in stars_here if s in main_stars]
        
        if len(mains_here) >= 2:
            for i in range(len(mains_here)):
                for j in range(i+1, len(mains_here)):
                    combo = _analyze_same_palace_combo(mains_here[i], mains_here[j], palace)
                    if combo:
                        results.append(combo)
    
    # ── 2. 对宫互照 ──
    for star in main_stars:
        b = branch_of(star)
        if not b: continue
        opp_branch = EARTHLY_BRANCHES[(EARTHLY_BRANCHES.index(b) + 6) % 12]
        opp_stars = [s for s in main_stars if branch_of(s) == opp_branch and s != star]
        for os in opp_stars:
            effect = _analyze_opposite_combo(star, os)
            if effect:
                results.append(InteractionResult(
                    "对宫", [star, os],
                    [palace_of(star), palace_of(os)],
                    effect["desc"], effect["rating"], effect["detail"]
                ))
    
    # ── 3. 三合会照 ──
    for palace in PALACE_NAMES:
        pi = PALACE_NAMES.index(palace)
        triad_palaces = [PALACE_NAMES[(pi + o) % 12] for o in TRIAD_OFFSET]
        triad_stars = []
        for tp in triad_palaces:
            for s in palace_stars.get(tp, []):
                if s in main_stars:
                    triad_stars.append((s, tp))
        
        # 检查命宫三合的特殊组合
        if palace == "命宫" and len(triad_stars) >= 3:
            effect = _analyze_triad_combo([s for s,_ in triad_stars])
            if effect:
                results.append(InteractionResult(
                    "三合", [s for s,_ in triad_stars],
                    triad_palaces,
                    effect["desc"], effect["rating"], effect["detail"]
                ))
    
    # ── 4. 夹宫效应 ──
    for palace in PALACE_NAMES:
        pi = PALACE_NAMES.index(palace)
        bi = EARTHLY_BRANCHES.index(star_to_branch.get(
            palace_stars.get(palace, [None])[0] if palace_stars.get(palace) else ""
        )) if palace_stars.get(palace) else -1
        
        if bi < 0:
            continue
            
        prev_b = EARTHLY_BRANCHES[(bi - 1) % 12]
        next_b = EARTHLY_BRANCHES[(bi + 1) % 12]
        
        left_stars = [s for s in main_stars if branch_of(s) == prev_b]
        right_stars = [s for s in main_stars if branch_of(s) == next_b]
        
        # 吉星夹 vs 煞星夹
        sha_stars = ["擎羊","陀罗","火星","铃星","地劫","地空"]
        ji_stars = ["文昌","文曲","左辅","右弼","天魁","天钺"]
        
        left_all = stars_at(prev_b)
        right_all = stars_at(next_b)
        
        sha_clip = any(s in sha_stars for s in left_all) and any(s in sha_stars for s in right_all)
        ji_clip = any(s in ji_stars for s in left_all) and any(s in ji_stars for s in right_all)
        
        if sha_clip and palace_stars.get(palace):
            results.append(InteractionResult(
                "夹宫", left_all + right_all, [palace],
                f"{palace}被煞星所夹, 运势多有阻碍, 需加倍努力方能突破。",
                -3, f"左右邻宫煞星汇聚, 对{palace}形成压制。建议在此领域做好充分准备, 不可冒进。"
            ))
        elif ji_clip and palace_stars.get(palace):
            results.append(InteractionResult(
                "夹宫", left_all + right_all, [palace],
                f"{palace}得吉星夹辅, 此宫事务多遇贵人相助, 顺遂通达。",
                +3, f"左右邻宫吉星扶持, {palace}能量倍增。宜在此领域积极进取, 把握良机。"
            ))
    
    # ── 5. 四化飞入分析 ──
    for star, stype in sihua_map.items():
        sb = branch_of(star)
        sp = palace_of(star)
        if not sb or not sp: continue
        
        # 飞入对宫
        opp_idx = (EARTHLY_BRANCHES.index(sb) + 6) % 12
        opp_branch = EARTHLY_BRANCHES[opp_idx]
        for pname, pidx in PALACE_LAYOUT_CACHE.items():  # fallback
            pass
        
        effect = _analyze_sihua_flight(star, stype, sp)
        if effect:
            results.append(InteractionResult(
                "四化飞星", [star], [sp],
                effect["desc"], effect["rating"], effect["detail"]
            ))
    
    return results


# 缓存: 宫名→地支索引 (在外部设置)
PALACE_LAYOUT_CACHE: Dict[str, int] = {}


# ──────────────────────────────────────
# 组合效应字典
# ──────────────────────────────────────

def _analyze_same_palace_combo(s1: str, s2: str, palace: str) -> Optional[InteractionResult]:
    """分析同宫双主星组合."""
    key = tuple(sorted([s1, s2]))
    
    combos = {
        ("紫微","天府"): ("紫府同宫", "最尊贵的帝王组合", +5, 
            f"紫微天府同守{palace}, 如帝王坐朝堂。天生领袖, 气度恢弘, 一生贵人环绕。"
            "宜担任管理职位或自主创业, 格局高者可达公卿之位。但需防过于自负。"),
        ("紫微","天相"): ("紫相会合", "权威与辅佐完美结合", +4,
            f"紫微天相同宫{palace}, 既有领导力又善协调。适合行政、管理、公关等领域。"
            "为人正直, 处事公正, 深得上下信任。"),
        ("紫微","破军"): ("紫破同宫", "帝王遇破军, 大破大立", +2,
            f"紫微破军同守{palace}, 霸气外露, 敢作敢为。一生多有开创性成就, "
            "但也伴随大的变动。宜顺势而为, 不宜固守。"),
        ("太阳","太阴"): ("日月同宫", "阴阳调和, 刚柔并济", +4,
            f"太阳太阴同守{palace}, 性格圆融, 善于处理复杂人际关系。"
            "事业上进退有据, 能文能武。家庭观念强, 注重平衡。"),
        ("太阳","巨门"): ("巨日同宫", "口才与光芒并耀", +3,
            f"太阳巨门同守{palace}, 口才出众, 见识广博。宜教育、传媒、法律行业。"
            "能够以言服人, 但也需谨防口舌是非。"),
        ("天机","天梁"): ("机梁善谈", "智谋与长者之风", +3,
            f"天机天梁同守{palace}, 聪明睿智, 善于分析和谋划。宜顾问、咨询、教育。"
            "有长者之风, 乐于提携后进, 但也需防好为人师。"),
        ("武曲","天府"): ("武府会合", "财富与经营之才", +4,
            f"武曲天府同守{palace}, 理财能力极强, 善于经营和投资。一生财富积累可观。"
            "宜金融、地产、贸易等行业。为人务实稳重。"),
        ("廉贞","天府"): ("廉府清白", "才华与端庄并存", +3,
            f"廉贞天府同守{palace}, 才华横溢而不失端庄。宜艺术、设计、文职工作。"
            "虽可能经历波折, 但能持身清白, 终得善果。"),
        ("廉贞","贪狼"): ("廉贪会合", "才华与欲望交织", -1,
            f"廉贞贪狼同守{palace}, 多才多艺但易为欲望所困。桃花运极旺, "
            "需管控情感, 避免为情所累。若能自律, 可在艺术领域大放异彩。"),
        ("七杀","破军"): ("杀破会合", "刚烈与变动并存", -2,
            f"七杀破军同守{palace}, 性格刚烈决绝,一生多变。宜武职、创业、竞争性行业。"
            "需防冲动决策, 学会以柔克刚。"),
        ("天同","太阴"): ("同阴柔美", "温柔与细腻的典范", +3,
            f"天同太阴同守{palace}, 性情温和, 善解人意。宜服务、护理、艺术行业。"
            "人缘极佳, 生活安逸, 但需防过于安逸导致进取心不足。"),
        ("贪狼","武曲"): ("贪武同行", "欲望与理财并存", +1,
            f"贪狼武曲同守{palace}, 有赚钱的欲望也有理财的手段。宜经商, 但需防"
            "过度投机。财运波动较大, 需要稳健策略。"),
    }
    
    if key in combos:
        name, desc, rating, detail = combos[key]
        return InteractionResult("同宫", [s1, s2], [palace], desc, rating, detail)
    
    return None


def _analyze_opposite_combo(s1: str, s2: str) -> Optional[dict]:
    """分析对宫互照."""
    key = tuple(sorted([s1, s2]))
    
    combos = {
        ("紫微","破军"): {"desc":"紫微破军对宫互照, 帝星与破军相望, 主大起大落。一生必有重大变革。",
                          "rating":2, "detail":"紫微坐命, 破军在迁移, 内心渴望安稳但环境逼迫改变。学会在变化中保持定力是人生课题。"},
        ("太阳","太阴"): {"desc":"日月对宫互照, 阴阳平衡, 人生起伏有序。",
                          "rating":4, "detail":"太阳太阴分守命宫与迁移, 内外兼修, 进退有据。适合需要平衡能力的工作。"},
        ("天机","巨门"): {"desc":"天机巨门对宫, 智慧与口才相呼应。",
                          "rating":3, "detail":"善于思考也善于表达, 宜律师、教师、咨询师等需要逻辑与口才并重的职业。"},
        ("廉贞","贪狼"): {"desc":"廉贞贪狼对宫, 才华与桃花互相影响。",
                          "rating":0, "detail":"命宫与迁移宫的艺术星曜互照, 适合在艺术和交际领域发展, 但需注意情感管理。"},
    }
    
    return combos.get(key)


def _analyze_triad_combo(stars: List[str]) -> Optional[dict]:
    """分析三合会照组合."""
    sset = set(stars)
    
    if {"七杀","破军","贪狼"}.issubset(sset):
        return {"desc":"杀破狼三合会照命宫, 人生充满变动与机遇。一生高潮迭起, 绝不平庸。",
                "rating":2, "detail":"这是紫微斗数中最具张力的组合之一。宜顺势而为, 把握每次变革的机遇。创业、开拓性工作最适合。但需注意风险控制。"}
    
    if {"天机","太阴","天同","天梁"}.issubset(sset):
        return {"desc":"机月同梁四曜会照, 清贵之格。宜公职、文教、公益事业。",
                "rating":4, "detail":"此组合主清贵而非富贵, 不宜经商。适合公务员、教师、研究员等稳定的公职工作。为人正直, 有社会责任感。"}
    
    if {"太阳","天梁","文昌","禄存"}.intersection(sset) == {"太阳","天梁","文昌"}:
        return {"desc":"阳梁昌禄会照, 科甲之格。学业有成, 金榜题名。",
                "rating":5, "detail":"最佳的科名组合。考试运强, 学历高, 宜走学术或专业路线。获得社会地位的方式是通过知识和专业能力。"}
    
    return None


def _analyze_sihua_flight(star: str, stype: str, palace: str) -> Optional[dict]:
    """分析四化飞入某宫的效应."""
    effects = {
        ("化禄","命宫"): {"desc":f"{star}化禄入命宫, 天生福泽深厚, 一生财运亨通。",
                         "rating":5, "detail":"命宫得化禄, 如天降甘霖。先天条件优越, 容易获得资源。但需防过于安逸, 不思进取。"},
        ("化禄","财帛"): {"desc":f"{star}化禄入财帛宫, 财运极旺, 正财偏财皆有。",
                         "rating":5, "detail":"财帛宫化禄, 赚钱能力出众。宜把握良机, 但需合理理财, 避免挥霍。"},
        ("化禄","官禄"): {"desc":f"{star}化禄入官禄宫, 事业顺利, 多贵人提携。",
                         "rating":4, "detail":"官禄宫化禄, 职场运势强劲。容易获得上级赏识, 升迁机会多。"},
        ("化权","命宫"): {"desc":f"{star}化权入命宫, 权势欲望强, 有领导力。",
                         "rating":4, "detail":"命宫化权, 天生有领导气质。做事果断, 执行力强。但需防专断独行。"},
        ("化权","官禄"): {"desc":f"{star}化权入官禄宫, 事业有权威, 能独当一面。",
                         "rating":4, "detail":"官禄宫化权, 在职场上能掌握实权。宜担任管理职位, 发挥领导才能。"},
        ("化科","命宫"): {"desc":f"{star}化科入命宫, 名声好, 学业有成。",
                         "rating":4, "detail":"命宫化科, 天生有书卷气。宜走学术、专业路线, 以知识和名声立足。"},
        ("化科","官禄"): {"desc":f"{star}化科入官禄宫, 事业以专业立身, 名声在外。",
                         "rating":3, "detail":"官禄宫化科, 宜在专业领域深耕。声誉是事业的基石。"},
        ("化忌","命宫"): {"desc":f"{star}化忌入命宫, 一生多波折, 需加倍努力。",
                         "rating":-3, "detail":"命宫化忌, 人生课题较多。但化忌也代表执着, 若能专注于某个领域, 也能有大成就。需注意心理健康。"},
        ("化忌","夫妻"): {"desc":f"{star}化忌入夫妻宫, 感情多波折, 需用心经营。",
                         "rating":-3, "detail":"夫妻宫化忌, 感情路上多考验。需学会沟通和包容, 婚姻方可长久。"},
        ("化忌","财帛"): {"desc":f"{star}化忌入财帛宫, 财运多阻碍, 宜守不宜攻。",
                         "rating":-2, "detail":"财帛宫化忌, 赚钱辛苦, 宜精打细算。不适合高风险投资。"},
    }
    
    key = (stype, palace)
    if key in effects:
        return effects[key]
    
    # 通用描述
    generic = {
        "化禄": {"desc":f"{star}化禄入{palace}, 该领域运势得到加持。", "rating":3,
                 "detail":f"{palace}得化禄, 能量充沛。此领域多为顺境, 宜积极进取。"},
        "化权": {"desc":f"{star}化权入{palace}, 该领域有掌控力。", "rating":3,
                 "detail":f"{palace}得化权, 主导性强。此领域您有话语权, 但也需听取他人意见。"},
        "化科": {"desc":f"{star}化科入{palace}, 该领域名声好。", "rating":3,
                 "detail":f"{palace}得化科, 声誉良好。此领域以专业和名声取胜。"},
        "化忌": {"desc":f"{star}化忌入{palace}, 该领域多阻碍。", "rating":-2,
                 "detail":f"{palace}得化忌, 此领域是您的人生课题。面对困难时, 坚持不懈必有突破。"},
    }
    
    return generic.get(stype)


# ──────────────────────────────────────
# 多层次解读报告生成
# ──────────────────────────────────────

@dataclass
class DeepReport:
    """深度解读报告."""
    # 性格分析
    personality: str = ""
    personality_detail: str = ""
    
    # 事业财运
    career: str = ""
    career_detail: str = ""
    wealth: str = ""
    wealth_tip: str = ""
    
    # 感情婚姻
    relationship: str = ""
    relationship_detail: str = ""
    
    # 健康状况
    health: str = ""
    health_warning: str = ""
    
    # 关键年龄节点
    key_ages: List[dict] = field(default_factory=list)
    
    # 人生建议
    advice: str = ""
    
    # 命盘亮点
    highlights: List[str] = field(default_factory=list)
    cautions: List[str] = field(default_factory=list)


def generate_deep_report(chart_data, interactions: List[InteractionResult]) -> DeepReport:
    """
    生成深度多层次解读报告.
    
    基于星曜具体位置、互涉关系和四化飞星,
    推导个性化的命盘解读, 而非模板匹配.
    """
    report = DeepReport()
    d = chart_data
    
    # 快速索引
    pstars = {p.name: p.stars for p in d.palaces}
    ming_stars = pstars.get("命宫", [])
    shen_palace_name = next((p.name for p in d.palaces if p.is_body), "")
    shen_stars = pstars.get(shen_palace_name, [])
    fude_stars = pstars.get("福德", [])
    guanlu_stars = pstars.get("官禄", [])
    caibo_stars = pstars.get("财帛", [])
    fuqi_stars = pstars.get("夫妻", [])
    jier_stars = pstars.get("疾厄", [])
    qianyi_stars = pstars.get("迁移", [])
    tianzhai_stars = pstars.get("田宅", [])
    zinv_stars = pstars.get("子女", [])
    fumu_stars = pstars.get("父母", [])
    jiaoyou_stars = pstars.get("交友", [])
    xiongdi_stars = pstars.get("兄弟", [])
    
    main_stars_set = {"紫微","天机","太阳","武曲","天同","廉贞",
                      "天府","太阴","贪狼","巨门","天相","天梁","七杀","破军"}
    
    # ── 一、性格分析 ──
    personality_parts = []
    personality_detail_parts = []
    
    # 命宫主星决定性格基调
    ming_mains = [s for s in ming_stars if s in main_stars_set]
    ming_aux = [s for s in ming_stars if s not in main_stars_set]
    
    if ming_mains:
        for star in ming_mains:
            base = PERSONALITY_BASE.get(star, f"{star}坐命, 个性鲜明。")
            personality_parts.append(base)
    
    if not ming_mains:
        # 命无正曜, 借对宫
        opp = OPPOSITE_PALACE.get("命宫","")
        opp_stars = pstars.get(opp, [])
        opp_mains = [s for s in opp_stars if s in main_stars_set]
        if opp_mains:
            personality_parts.append(f"命宫无主星, 借{opp}宫{'、'.join(opp_mains)}为用。性格较受环境左右, 善于适应变化。")
    
    # 身宫影响后半生性格
    if shen_palace_name and shen_stars:
        shen_mains = [s for s in shen_stars if s in main_stars_set]
        if shen_mains:
            personality_detail_parts.append(f"身宫在{shen_palace_name}, {'、'.join(shen_mains)}能量在后半生逐渐显现。")
    
    # 福德宫影响内心世界
    fude_mains = [s for s in fude_stars if s in main_stars_set]
    if fude_mains:
        for star in fude_mains:
            inner = FUDE_INNER.get(star, f"内心世界受{star}影响。")
            personality_detail_parts.append(inner)
    
    # 迁移宫影响对外表现
    qianyi_mains = [s for s in qianyi_stars if s in main_stars_set]
    if qianyi_mains:
        personality_detail_parts.append(f"对外表现: {'、'.join(qianyi_mains)}坐迁移, 在外给人留下{'、'.join(qianyi_mains)}的印象。")
    
    report.personality = "。".join(personality_parts[:3]) + "。"
    report.personality_detail = "\n".join(personality_detail_parts[:4])
    
    # ── 二、事业财运 ──
    career_parts = []
    wealth_parts = []
    
    # 官禄宫
    guanlu_mains = [s for s in guanlu_stars if s in main_stars_set]
    if guanlu_mains:
        for star in guanlu_mains:
            c = CAREER_STAR.get(star, f"{star}守官禄, 事业有发展。")
            career_parts.append(c)
    
    # 财帛宫
    caibo_mains = [s for s in caibo_stars if s in main_stars_set]
    if caibo_mains:
        for star in caibo_mains:
            w = WEALTH_STAR.get(star, f"{star}守财帛, 财运平稳。")
            wealth_parts.append(w)
    
    # 迁移宫对事业的影响
    if "天马" in qianyi_stars:
        career_parts.append("天马在迁移, 宜外出发展, 远行有利事业。")
    if "太阳" in qianyi_stars:
        career_parts.append("太阳在迁移, 远方有贵人, 适合在外地建立事业。")
    
    report.career = "。".join(career_parts[:3]) + "。"
    report.career_detail = _generate_career_detail(guanlu_mains, caibo_mains, d.sihua_map)
    report.wealth = "。".join(wealth_parts[:3]) + "。"
    
    # 财运提示
    if "禄存" in caibo_stars:
        report.wealth_tip = "财帛宫有禄存, 有稳定积蓄运。宜定期储蓄, 建立长期财务规划。"
    elif "擎羊" in caibo_stars or "陀罗" in caibo_stars:
        report.wealth_tip = "财帛宫有煞星, 财运波动较大。宜保守理财, 不宜投机。"
    elif "火星" in caibo_stars or "铃星" in caibo_stars:
        report.wealth_tip = "财帛宫有火铃, 有突发之财也有突发之耗。建议做好预算管理。"
    
    # ── 三、感情婚姻 ──
    rel_parts = []
    fuqi_mains = [s for s in fuqi_stars if s in main_stars_set]
    if fuqi_mains:
        for star in fuqi_mains:
            r = RELATIONSHIP_STAR.get(star, f"{star}守夫妻宫, 感情需用心经营。")
            rel_parts.append(r)
    
    # 桃花星影响
    if "贪狼" in fuqi_stars or "廉贞" in fuqi_stars:
        rel_parts.append("夫妻宫见桃花星, 异性缘旺, 需注意感情界限。")
    if "巨门" in fuqi_stars:
        rel_parts.append("巨门在夫妻宫, 夫妻沟通至关重要, 宜坦诚交流避免猜忌。")
    
    report.relationship = "。".join(rel_parts[:3]) + "。"
    report.relationship_detail = _generate_relationship_detail(fuqi_stars, zinv_stars, fumu_stars)
    
    # ── 四、健康 ──
    health_parts = []
    jier_mains = [s for s in jier_stars if s in main_stars_set]
    sha_in_jier = [s for s in jier_stars if s in ["擎羊","陀罗","火星","铃星","地劫","地空"]]
    
    if jier_mains:
        for star in jier_mains:
            h = HEALTH_STAR.get(star, f"")
            if h: health_parts.append(h)
    
    if sha_in_jier:
        health_parts.append(f"疾厄宫有煞星{'、'.join(sha_in_jier)}, 需注意{'意外伤害' if '擎羊' in sha_in_jier or '火星' in sha_in_jier else '慢性疾病'}。")
    
    report.health = "。".join(health_parts[:3]) + "。" if health_parts else "疾厄宫平稳, 注意日常保健即可。"
    report.health_warning = _generate_health_warning(jier_stars)
    
    # ── 五、关键年龄节点 ──
    report.key_ages = _derive_key_ages(d)
    
    # ── 六、人生建议 ──
    report.advice = _generate_advice(chart_data, interactions)
    
    # ── 七、亮点与警示 ──
    for inter in interactions:
        if inter.rating >= 4:
            report.highlights.append(f"✨ {inter.effect}")
        elif inter.rating <= -2:
            report.cautions.append(f"⚠ {inter.effect}")
    
    # 去重
    report.highlights = list(dict.fromkeys(report.highlights))[:5]
    report.cautions = list(dict.fromkeys(report.cautions))[:5]
    
    return report


# ──────────────────────────────────────
# 详细解读字典
# ──────────────────────────────────────

PERSONALITY_BASE = {
    "紫微": "紫微坐命, 天生具有领袖气质。自尊心强, 行事光明磊落, 一生贵人运佳。",
    "天机": "天机坐命, 思维敏捷, 好奇心强。善于谋划和分析, 但想法多变, 宜专注一行。",
    "太阳": "太阳坐命, 热情开朗, 乐于助人, 人缘极佳。胸怀坦荡, 有强烈正义感。女命有男子气概。",
    "武曲": "武曲坐命, 刚毅果断, 理财能力出众。性格刚硬, 做事坚持到底, 宜刚柔并济。",
    "天同": "天同坐命, 性情温和, 知足常乐。善于协调人际关系, 人缘好, 但有时缺乏进取心。",
    "廉贞": "廉贞坐命, 个性鲜明, 才华横溢。情感丰富, 情绪波动较大, 宜修心养性。",
    "天府": "天府坐命, 稳重务实, 善于经营和理财。一生衣食无忧, 但有时过于保守谨慎。",
    "太阴": "太阴坐命, 温柔细腻, 审美力强。女命端庄贤淑, 男命温文尔雅。注重生活品质。",
    "贪狼": "贪狼坐命, 多才多艺, 善于交际。桃花运强, 魅力四射, 但需节制欲望。",
    "巨门": "巨门坐命, 口才出众, 善于思辨。但易招惹是非口舌, 说话前需三思。",
    "天相": "天相坐命, 正直善良, 人缘极好。善于服务他人, 适合公职或服务行业。",
    "天梁": "天梁坐命, 有长者之风, 乐于助人。性格固执, 好为人师, 但心地善良。",
    "七杀": "七杀坐命, 性格刚烈, 敢作敢为。适合开拓性工作, 但须防冲动决策。",
    "破军": "破军坐命, 个性独立, 不喜约束。一生多变动, 宜顺势而为, 不可强行逆势。",
}

FUDE_INNER = {
    "天同": "内心知足常乐, 精神世界丰富。晚运安逸, 享受生活。",
    "廉贞": "内心世界丰富但也较情绪化。需培养平和心态, 避免精神内耗。",
    "紫微": "内心有强烈的掌控欲, 希望一切尽在掌握。精神追求高。",
    "太阳": "内心光明, 喜欢与人分享。但独处时可能感到空虚。",
    "太阴": "内心细腻敏感, 追求完美。注重精神生活的品质。",
}

CAREER_STAR = {
    "紫微": "紫微守官禄, 适合担任领导职务或自主创业。有统御之才",
    "太阳": "太阳守官禄, 适合公共事业、教育或需要曝光度的工作。光芒四射",
    "武曲": "武曲守官禄, 适合金融、管理、技术等实干型工作。执行力强",
    "天相": "天相守官禄, 适合行政、管理、服务行业。能获得上级赏识",
    "天机": "天机守官禄, 适合策划、咨询、技术研发等动脑型工作。善用智慧",
    "巨门": "巨门守官禄, 适合法律、传媒、教育等以口才见长的工作",
    "七杀": "七杀守官禄, 适合军警、工程、外科等需要决断力的工作。勇往直前",
    "破军": "破军守官禄, 适合开拓创新类工作。不喜按部就班, 宜创业或项目制工作",
}

WEALTH_STAR = {
    "武曲": "武曲守财帛, 为正财星归位。理财能力出众, 宜金融、贸易行业",
    "天府": "天府守财帛, 善于积累财富。理财稳健, 一生积蓄丰厚",
    "太阴": "太阴守财帛, 有积蓄运。宜从事与女性、美丽相关的行业",
    "禄存": "禄存入财帛宫, 财运亨通, 有稳定财源。宜长期投资",
}

RELATIONSHIP_STAR = {
    "太阴": "太阴守夫妻, 配偶温柔体贴。婚姻和谐美满, 家庭幸福",
    "贪狼": "贪狼守夫妻, 桃花运旺, 配偶多才多艺。但需防感情多变",
    "巨门": "巨门守夫妻, 夫妻间沟通至关重要。宜多交流减少误会",
    "天同": "天同守夫妻, 配偶性格温和。婚姻平稳幸福, 无大波澜",
    "紫微": "紫微守夫妻, 配偶有地位或能力。婚姻需要相互尊重与包容",
    "太阳": "太阳守夫妻, 配偶性格开朗。婚姻光明正大, 但需防一方过于强势",
    "廉贞": "廉贞守夫妻, 感情浓烈但也有波折。需用心经营, 方能长久",
}

HEALTH_STAR = {
    "七杀": "疾厄宫七杀, 需注意意外伤害和外科手术。宜定期体检",
    "天机": "疾厄宫天机, 神经系统较敏感。需注意压力管理和睡眠质量",
    "巨门": "疾厄宫巨门, 需注意消化系统和口腔健康。饮食宜清淡",
    "太阳": "疾厄宫太阳, 需注意心血管系统和眼睛。不宜过度劳累",
    "太阴": "疾厄宫太阴, 需注意妇科/泌尿系统和情绪健康",
}


def _generate_career_detail(guanlu_mains, caibo_mains, sihua_map):
    """生成事业财运的详细分析."""
    parts = []
    if guanlu_mains:
        parts.append(f"官禄宫有{'、'.join(guanlu_mains)}, 这决定了您的事业发展方向。")
    if caibo_mains:
        parts.append(f"财运受{'、'.join(caibo_mains)}影响, 理财风格与之相关。")
    if sihua_map:
        sihua_desc = "、".join(f"{s}{t}" for s,t in sihua_map.items())
        parts.append(f"四化'{sihua_desc}'是事业财运的催化剂, 推动具体事务的发展。")
    return "\n".join(parts)


def _generate_relationship_detail(fuqi, zinv, fumu):
    """生成感情婚姻的详细分析."""
    parts = []
    if fuqi:
        parts.append(f"夫妻宫{'、'.join(fuqi[:3])}构成婚姻的基本面貌。")
    if zinv:
        parts.append(f"子女宫星曜影响生育运和亲子关系。")
    if fumu:
        parts.append(f"父母宫{'、'.join(fumu[:3])}暗示原生家庭对婚姻观的影响。")
    return "\n".join(parts)


def _generate_health_warning(jier_stars):
    """生成健康警告."""
    warnings = []
    sha = [s for s in jier_stars if s in ["擎羊","陀罗","火星","铃星"]]
    if "擎羊" in jier_stars: warnings.append("注意意外伤害和外伤。避免危险运动。")
    if "陀罗" in jier_stars: warnings.append("注意慢性疾病和旧伤复发。坚持定期检查。")
    if "火星" in jier_stars: warnings.append("注意急性炎症和突发疾病。保持作息规律。")
    if "铃星" in jier_stars: warnings.append("注意隐匿性疾病。身体不适需及时就医。")
    if "地劫" in jier_stars or "地空" in jier_stars: warnings.append("注意精神健康, 避免过度思虑。")
    return "；".join(warnings[:3])


def _derive_key_ages(chart_data) -> List[dict]:
    """推导关键年龄节点."""
    ages = []
    # 基于大限推导
    for palace, dx_range in chart_data.daxian.items():
        if "-" in dx_range:
            start, end = dx_range.split("-")
            try:
                start_age = int(start)
                if palace == "命宫":
                    ages.append({"age": start_age, "event": "大限始起命宫, 人生进入自主阶段。", "type": "milestone"})
                elif palace == "官禄":
                    ages.append({"age": start_age, "event": "事业大限开启, 职业生涯的重要十年。", "type": "career"})
                elif palace == "夫妻":
                    ages.append({"age": start_age, "event": "感情大限开启, 婚姻和人际关系进入新阶段。", "type": "relationship"})
                elif palace == "财帛":
                    ages.append({"age": start_age, "event": "财运大限开启, 财富积累的关键期。", "type": "wealth"})
            except: pass
    return sorted(ages, key=lambda x: x['age'])[:6]


def _generate_advice(chart_data, interactions) -> str:
    """生成个性化建议."""
    parts = []
    
    # 基于命盘特点
    if chart_data.wuxing_ju <= 2:
        parts.append("局数较低, 早年运势起步较缓。但厚积薄发, 中年后可有大成。建议打好基础, 不急于求成。")
    elif chart_data.wuxing_ju >= 5:
        parts.append("局数较高, 先天条件优越。但需防志得意满, 应保持谦逊和持续学习的心态。")
    
    # 基于星曜互涉
    good_interactions = [i for i in interactions if i.rating >= 3]
    bad_interactions = [i for i in interactions if i.rating <= -2]
    
    if good_interactions:
        parts.append(f"命盘有{len(good_interactions)}个吉利组合, 利用好这些优势可事半功倍。")
    if bad_interactions:
        parts.append(f"命盘有{len(bad_interactions)}个需注意的组合, 在这些领域多加谨慎即可化解。")
    
    return "\n".join(parts)


def generate_enhanced_output(chart_data, interactions, deep_report) -> Dict:
    """生成完整增强输出 (整合所有分析)."""
    return {
        "personality": {
            "summary": deep_report.personality,
            "detail": deep_report.personality_detail,
        },
        "career_wealth": {
            "career": deep_report.career,
            "career_detail": deep_report.career_detail,
            "wealth": deep_report.wealth,
            "wealth_tip": deep_report.wealth_tip,
        },
        "relationship": {
            "summary": deep_report.relationship,
            "detail": deep_report.relationship_detail,
        },
        "health": {
            "summary": deep_report.health,
            "warning": deep_report.health_warning,
        },
        "key_ages": deep_report.key_ages,
        "advice": deep_report.advice,
        "highlights": deep_report.highlights,
        "cautions": deep_report.cautions,
        "interactions": [
            {"type": i.type, "stars": i.stars, "palaces": i.palaces,
             "effect": i.effect, "rating": i.rating, "detail": i.detail}
            for i in interactions[:10]  # Top 10
        ],
    }
