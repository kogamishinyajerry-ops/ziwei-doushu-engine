"""
命格个性系统 — DestinyProfile & Dimension Radar

为小红书分享场景设计:
- 命码 (Destiny Code): 类似 MBTI 的 4-5 字母代号
- 五维雷达: 命·运·才·情·煞 五大维度评分
- 天性词云: 3-5 个核心性格关键词
- 适合/不适合: SBTI 风格的职业/关系建议
"""

import hashlib
import random
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field

from ..calendar.constants import (
    EARTHLY_BRANCHES, PALACE_NAMES,
    SIHUA_NAMES,
)

# ══════════════════════════════════════════════════════════════
# 命码系统 — Destiny Code
# ══════════════════════════════════════════════════════════════

MAIN_STARS = {"紫微","天机","太阳","武曲","天同","廉贞",
              "天府","太阴","贪狼","巨门","天相","天梁","七杀","破军"}

STAR_CODE_MAP = {
    "紫微": "紫", "天机": "机", "太阳": "阳", "武曲": "武",
    "天同": "同", "廉贞": "贞", "天府": "府", "太阴": "阴",
    "贪狼": "贪", "巨门": "巨", "天相": "相", "天梁": "梁",
    "七杀": "杀", "破军": "破",
}

STAR_EMOJI = {
    "紫微": "👑", "天机": "🧠", "太阳": "☀️", "武曲": "⚔️",
    "天同": "🌟", "廉贞": "🎭", "天府": "🏛️", "太阴": "🌙",
    "贪狼": "💫", "巨门": "🗣️", "天相": "🤝", "天梁": "🦉",
    "七杀": "🗡️", "破军": "💥",
}

# 命码格式: [命宫主星码][身宫主星码][四化特征码][特殊标记]
# 例子: "紫阳·文昌·天梁" → 紫微/太阳 + 文昌加持 + 天梁庇护


