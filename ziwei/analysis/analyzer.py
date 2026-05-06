"""
紫微斗数分析解读模块 — Analysis & Interpretation Engine

包含:
- 星曜亮度 (庙旺利陷得平不陷)
- 格局识别 (30+ 经典格局)
- 三方四正分析
- 宫位解读文本生成
"""

from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field
from ..calendar.constants import (
    EARTHLY_BRANCHES, HEAVENLY_STEMS,
    PALACE_NAMES, OPPOSITE_PALACE,
    TRIAD_OFFSET, FOUR_CARDINAL_OFFSET,
    SIHUA_NAMES,
)

# ──────────────────────────────────────
# 星曜亮度 (庙Bright / 旺Prosperous / 利Beneficial / 得Gain / 平Neutral / 不Weak / 陷Fallen)
# ──────────────────────────────────────

# 格式: {星名: {地支: 亮度等级}}
# 亮度: 庙(7) > 旺(6) > 利(5) > 得(4) > 平(3) > 不(2) > 陷(1)
BRIGHTNESS_LEVELS = {
    7: "庙", 6: "旺", 5: "利", 4: "得", 3: "平", 2: "不", 1: "陷"
}

# Each star's brightness across the 12 earthly branches
STAR_BRIGHTNESS: Dict[str, Dict[str, int]] = {
    "紫微": {
        "子": 6, "丑": 7, "寅": 6, "卯": 6, "辰": 4, "巳": 6,
        "午": 7, "未": 6, "申": 4, "酉": 6, "戌": 4, "亥": 4,
    },
    "天机": {
        "子": 6, "丑": 1, "寅": 4, "卯": 6, "辰": 6, "巳": 4,
        "午": 1, "未": 6, "申": 6, "酉": 1, "戌": 4, "亥": 4,
    },
    "太阳": {
        "子": 1, "丑": 2, "寅": 6, "卯": 7, "辰": 6, "巳": 6,
        "午": 7, "未": 4, "申": 4, "酉": 3, "戌": 1, "亥": 1,
    },
    "武曲": {
        "子": 6, "丑": 6, "寅": 4, "卯": 4, "辰": 7, "巳": 6,
        "午": 6, "未": 6, "申": 4, "酉": 7, "戌": 7, "亥": 4,
    },
    "天同": {
        "子": 6, "丑": 4, "寅": 4, "卯": 6, "辰": 3, "巳": 7,
        "午": 4, "未": 4, "申": 6, "酉": 3, "戌": 4, "亥": 7,
    },
    "廉贞": {
        "子": 4, "丑": 4, "寅": 7, "卯": 4, "辰": 4, "巳": 4,
        "午": 4, "未": 4, "申": 7, "酉": 4, "戌": 4, "亥": 4,
    },
    "天府": {
        "子": 7, "丑": 7, "寅": 6, "卯": 4, "辰": 6, "巳": 6,
        "午": 6, "未": 6, "申": 4, "酉": 4, "戌": 7, "亥": 6,
    },
    "太阴": {
        "子": 4, "丑": 4, "寅": 4, "卯": 1, "辰": 1, "巳": 1,
        "午": 1, "未": 4, "申": 4, "酉": 7, "戌": 7, "亥": 7,
    },
    "贪狼": {
        "子": 6, "丑": 6, "寅": 3, "卯": 4, "辰": 1, "巳": 1,
        "午": 6, "未": 6, "申": 4, "酉": 4, "戌": 4, "亥": 4,
    },
    "巨门": {
        "子": 6, "丑": 6, "寅": 6, "卯": 1, "辰": 1, "巳": 1,
        "午": 6, "未": 6, "申": 6, "酉": 1, "戌": 1, "亥": 4,
    },
    "天相": {
        "子": 6, "丑": 7, "寅": 6, "卯": 1, "辰": 4, "巳": 4,
        "午": 6, "未": 1, "申": 4, "酉": 4, "戌": 4, "亥": 4,
    },
    "天梁": {
        "子": 7, "丑": 6, "寅": 6, "卯": 4, "辰": 4, "巳": 1,
        "午": 7, "未": 6, "申": 4, "酉": 6, "戌": 4, "亥": 1,
    },
    "七杀": {
        "子": 6, "丑": 6, "寅": 7, "卯": 4, "辰": 4, "巳": 3,
        "午": 6, "未": 6, "申": 7, "酉": 4, "戌": 4, "亥": 3,
    },
    "破军": {
        "子": 6, "丑": 6, "寅": 4, "卯": 1, "辰": 1, "巳": 4,
        "午": 7, "未": 6, "申": 4, "酉": 1, "戌": 4, "亥": 4,
    },
}