def generate_destiny_code(
    ming_stars: List[str],
    shen_stars: List[str],
    sihua_stars: List[str],
    star_to_branch: Dict[str, str],
) -> Dict:
    """
    生成个性化命码.
    
    Returns:
        {
            "code": "紫阳·文昌",
            "full_name": "紫阳·文昌·天梁",
            "emoji": "👑☀️",
            "element": "火",
            "tagline": "帝王之光，照耀四方",
            "rarity_percentile": 87,
            "keywords": ["领导力", "创造力", "正义感"],
        }
    """
    # 1. 提取命宫/身宫主星 (命宫无主星时借对宫)
    ming_mains = [s for s in ming_stars if s in MAIN_STARS]
    shen_mains = [s for s in shen_stars if s in MAIN_STARS]
    
    # 命宫无主星 → 借迁移宫
    if not ming_mains:
        from ..calendar.constants import OPPOSITE_PALACE
        qianyi_name = OPPOSITE_PALACE.get("命宫", "迁移")
        # 尝试从 star_to_branch 反向找迁移宫星曜
        qianyi_stars = []
        for star, branch in star_to_branch.items():
            if star in MAIN_STARS:
                # 查找迁移宫对应的branch (命宫对宫)
                qianyi_stars.append(star)
        # 简化: 取所有主星中不在命宫的作为候补
        all_main_stars = [s for s, b in star_to_branch.items() if s in MAIN_STARS]
        ming_mains = all_main_stars[:2]  # 取前2个作为借星
    
    primary_stars = ming_mains[:2]
    if len(primary_stars) < 2 and shen_mains:
        primary_stars += [s for s in shen_mains if s not in primary_stars]
    # 如果还是没有, 从所有主星中取
    if not primary_stars:
        all_mains = [s for s, b in star_to_branch.items() if s in MAIN_STARS]
        primary_stars = all_mains[:2]
    
    # 2. 找最强的吉星加持
    auspicious = ["文昌","文曲","左辅","右弼","天魁","天钺","禄存","天马"]
    auspicious_present = [s for s in ming_stars + shen_stars if s in auspicious]
    # 如果命宫没有吉星, 从全盘找
    if not auspicious_present:
        auspicious_present = [s for s, b in star_to_branch.items() if s in auspicious][:2]
    
    # 3. 找特殊标记 (煞星/桃花/特殊配置)
    sha_stars = ["擎羊","陀罗","火星","铃星","地劫","地空"]
    sha_present = [s for s in ming_stars + shen_stars if s in sha_stars]
    tao_stars = ["贪狼","廉贞","太阴"]
    tao_present = [s for s in ming_stars + shen_stars if s in tao_stars]
    
    # 4. 构建命码
    code_parts = []
    for s in primary_stars[:2]:
        if s in STAR_CODE_MAP:
            code_parts.append(STAR_CODE_MAP[s])
    
    full_name_parts = []
    for s in primary_stars[:3]:
        full_name_parts.append(s)
    
    if auspicious_present and len(full_name_parts) < 3:
        full_name_parts.append(auspicious_present[0])
        code_parts.append(auspicious_present[0][:2])
    
    # 命码字符串
    code_str = "·".join(code_parts) if code_parts else "天命"
    full_name = "·".join(full_name_parts) if full_name_parts else "天命未定"
    
    # Emoji 组合
    emoji = ""
    for s in primary_stars[:2]:
        emoji += STAR_EMOJI.get(s, "✨")
    
    # 5. 确定五行元素
    element_map = {
        "紫微":"土", "天机":"木", "太阳":"火", "武曲":"金",
        "天同":"水", "廉贞":"火", "天府":"土", "太阴":"水",
        "贪狼":"木", "巨门":"水", "天相":"水", "天梁":"土",
        "七杀":"金", "破军":"水",
    }
    elements = [element_map.get(s, "") for s in primary_stars if s in element_map]
    dominant_element = max(set(elements), key=elements.count) if elements else "土"
    
    # 6. 角色关键词
    keyword_map = {
        "紫微": ["领导力","统御","格局"],
        "天机": ["智谋","分析","变通"],
        "太阳": ["热情","正义","感染力"],
        "武曲": ["刚毅","执行","财富"],
        "天同": ["和谐","福气","知足"],
        "廉贞": ["才华","热情","执着"],
        "天府": ["稳重","经营","积累"],
        "太阴": ["细腻","审美","直觉"],
        "贪狼": ["魅力","社交","才艺"],
        "巨门": ["口才","思辨","求真"],
        "天相": ["公正","服务","协调"],
        "天梁": ["智慧","庇护","长者"],
        "七杀": ["勇气","决断","开拓"],
        "破军": ["创新","变革","独立"],
    }
    
    keywords = []
    for s in primary_stars[:2]:
        if s in keyword_map:
            keywords.extend(keyword_map[s][:2])
    # 如果主星没产生关键词, 用吉星
    if not keywords:
        for s in auspicious_present[:2]:
            gk_map = {"文昌":"文采","文曲":"才艺","左辅":"贵人","右弼":"人缘","天魁":"科名","天钺":"功名","禄存":"财富","天马":"奔波"}
            if s in gk_map:
                keywords.append(gk_map[s])
    # 仍然没有就用元素
    if not keywords:
        elem_kw = {"金":"坚韧","木":"生机","水":"智慧","火":"热情","土":"稳重"}
        keywords = [elem_kw.get(dominant_element, "独特")]
    keywords = list(dict.fromkeys(keywords))[:3]  # 去重取前3
    
    # 7. 角色标语
    taglines = {
        ("紫微","太阳"): "帝王之光，照耀四方",
        ("紫微","天相"): "贤君良相，天下归心",
        ("紫微","破军"): "铁血君王，破而后立",
        ("太阳","紫微"): "帝王之光，照耀四方",
        ("天相","紫微"): "贤君良相，天下归心",
        ("破军","紫微"): "铁血君王，破而后立",
        ("紫微","七杀"): "紫微统御，杀破千军",
        ("七杀","紫微"): "紫微统御，杀破千军",
        ("紫微","天府"): "紫府同辉，至尊至贵",
        ("天府","紫微"): "紫府同辉，至尊至贵",
        ("太阳","巨门"): "光芒之舌，以言服人",
        ("巨门","太阳"): "光芒之舌，以言服人",
        ("天机","天梁"): "神机妙算，慧眼如炬",
        ("天梁","天机"): "神机妙算，慧眼如炬",
        ("武曲","天府"): "金玉满堂，富甲一方",
        ("天府","武曲"): "金玉满堂，富甲一方",
        ("武曲","七杀"): "刚勇果决，一往无前",
        ("七杀","武曲"): "刚勇果决，一往无前",
        ("天同","太阴"): "温润如玉，静水流深",
        ("太阴","天同"): "温润如玉，静水流深",
        ("廉贞","贪狼"): "绝代风华，才情无双",
        ("贪狼","廉贞"): "绝代风华，才情无双",
        ("贪狼","武曲"): "欲望与实力并存",
        ("武曲","贪狼"): "欲望与实力并存",
        ("七杀","破军"): "破阵先锋，勇冠三军",
        ("破军","七杀"): "破阵先锋，勇冠三军",
        ("太阴","天同"): "月下安眠，福泽绵长",
        ("天府","天相"): "稳重辅臣，国之栋梁",
        ("天相","天府"): "稳重辅臣，国之栋梁",
    }
    
    # 单个主星的标语
    solo_taglines = {
        "紫微": "帝王之星，注定不凡",
        "天机": "神机妙算，智者千虑",
        "太阳": "光芒万丈，照破山河",
        "武曲": "刚毅果决，财运亨通",
        "天同": "福星高照，知足常乐",
        "廉贞": "才华横溢，至情至性",
        "天府": "稳重如山，财库丰盈",
        "太阴": "温润如玉，静水流深",
        "贪狼": "魅力无边，多才多艺",
        "巨门": "口若悬河，明辨是非",
        "天相": "正直善良，辅佐之才",
        "天梁": "德高望重，福寿绵长",
        "七杀": "勇往直前，所向披靡",
        "破军": "破旧立新，天地重塑",
    }
    
    key = tuple(sorted(primary_stars[:2])) if len(primary_stars) >= 2 else None
    if key and key in taglines:
        tagline = taglines[key]
    elif primary_stars and primary_stars[0] in solo_taglines:
        tagline = solo_taglines[primary_stars[0]]
    elif primary_stars:
        tagline = f"{'、'.join(primary_stars[:2])}之命，独特不凡"
    else:
        tagline = "天命难测，自成一体"
    
    return {
        "code": code_str,
        "full_name": full_name,
        "emoji": emoji or "✨",
        "element": dominant_element,
        "tagline": tagline,
        "keywords": keywords,
        "primary_stars": primary_stars[:3],
        "auspicious_bonus": auspicious_present[:2],
        "shadow_mark": sha_present[:1],
    }