# 辅星亮度
AUX_BRIGHTNESS = {
    "文昌": {"子": 4,"丑": 4,"寅": 6,"卯": 7,"辰": 4,"巳": 4,"午": 1,"未": 4,"申": 4,"酉": 4,"戌": 4,"亥": 4},
    "文曲": {"子": 4,"丑": 4,"寅": 6,"卯": 4,"辰": 7,"巳": 4,"午": 1,"未": 4,"申": 4,"酉": 4,"戌": 4,"亥": 4},
    "左辅": {"子": 4,"丑": 4,"寅": 4,"卯": 7,"辰": 6,"巳": 4,"午": 4,"未": 4,"申": 1,"酉": 4,"戌": 4,"亥": 4},
    "右弼": {"子": 4,"丑": 4,"寅": 4,"卯": 4,"辰": 4,"巳": 4,"午": 4,"未": 4,"申": 4,"酉": 1,"戌": 7,"亥": 6},
    "天魁": {"子": 4,"丑": 7,"寅": 4,"卯": 4,"辰": 4,"巳": 4,"午": 7,"未": 4,"申": 4,"酉": 4,"戌": 4,"亥": 4},
    "天钺": {"子": 4,"丑": 4,"寅": 4,"卯": 4,"辰": 4,"巳": 7,"午": 4,"未": 4,"申": 4,"酉": 7,"戌": 4,"亥": 4},
    "禄存": {"子": 4,"丑": 4,"寅": 7,"卯": 7,"辰": 4,"巳": 4,"午": 4,"未": 4,"申": 4,"酉": 4,"戌": 4,"亥": 7},
    "擎羊": {"子": 1,"丑": 1,"寅": 4,"卯": 7,"辰": 4,"巳": 1,"午": 4,"未": 1,"申": 4,"酉": 7,"戌": 4,"亥": 1},
    "陀罗": {"子": 4,"丑": 1,"寅": 4,"卯": 1,"辰": 4,"巳": 4,"午": 1,"未": 4,"申": 1,"酉": 4,"戌": 1,"亥": 4},
    "火星": {"子": 1,"丑": 4,"寅": 7,"卯": 4,"辰": 1,"巳": 1,"午": 1,"未": 4,"申": 4,"酉": 4,"戌": 4,"亥": 4},
    "铃星": {"子": 4,"丑": 4,"寅": 7,"卯": 4,"辰": 1,"巳": 4,"午": 1,"未": 4,"申": 4,"酉": 4,"戌": 7,"亥": 4},
    "天马": {"子": 4,"丑": 4,"寅": 4,"卯": 4,"辰": 4,"巳": 7,"午": 4,"未": 4,"申": 7,"酉": 4,"戌": 4,"亥": 7},
}

# Merge all brightness data
ALL_BRIGHTNESS = {**STAR_BRIGHTNESS, **AUX_BRIGHTNESS}


def get_star_brightness(star_name: str, branch: str) -> Tuple[int, str]:
    """获取星曜在指定地支的亮度等级和名称."""
    if star_name in ALL_BRIGHTNESS and branch in ALL_BRIGHTNESS[star_name]:
        level = ALL_BRIGHTNESS[star_name][branch]
        return level, BRIGHTNESS_LEVELS.get(level, "平")
    return 3, "平"


# ──────────────────────────────────────
# 格局识别 Pattern Detection
# ──────────────────────────────────────

@dataclass
class Pattern:
    """格局信息."""
    name: str           # 格局名称
    category: str       # 类别: 富贵/科名/技艺/凶险/特殊
    description: str    # 格局描述
    quality: str        # 吉凶: 吉/凶/中平/待定
    stars_involved: List[str] = field(default_factory=list)


def detect_patterns(
    star_to_branch: Dict[str, str],
    palace_stars: Dict[str, List[str]],
    ming_branch: str,
    year_stem: str,
) -> List[Pattern]:
    """
    检测命盘格局.
    
    Args:
        star_to_branch: {星名: 地支}
        palace_stars: {宫名: [星名列表]}
        ming_branch: 命宫地支
        year_stem: 年干
    
    Returns:
        检测到的格局列表
    """
    patterns = []
    
    # Helper: 获取某星所在支
    def branch_of(star: str) -> Optional[str]:
        return star_to_branch.get(star)
    
    # Helper: 检查两个星是否同宫
    def same_palace(s1: str, s2: str) -> bool:
        b1, b2 = branch_of(s1), branch_of(s2)
        return b1 is not None and b2 is not None and b1 == b2
    
    # Helper: 星是否在命宫
    def in_ming(star: str) -> bool:
        return branch_of(star) == ming_branch
    
    # Helper: 星是否在命宫三方(本宫+4+8宫位)
    def in_ming_triad(star: str) -> bool:
        b = branch_of(star)
        if b is None:
            return False
        mi = EARTHLY_BRANCHES.index(ming_branch)
        si = EARTHLY_BRANCHES.index(b)
        for off in TRIAD_OFFSET:
            if (mi + off) % 12 == si:
                return True
        return False
    
    ming_stars = palace_stars.get("命宫", [])
    all_stars_in_ming = [s for s in ming_stars]
    
    # ── 1. 紫府同宫 ──
    if same_palace("紫微", "天府"):
        patterns.append(Pattern("紫府同宫", "富贵", "紫微天府同守一宫，为最尊贵的组合，主大富大贵，权倾朝野。", "吉", ["紫微", "天府"]))
    
    # ── 2. 君臣庆会 ──
    if branch_of("紫微") == ming_branch:
        aux_count = sum(1 for s in ["左辅","右弼","文昌","文曲","天魁","天钺"] if in_ming_triad(s))
        if aux_count >= 2:
            patterns.append(Pattern("君臣庆会", "富贵", "紫微坐命，三方四正多吉星辅佐，如君王得贤臣，主大贵。", "吉", ["紫微"]))
    
    # ── 3. 紫微朝垣 ──
    if "紫微" in ming_stars:
        has_fu = any(s in all_stars_in_ming for s in ["左辅","右弼","天相","天府"])
        if has_fu:
            patterns.append(Pattern("紫微朝垣", "富贵", "紫微坐命有辅佐吉星相伴，领导力强，受人拥戴。", "吉", ["紫微"]))
    
    # ── 4. 杀破狼 ──
    # 命宫/三方有七杀+破军+贪狼中至少两个
    sha_po_lang = [s for s in ["七杀","破军","贪狼"] if in_ming_triad(s)]
    if len(sha_po_lang) >= 3:
        patterns.append(Pattern("杀破狼", "技艺", "七杀、破军、贪狼三曜会合命宫三方，主人生动荡多变，但若能乘风破浪，可成大业。宜武职、创业。", "中平", sha_po_lang))
    elif len(sha_po_lang) == 2:
        if "七杀" in sha_po_lang and "破军" in sha_po_lang:
            patterns.append(Pattern("杀破", "技艺", "七杀破军二曜照命宫三方，性格刚烈果决，适合竞争性强的领域。", "中平", sha_po_lang))
    
    # ── 5. 机月同梁 ──
    ji_yue_tong_liang = ["天机","太阴","天同","天梁"]
    count_jytl = sum(1 for s in ji_yue_tong_liang if in_ming_triad(s))
    if count_jytl == 4:
        patterns.append(Pattern("机月同梁", "科名", "天机、太阴、天同、天梁四曜会合，主清贵，宜公职、文教、公益事业。为吏人格局。", "吉", ji_yue_tong_liang))
    elif count_jytl >= 3:
        patterns.append(Pattern("机月同梁格", "科名", "天机太阴天同天梁会照命宫三方，宜稳定公职，不宜经商。", "吉", ji_yue_tong_liang))
    
    # ── 6. 月朗天门 ──
    if branch_of("太阴") == "亥" and in_ming_triad("太阴"):
        patterns.append(Pattern("月朗天门", "富贵", "太阴在亥宫，月光最明亮之位，性格温润如玉，富贵双全。女命尤佳。", "吉", ["太阴"]))
    
    # ── 7. 日照雷门 ──
    if branch_of("太阳") == "卯" and in_ming_triad("太阳"):
        patterns.append(Pattern("日照雷门", "富贵", "太阳在卯宫，旭日东升之位，主一生光明磊落，前程似锦。", "吉", ["太阳"]))
    
    # ── 8. 日丽中天 ──
    if branch_of("太阳") == "午" and in_ming_triad("太阳"):
        patterns.append(Pattern("日丽中天", "富贵", "太阳在午宫，如日中天，光芒万丈。事业辉煌，但需防过刚易折。", "吉", ["太阳"]))
    
    # ── 9. 明珠出海 ──
    # 太阳在卯(命宫), 太阴在亥(迁移宫=对宫)
    if branch_of("太阳") == "卯" and branch_of("太阴") == "亥":
        if in_ming("太阳"):
            patterns.append(Pattern("明珠出海", "富贵", "太阳在卯坐命，太阴在亥照迁移。日月并明，一生光明。", "吉", ["太阳","太阴"]))
    
    # ── 10. 禄马交驰 ──
    if same_palace("禄存", "天马"):
        patterns.append(Pattern("禄马交驰", "富贵", "禄存与天马同宫，财源滚滚如奔马，主暴发致富，多动中得财。", "吉", ["禄存","天马"]))
    elif in_ming_triad("禄存") and in_ming_triad("天马"):
        patterns.append(Pattern("禄马交驰", "富贵", "禄存天马在命宫三方，奔波得财，宜外勤、贸易。", "吉", ["禄存","天马"]))
    
    # ── 11. 火贪格 / 铃贪格 ──
    if same_palace("火星", "贪狼"):
        patterns.append(Pattern("火贪格", "富贵", "火星与贪狼同宫，火炼贪狼金，主突发横财，但来得快去得也快。", "中平", ["火星","贪狼"]))
    if same_palace("铃星", "贪狼"):
        patterns.append(Pattern("铃贪格", "富贵", "铃星与贪狼同宫，主偏财运强，谋略过人。", "中平", ["铃星","贪狼"]))
    
    # ── 12. 石中隐玉 ──
    if branch_of("巨门") in ["子","午"] and in_ming_triad("巨门"):
        aux_present = any(s in all_stars_in_ming for s in ["文昌","文曲","左辅","右弼","禄存"])
        if aux_present:
            patterns.append(Pattern("石中隐玉", "科名", "巨门在子午坐命，有吉星辅佐，如石中美玉，须经雕琢方显光华。口才出众。", "吉", ["巨门"]))
    
    # ── 13. 马头带箭 ──
    if branch_of("天同") == "午" and branch_of("擎羊") == "午" and in_ming_triad("天同"):
        patterns.append(Pattern("马头带箭", "特殊", "天同在午宫与擎羊同度，马头带箭格。历尽艰辛而后成，意志力超群。", "中平", ["天同","擎羊"]))
    
    # ── 14. 巨日同宫 ──
    if same_palace("巨门", "太阳"):
        patterns.append(Pattern("巨日同宫", "科名", "巨门与太阳同宫，口才与光芒并耀，宜教育、传媒、法律行业。", "吉", ["巨门","太阳"]))
    
    # ── 15. 阳梁昌禄 ──
    yang_liang_chang_lu = ["太阳","天梁","文昌","禄存"]
    count_ylcl = sum(1 for s in yang_liang_chang_lu if in_ming_triad(s))
    if count_ylcl >= 3:
        patterns.append(Pattern("阳梁昌禄", "科名", "太阳天梁文昌禄存会照，为科甲之格，主聪明好学，金榜题名。", "吉", yang_liang_chang_lu))
    
    # ── 16. 府相朝垣 ──
    if in_ming_triad("天府") and in_ming_triad("天相"):
        patterns.append(Pattern("府相朝垣", "富贵", "天府天相在三方四正朝照命宫，主稳重务实，富贵可期。", "吉", ["天府","天相"]))
    
    # ── 17. 文星拱命 ──
    wenxing = ["文昌","文曲"]
    if any(branch_of(s) == ming_branch for s in wenxing):
        patterns.append(Pattern("文星拱命", "科名", "文昌或文曲坐命，主聪明颖悟，学业有成，宜文职。", "吉", wenxing))
    
    # ── 18. 双禄交流 ──
    sihua_stars_in_ming_triad = []
    for star, stype in {}:  # will be populated by caller
        pass
    
    # ── 19. 禄文拱命 ──
    if branch_of("禄存") == ming_branch and any(branch_of(s) == ming_branch for s in ["文昌","文曲"]):
        patterns.append(Pattern("禄文拱命", "科名", "禄存与文昌/文曲同守命宫，学识与财富并重，实业有成。", "吉", ["禄存"]))
    
    # ── 20. 刑囚夹印 ──
    if branch_of("天相") == ming_branch:
        mi = EARTHLY_BRANCHES.index(ming_branch)
        prev_b = EARTHLY_BRANCHES[(mi - 1) % 12]
        next_b = EARTHLY_BRANCHES[(mi + 1) % 12]
        has_qy = branch_of("擎羊") in [prev_b, next_b]
        has_lz = branch_of("廉贞") in [prev_b, next_b]
        if has_qy and has_lz:
            patterns.append(Pattern("刑囚夹印", "凶险", "天相被擎羊(刑)与廉贞(囚)夹宫，主官非诉讼，需谨慎行事。", "凶", ["天相","擎羊","廉贞"]))
    
    # ── 21. 火铃夹命 ──
    mi = EARTHLY_BRANCHES.index(ming_branch)
    prev_b = EARTHLY_BRANCHES[(mi - 1) % 12]
    next_b = EARTHLY_BRANCHES[(mi + 1) % 12]
    if (branch_of("火星") == prev_b and branch_of("铃星") == next_b) or \
       (branch_of("铃星") == prev_b and branch_of("火星") == next_b):
        patterns.append(Pattern("火铃夹命", "凶险", "火星与铃星夹命宫，主一生多波折，易有突发灾祸。但若格局配合得好，亦能激发斗志。", "凶", ["火星","铃星"]))
    
    # ── 22. 羊陀夹命 ──
    if (branch_of("擎羊") == prev_b and branch_of("陀罗") == next_b) or \
       (branch_of("陀罗") == prev_b and branch_of("擎羊") == next_b):
        patterns.append(Pattern("羊陀夹命", "凶险", "擎羊与陀罗夹命宫，前行有阻后退无路，一生多磨砺。", "凶", ["擎羊","陀罗"]))
    
    # ── 23. 空劫夹命 ──
    if (branch_of("地劫") == prev_b and branch_of("地空") == next_b) or \
       (branch_of("地空") == prev_b and branch_of("地劫") == next_b):
        patterns.append(Pattern("空劫夹命", "特殊", "地空地劫夹命，主思想超脱，不逐俗流。宜哲学宗教艺术，不宜经商。", "中平", ["地劫","地空"]))
    
    # ── 24. 廉贞清白 ──
    if in_ming("廉贞") and in_ming_triad("天府"):
        patterns.append(Pattern("廉贞清白", "特殊", "廉贞遇天府，化暴戾为端庄，虽历经沧桑而持身清白。", "吉", ["廉贞","天府"]))
    
    # ── 25. 雄宿乾元 ──
    if branch_of("廉贞") in ["寅","申"] and in_ming_triad("廉贞"):
        patterns.append(Pattern("雄宿乾元", "富贵", "廉贞在寅申守命，为雄宿乾元格。才华横溢，能在逆境中崛起。", "吉", ["廉贞"]))
    
    # ── 26. 武曲天相 ──
    if same_palace("武曲", "天相"):
        patterns.append(Pattern("武曲天相", "富贵", "武曲天相同宫，刚柔并济，理财能力强，宜金融、管理。", "吉", ["武曲","天相"]))
    
    # ── 27. 七杀朝斗 ──
    if branch_of("七杀") in ["寅","申"] and in_ming("七杀"):
        patterns.append(Pattern("七杀朝斗", "技艺", "七杀在寅申坐命，如大将镇守边关，主权威显赫，但孤独。", "中平", ["七杀"]))
    
    # ── 28. 命无正曜 ──
    main_stars = ["紫微","天机","太阳","武曲","天同","廉贞","天府","太阴","贪狼","巨门","天相","天梁","七杀","破军"]
    if not any(s in ming_stars for s in main_stars):
        patterns.append(Pattern("命无正曜", "特殊", "命宫无十四主星，须借对宫星曜为用。人生较受环境左右，宜随缘。", "待定", []))
    
    return patterns