# ══════════════════════════════════════════════════════════════
# 五维雷达 — 命·运·才·情·煞
# ══════════════════════════════════════════════════════════════

@dataclass
class Dimension:
    name: str       # 维度名
    emoji: str      # 图标
    score: int      # 0-100
    label: str      # 等级标签
    description: str  # 一句话解读


def calculate_dimensions(
    chart_data,
    palace_stars: Dict[str, List[str]],
    star_to_branch: Dict[str, str],
    sihua_map: Dict[str, str],
    interactions: List,
) -> Dict[str, Dimension]:
    """
    计算五维个性雷达.
    
    维度:
    - 命 (Destiny): 命宫强度 + 格局 + 先天条件
    - 运 (Fortune): 四化 + 大限 + 贵人运
    - 才 (Talent): 文昌文曲 + 专业技能
    - 情 (Heart): 桃花星 + 情感丰富度
    - 煞 (Challenge): 煞星配置 + 人生课题
    """
    ming_stars = palace_stars.get("命宫", [])
    
    # ── 命 (天命禀赋) 0-100 ──
    destiny_score = 50
    # 命宫有主星 +20
    ming_mains = [s for s in ming_stars if s in MAIN_STARS]
    if ming_mains:
        destiny_score += min(len(ming_mains) * 15, 30)
    # 有吉星加持 +10
    ji_in_ming = [s for s in ming_stars if s in ["文昌","文曲","左辅","右弼","天魁","天钺"]]
    destiny_score += min(len(ji_in_ming) * 5, 15)
    # 格局好 +15
    good_interactions = [i for i in interactions if hasattr(i, 'rating') and i.rating >= 3]
    destiny_score += min(len(good_interactions) * 3, 15)
    # 五行局高 +10
    if chart_data.wuxing_ju >= 5:
        destiny_score += 10
    destiny_score = max(0, min(100, destiny_score))
    
    # ── 运 (运势机遇) 0-100 ──
    fortune_score = 50
    # 四化加持
    sihua_count = len(sihua_map)
    fortune_score += sihua_count * 8
    # 禄存/天马
    if "禄存" in ming_stars:
        fortune_score += 10
    if "天马" in ming_stars:
        fortune_score += 5
    # 迁移宫好
    qianyi_stars = palace_stars.get("迁移", [])
    qianyi_mains = [s for s in qianyi_stars if s in MAIN_STARS]
    if qianyi_mains:
        fortune_score += 8
    fortune_score = max(0, min(100, fortune_score))
    
    # ── 才 (才华技能) 0-100 ──
    talent_score = 50
    # 文昌文曲
    wenchang_pos = star_to_branch.get("文昌", "")
    wenqu_pos = star_to_branch.get("文曲", "")
    ming_branch = chart_data.palaces[0].branch if chart_data.palaces else ""
    if wenchang_pos == ming_branch:
        talent_score += 15
    if wenqu_pos == ming_branch:
        talent_score += 15
    # 天机/廉贞/贪狼 在命宫三方
    mi = EARTHLY_BRANCHES.index(ming_branch) if ming_branch in EARTHLY_BRANCHES else 0
    triad_branches = [EARTHLY_BRANCHES[(mi + o) % 12] for o in [0, 4, 8]]
    creative_stars = {"天机","廉贞","贪狼","太阳"}
    for star, branch in star_to_branch.items():
        if star in creative_stars and branch in triad_branches:
            talent_score += 5
    talent_score = max(0, min(100, talent_score))
    
    # ── 情 (情感丰度) 0-100 ──
    heart_score = 50
    peach_stars = {"贪狼","廉贞","太阴","天同","文昌","文曲"}
    for star, branch in star_to_branch.items():
        if star in peach_stars and branch in triad_branches:
            heart_score += 8
    # 夫妻宫
    fuqi_stars = palace_stars.get("夫妻", [])
    fuqi_mains = [s for s in fuqi_stars if s in MAIN_STARS]
    if fuqi_mains:
        heart_score += 10
    if "红鸾" in star_to_branch:
        heart_score += 5
    if "天喜" in star_to_branch:
        heart_score += 5
    heart_score = max(0, min(100, heart_score))
    
    # ── 煞 (挑战课题) 0-100 ──
    challenge_score = 30  # 基线
    sha_stars = ["擎羊","陀罗","火星","铃星","地劫","地空"]
    for star, branch in star_to_branch.items():
        if star in sha_stars:
            if branch in triad_branches:
                challenge_score += 12
            elif branch == ming_branch:
                challenge_score += 20
    # 化忌在命宫
    for star, stype in sihua_map.items():
        if stype == "化忌":
            if star_to_branch.get(star) == ming_branch:
                challenge_score += 15
            elif star_to_branch.get(star) in triad_branches:
                challenge_score += 8
    challenge_score = max(0, min(100, challenge_score))
    
    def _label(score: int, high_is_good: bool = True) -> str:
        if score >= 90: return "登峰造极" if high_is_good else "险象环生"
        if score >= 75: return "出类拔萃" if high_is_good else "波折不断"
        if score >= 60: return "中上之资" if high_is_good else "偶有波澜"
        if score >= 45: return "中正平和"
        if score >= 30: return "中下之资" if high_is_good else "少有阻碍"
        return "尚待发掘" if high_is_good else "一路坦途"
    
    def _destiny_desc(score: int) -> str:
        if score >= 80: return "天生不凡，注定要走不寻常的路"
        if score >= 60: return "命格扎实，有成就大业的潜质"
        if score >= 40: return "中正平和，稳扎稳打亦有收获"
        return "命格清奇，以柔克刚方为上策"
    
    def _fortune_desc(score: int) -> str:
        if score >= 80: return "贵人环绕，机遇如雨后春笋"
        if score >= 60: return "运势平稳上升，把握关键节点"
        if score >= 40: return "运势中庸，需主动创造机会"
        return "运势起伏较大，耐心等待时机"
    
    def _talent_desc(score: int) -> str:
        if score >= 80: return "天纵之才，多领域皆有建树"
        if score >= 60: return "才思敏捷，专业领域能成大器"
        if score >= 40: return "勤能补拙，专注一处必有收获"
        return "才华内敛，适合深度钻研而非广撒网"
    
    def _heart_desc(score: int) -> str:
        if score >= 80: return "情感丰沛，是人群中的暖阳"
        if score >= 60: return "有情有义，人际关系处理得当"
        if score >= 40: return "情感内敛，重在质量而非数量"
        return "理性主导，情感世界自给自足"
    
    def _challenge_desc(score: int) -> str:
        if score >= 80: return "挫折是成长的阶梯，越战越勇"
        if score >= 60: return "人生有波折，但每次都能化险为夷"
        if score >= 40: return "偶有挑战，整体平顺"
        return "人生道路较为顺畅，少有大的波折"
    
    return {
        "destiny": Dimension("天命", "🔮", destiny_score, _label(destiny_score), _destiny_desc(destiny_score)),
        "fortune": Dimension("机遇", "🍀", fortune_score, _label(fortune_score), _fortune_desc(fortune_score)),
        "talent": Dimension("才华", "🎨", talent_score, _label(talent_score), _talent_desc(talent_score)),
        "heart": Dimension("情缘", "💝", heart_score, _label(heart_score), _heart_desc(heart_score)),
        "challenge": Dimension("课题", "⚡", challenge_score, _label(challenge_score, False), _challenge_desc(challenge_score)),
    }