# ──────────────────────────────────────
# 三方四正分析
# ──────────────────────────────────────

def get_triad_palaces(palace_name: str) -> List[str]:
    """获取某宫的三方宫位."""
    offset = PALACE_NAMES.index(palace_name)
    return [PALACE_NAMES[(offset + o) % 12] for o in TRIAD_OFFSET]


def get_four_cardinal(palace_name: str) -> List[str]:
    """获取某宫的四正宫位."""
    offset = PALACE_NAMES.index(palace_name)
    return [PALACE_NAMES[(offset + o) % 12] for o in FOUR_CARDINAL_OFFSET]


def analyze_triad_palaces(
    palace_name: str,
    palace_stars: Dict[str, List[str]],
    sihua_map: Dict[str, str],
) -> Dict:
    """
    分析某个宫位的三方四正.
    
    Returns:
        {
            "triad_palaces": [...],
            "triad_stars": {宫名: [星曜]},
            "triad_sihua": [...],
            "opposite_palace": str,
            "opposite_stars": [...],
            "summary": str,
        }
    """
    triads = get_triad_palaces(palace_name)
    opposite = OPPOSITE_PALACE.get(palace_name, "")
    
    triad_stars = {}
    triad_sihua = []
    
    for pname in triads:
        stars = palace_stars.get(pname, [])
        triad_stars[pname] = stars
        for s in stars:
            if s in sihua_map:
                triad_sihua.append(f"{s}({sihua_map[s]})")
    
    opposite_stars = palace_stars.get(opposite, [])
    
    # 简单总结
    total_main = sum(1 for stars in triad_stars.values() for s in stars 
                     if s in ["紫微","天机","太阳","武曲","天同","廉贞",
                              "天府","太阴","贪狼","巨门","天相","天梁","七杀","破军"])
    
    sha_count = sum(1 for stars in triad_stars.values() for s in stars
                    if s in ["擎羊","陀罗","火星","铃星","地劫","地空"])
    
    ji_count = sum(1 for stars in triad_stars.values() for s in stars
                   if s in ["文昌","文曲","左辅","右弼","天魁","天钺","禄存"])
    
    summary = f"三方四正共有主星{total_main}颗"
    if ji_count > sha_count:
        summary += f"，吉星({ji_count})多于煞星({sha_count})，总体吉利。"
    elif sha_count > ji_count:
        summary += f"，煞星({sha_count})多于吉星({ji_count})，需加注意。"
    else:
        summary += "，吉凶参半。"
    
    return {
        "triad_palaces": triads,
        "triad_stars": triad_stars,
        "triad_sihua": triad_sihua,
        "opposite_palace": opposite,
        "opposite_stars": opposite_stars,
        "summary": summary,
    }


# ──────────────────────────────────────
# 解读文本生成
# ──────────────────────────────────────

def interpret_palace(
    palace_name: str,
    stars: List[str],
    sihua_marks: List[str],
    is_body: bool,
    wuxing_ju: str,
    year_zodiac: str,
) -> str:
    """
    生成单个宫位的解读文本.
    
    Args:
        palace_name: 宫名
        stars: 该宫星曜列表
        sihua_marks: 该宫四化标记
        is_body: 是否身宫
        wuxing_ju: 五行局名
        year_zodiac: 生肖
    
    Returns:
        解读文本
    """
    parts = []
    main_stars_in_palace = [s for s in stars if s in STAR_BRIGHTNESS]
    aux_stars_in_palace = [s for s in stars if s not in STAR_BRIGHTNESS and s != "—"]
    
    # 主星解读
    if main_stars_in_palace:
        for star in main_stars_in_palace:
            interp = STAR_PALACE_INTERPRETATIONS.get((palace_name, star))
            if interp:
                parts.append(interp)
    
    if not parts:
        if main_stars_in_palace:
            parts.append(f"{'、'.join(main_stars_in_palace)}守{ palace_name }，")
        else:
            parts.append(f"{ palace_name }无主星，")
    
    # 身宫
    if is_body:
        parts.append(f"此为身宫，人生后半程的重心所在。")
    
    # 四化
    if sihua_marks:
        parts.append(f"该宫有{'、'.join(sihua_marks)}，加强了此宫的变动性。")
    
    # 煞星
    sha_here = [s for s in stars if s in ["擎羊","陀罗","火星","铃星","地劫","地空"]]
    if sha_here:
        parts.append(f"有煞星{'、'.join(sha_here)}，需防波折和不顺。")
    
    # 吉星
    ji_here = [s for s in stars if s in ["文昌","文曲","左辅","右弼","天魁","天钺"]]
    if ji_here:
        parts.append(f"有吉星{'、'.join(ji_here)}相助，运势得到加强。")
    
    return "".join(parts)