# ══════════════════════════════════════════════════════════════
# 随机化个性化 — 风格变体
# ══════════════════════════════════════════════════════════════

# 元素主题色
ELEMENT_THEMES = {
    "金": {
        "primary": "#d4a853", "bg": "linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)",
        "accent": "#e2c174", "glow": "0 0 20px rgba(212,168,83,0.3)",
        "card_bg": "rgba(212,168,83,0.06)", "border": "rgba(212,168,83,0.2)",
        "name": "鎏金", "vibe": "尊贵不凡，金光璀璨",
    },
    "木": {
        "primary": "#4ade80", "bg": "linear-gradient(135deg, #0a1a0a 0%, #0d2818 50%, #0a2e1a 100%)",
        "accent": "#6ee7a7", "glow": "0 0 20px rgba(74,222,128,0.3)",
        "card_bg": "rgba(74,222,128,0.06)", "border": "rgba(74,222,128,0.2)",
        "name": "青木", "vibe": "生机勃勃，万物生长",
    },
    "水": {
        "primary": "#60a5fa", "bg": "linear-gradient(135deg, #0a0a2e 0%, #0d1642 50%, #0a1a3a 100%)",
        "accent": "#93c5fd", "glow": "0 0 20px rgba(96,165,250,0.3)",
        "card_bg": "rgba(96,165,250,0.06)", "border": "rgba(96,165,250,0.2)",
        "name": "深海", "vibe": "深邃如海，智慧流动",
    },
    "火": {
        "primary": "#f97316", "bg": "linear-gradient(135deg, #1a0a0a 0%, #2e0d0d 50%, #3a0a0a 100%)",
        "accent": "#fb923c", "glow": "0 0 20px rgba(249,115,22,0.3)",
        "card_bg": "rgba(249,115,22,0.06)", "border": "rgba(249,115,22,0.2)",
        "name": "赤焰", "vibe": "热情似火，活力四射",
    },
    "土": {
        "primary": "#a78bfa", "bg": "linear-gradient(135deg, #1a0a2e 0%, #1d1235 50%, #160a2a 100%)",
        "accent": "#c4b5fd", "glow": "0 0 20px rgba(167,139,250,0.3)",
        "card_bg": "rgba(167,139,250,0.06)", "border": "rgba(167,139,250,0.2)",
        "name": "厚土", "vibe": "厚德载物，稳如泰山",
    },
}