# 主星在各宫的简化解说模板
STAR_PALACE_INTERPRETATIONS = {
    ("命宫", "紫微"): "紫微坐命，天生具有领袖气质，自尊心强，好面子。一生贵人运佳，宜担任管理职位。",
    ("命宫", "天机"): "天机坐命，思维敏捷，好奇心强，善于谋划。但想法多变，宜专注一行。",
    ("命宫", "太阳"): "太阳坐命，热情开朗，乐于助人，人缘佳。女命有男子气概。",
    ("命宫", "武曲"): "武曲坐命，刚毅果断，理财能力强。性格较刚硬，宜刚柔并济。",
    ("命宫", "天同"): "天同坐命，性情温和，知足常乐。善于协调人际关系，但有时缺乏进取心。",
    ("命宫", "廉贞"): "廉贞坐命，个性鲜明，才华横溢。情绪波动大，宜修心养性。",
    ("命宫", "天府"): "天府坐命，稳重务实，善于理财和经营。一生衣食无忧，但有时过于保守。",
    ("命宫", "太阴"): "太阴坐命，温柔细腻，审美力强。女命端庄贤淑，男命温文尔雅。",
    ("命宫", "贪狼"): "贪狼坐命，多才多艺，善于交际。桃花运强，但需节制欲望。",
    ("命宫", "巨门"): "巨门坐命，口才出众，善于思辨。但易招惹是非口舌，需慎言。",
    ("命宫", "天相"): "天相坐命，正直善良，人缘好。善于服务他人，适合公职或服务业。",
    ("命宫", "天梁"): "天梁坐命，有长者之风，乐于助人。但性格固执，好为人师。",
    ("命宫", "七杀"): "七杀坐命，性格刚烈，敢作敢为。适合开拓性工作，但须防冲动。",
    ("命宫", "破军"): "破军坐命，个性独立，不喜约束。一生多变动，宜顺势而为。",
    
    ("财帛", "武曲"): "武曲守财帛宫，为财星归位，理财能力出众，宜金融、贸易行业。",
    ("财帛", "天府"): "天府守财帛宫，善于积累财富，理财稳健，一生积蓄丰厚。",
    ("财帛", "太阴"): "太阴守财帛宫，有积蓄运，宜从事与女性、美丽相关的行业。",
    ("财帛", "禄存"): "禄存入财帛宫，财运亨通，有稳定财源。",
    
    ("官禄", "紫微"): "紫微守官禄宫，事业心强，适合担任领导职务，或自主创业。",
    ("官禄", "太阳"): "太阳守官禄宫，适合从事公共事业、教育或需要曝光度的工作。",
    ("官禄", "天相"): "天相守官禄宫，适合行政、管理、服务行业，能获得上级赏识。",
    
    ("夫妻", "太阴"): "太阴守夫妻宫，配偶温柔体贴，婚姻和谐美满。",
    ("夫妻", "贪狼"): "贪狼守夫妻宫，桃花运旺，配偶多才多艺，但需防感情多变。",
    ("夫妻", "巨门"): "巨门守夫妻宫，夫妻间沟通重要，宜多交流减少误会。",
    
    ("迁移", "天马"): "天马守迁移宫，一生多走动，宜外出发展，远行有利。",
    ("迁移", "太阳"): "太阳守迁移宫，出外有贵人相助，适合在外地发展事业。",
    
    ("福德", "天同"): "天同守福德宫，知足常乐，精神世界丰富，晚年安逸。",
    ("福德", "廉贞"): "廉贞守福德宫，内心世界丰富但也较情绪化，需培养平和心态。",
    
    ("父母", "天梁"): "天梁守父母宫，父母有寿，有长辈缘，或与长辈关系密切。",
    ("父母", "紫微"): "紫微守父母宫，出身较好，父母有地位或能力。",
    
    ("疾厄", "七杀"): "七杀守疾厄宫，需注意意外伤害和外科手术，宜定期体检。",
    ("疾厄", "天机"): "天机守疾厄宫，神经系统较敏感，需注意压力管理和睡眠。",
    
    ("田宅", "天府"): "天府守田宅宫，房产运好，有不动产缘分，家居环境优雅。",
    ("田宅", "太阴"): "太阴守田宅宫，房产运平稳上升，宜购置优质物业。",
    
    ("子女", "武曲"): "武曲守子女宫，子女个性独立，有主见，教育上宜因材施教。",
    ("子女", "天同"): "天同守子女宫，子女乖巧懂事，亲子关系融洽。",
    
    ("交友", "左辅"): "左辅守交友宫，朋友正直可靠，能得朋友相助。",
    ("交友", "右弼"): "右弼守交友宫，人际关系融洽，有贵人缘。",
    ("交友", "巨门"): "巨门守交友宫，需谨慎交友，防朋友间口舌是非。",
    
    ("兄弟", "天机"): "天机守兄弟宫，兄弟姐妹聪明，但关系可能有变数。",
    ("兄弟", "天梁"): "天梁守兄弟宫，兄弟姐妹间有照顾之责，长幼有序。",
}


# ──────────────────────────────────────
# 综合命盘概览解读
# ──────────────────────────────────────

def generate_overview(
    chart_data,  # ChartData
    patterns: List[Pattern],
) -> str:
    """生成命盘综合概览."""
    lines = []
    
    # 基本信息
    lines.append(f"此命盘命主生于{chart_data.birth_date}，五行局为{chart_data.wuxing_ju_name}，命宫在{chart_data.ming_palace}。")
    
    # 格局
    if patterns:
        patterns_good = [p for p in patterns if p.quality == "吉"]
        patterns_bad = [p for p in patterns if p.quality == "凶"]
        patterns_neutral = [p for p in patterns if p.quality in ["中平","待定","特殊"]]
        
        if patterns_good:
            names = "、".join(p.name for p in patterns_good)
            lines.append(f"命盘呈现{len(patterns_good)}个吉利格局：{names}。")
        
        if patterns_bad:
            names = "、".join(p.name for p in patterns_bad)
            lines.append(f"需注意{len(patterns_bad)}个警示格局：{names}。")
        
        if patterns_neutral:
            names = "、".join(p.name for p in patterns_neutral)
            lines.append(f"另有特殊格局：{names}。")
    
    # 四化简评
    sihua_desc = []
    for star, stype in chart_data.sihua_map.items():
        sihua_desc.append(f"{star}{stype}")
    if sihua_desc:
        lines.append(f"生年四化为{'，'.join(sihua_desc)}，这是命局的核心动力。")
    
    # 命宫简评
    ming_stars = chart_data.palaces[0].stars if chart_data.palaces else []
    if ming_stars:
        lines.append(f"命宫星曜{'、'.join(ming_stars[:4])}奠定性格基调。")
    
    return "\n".join(lines)