def get_element_theme(element: str) -> Dict:
    """根据五行元素获取视觉主题."""
    return ELEMENT_THEMES.get(element, ELEMENT_THEMES["土"])


# ══════════════════════════════════════════════════════════════
# 分享内容生成器
# ══════════════════════════════════════════════════════════════

def generate_share_text(destiny_code: Dict, dimensions: Dict, rarity: Dict, element: str) -> Dict:
    """
    生成适合小红书分享的文本内容.
    
    Returns:
        {
            "title": "我的紫微命盘——紫阳·文昌 🎭",
            "body": "...",  # 适合直接复制的分享文案
            "tags": ["#紫微斗数", "#命盘分析", ...],
        }
    """
    theme = ELEMENT_THEMES.get(element, ELEMENT_THEMES["土"])
    
    dim_lines = []
    dim_order = [
        ("destiny", "🔮 天命"),
        ("fortune", "🍀 机遇"),
        ("talent", "🎨 才华"),
        ("heart", "💝 情缘"),
        ("challenge", "⚡ 课题"),
    ]
    
    for key, label in dim_order:
        d = dimensions[key]
        bar = "█" * (d.score // 10) + "░" * (10 - d.score // 10)
        dim_lines.append(f"{label} [{bar}] {d.score}分 · {d.label}")
    
    # 稀有度
    rarity_text = rarity.get("rank_text", "独一无二的你")
    
    body = f"""🔮 我的紫微斗数命盘揭秘！

命格: {destiny_code['full_name']}
元素: {theme['name']} · {theme['vibe']}
{rarity_text}

{' '.join(destiny_code.get('keywords', []))}

{' | '.join(dim_lines[:3])}
{' | '.join(dim_lines[3:])}

#紫微斗数 #命盘解读 #性格测试 #{destiny_code['full_name'].replace('·','')} #{theme['name']}之命"""
    
    return {
        "title": f"我的紫微命盘——{destiny_code.get('full_name', '天命')} {destiny_code.get('emoji', '✨')}",
        "body": body,
        "tags": [
            "#紫微斗数", "#命盘解读", "#性格测试",
            f"#{destiny_code.get('full_name', '').replace('·', '')}",
            f"#{theme.get('name', '')}之命",
        ],
        "dimensions": [
            {"name": "天命", "emoji": "🔮", "score": dimensions["destiny"].score, "label": dimensions["destiny"].label},
            {"name": "机遇", "emoji": "🍀", "score": dimensions["fortune"].score, "label": dimensions["fortune"].label},
            {"name": "才华", "emoji": "🎨", "score": dimensions["talent"].score, "label": dimensions["talent"].label},
            {"name": "情缘", "emoji": "💝", "score": dimensions["heart"].score, "label": dimensions["heart"].label},
            {"name": "课题", "emoji": "⚡", "score": dimensions["challenge"].score, "label": dimensions["challenge"].label},
        ],
    }