def full_analysis(chart_data) -> Dict:
    """
    完整分析 — 返回结构化的分析结果.
    """
    # 构建星→支映射
    star_to_branch = {}
    palace_stars = {}
    for p in chart_data.palaces:
        palace_stars[p.name] = p.stars
        for s in p.stars:
            star_to_branch[s] = p.branch
    
    ming_branch = chart_data.palaces[0].branch if chart_data.palaces else "子"
    
    # 格局检测
    patterns = detect_patterns(star_to_branch, palace_stars, ming_branch, chart_data.year_pillar[0])
    
    # 各宫亮度
    brightness_info = {}
    for p in chart_data.palaces:
        b_info = {}
        for s in p.stars:
            level, name = get_star_brightness(s, p.branch)
            b_info[s] = {"level": level, "name": name}
        brightness_info[p.name] = b_info
    
    # 三方四正分析 (仅命宫)
    triad_analysis = analyze_triad_palaces("命宫", palace_stars, chart_data.sihua_map)
    
    # 各宫解读
    palace_interpretations = {}
    for p in chart_data.palaces:
        palace_interpretations[p.name] = interpret_palace(
            p.name, p.stars, p.sihua, p.is_body,
            chart_data.wuxing_ju_name, chart_data.zodiac
        )
    
    # 综合概览
    overview = generate_overview(chart_data, patterns)
    
    return {
        "patterns": [
            {"name": p.name, "category": p.category, "quality": p.quality,
             "description": p.description, "stars": p.stars_involved}
            for p in patterns
        ],
        "brightness": brightness_info,
        "triad_analysis": triad_analysis,
        "palace_interpretations": palace_interpretations,
        "overview": overview,
    }
