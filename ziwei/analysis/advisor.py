"""
智能命理顾问 — Intelligent Ziwei Advisor

功能:
- 自由问答: 用户提出任何紫微斗数相关问题
- 知识库检索: 内置紫微斗数专业知识
- 命盘上下文注入: 结合具体命盘的星曜/宫位/四化进行个性化分析
- 专业约束: 拒绝过于离谱的问题，只回答有依据的内容
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from ..calendar.constants import (
    EARTHLY_BRANCHES, HEAVENLY_STEMS, PALACE_NAMES,
    ZODIAC, SIHUA_NAMES,
)

# ═══════════════════════════════════════════════════
# 紫微斗数知识库
# ═══════════════════════════════════════════════════

KNOWLEDGE_BASE = {
    # ─── 星曜概述 ───
    "紫微": {
        "element": "土", "yin_yang": "阳", "nature": "帝星",
        "traits": "领导力、权威、自尊心强、贵人运佳",
        "career": "适合管理、政府、创业、领导岗位",
        "relationship": "配偶有地位或能力，婚姻需互相尊重",
        "health": "脾胃、消化系统",
    },
    "天机": {
        "element": "木", "yin_yang": "阴", "nature": "智星",
        "traits": "思维敏捷、好奇心强、善谋划、想法多变",
        "career": "适合策划、咨询、科研、IT等脑力工作",
        "relationship": "配偶聪明灵活，需要精神层面的共鸣",
        "health": "神经系统、肝胆",
    },
    "太阳": {
        "element": "火", "yin_yang": "阳", "nature": "贵星",
        "traits": "热情开朗、乐于助人、胸怀坦荡、有正义感",
        "career": "适合教育、传媒、公益、公共事业",
        "relationship": "配偶性格开朗，需防一方过于强势",
        "health": "心血管、眼睛",
    },
    "武曲": {
        "element": "金", "yin_yang": "阴", "nature": "财星",
        "traits": "刚毅果断、理财能力强、执行力强、性格刚硬",
        "career": "适合金融、技术、工程、管理",
        "relationship": "配偶务实有能力，但需注意感情表达",
        "health": "呼吸系统、骨骼",
    },
    "天同": {
        "element": "水", "yin_yang": "阳", "nature": "福星",
        "traits": "温和知足、善协调、人缘好、缺乏进取心",
        "career": "适合服务、协调、文化、福利行业",
        "relationship": "配偶性格温和，婚姻平稳幸福",
        "health": "肾脏、泌尿系统",
    },
    "廉贞": {
        "element": "火", "yin_yang": "阴", "nature": "次桃花/囚星",
        "traits": "才华横溢、情感丰富、个性鲜明、情绪波动",
        "career": "适合艺术、设计、文职、创意工作",
        "relationship": "感情浓烈多波折，需用心经营",
        "health": "血液、内分泌",
    },
    "天府": {
        "element": "土", "yin_yang": "阳", "nature": "库星",
        "traits": "稳重务实、善经营理财、保守谨慎、衣食无忧",
        "career": "适合管理、金融、地产、贸易",
        "relationship": "配偶稳重可靠，家境殷实",
        "health": "脾胃、肌肉",
    },
    "太阴": {
        "element": "水", "yin_yang": "阴", "nature": "富星/月星",
        "traits": "温柔细腻、审美力强、注重品质、敏感多思",
        "career": "适合艺术、设计、护理、美容",
        "relationship": "配偶温柔体贴，女命婚姻幸福",
        "health": "妇科、情绪、泌尿",
    },
    "贪狼": {
        "element": "水/木", "yin_yang": "阳", "nature": "桃花/欲望星",
        "traits": "多才多艺、善交际、桃花旺、欲望强",
        "career": "适合演艺、公关、贸易、社交行业",
        "relationship": "桃花运旺，配偶多才但需防感情多变",
        "health": "肝胆、肾脏",
    },
    "巨门": {
        "element": "水", "yin_yang": "阴", "nature": "暗星/口舌星",
        "traits": "口才好、善思辨、易招是非、心思缜密",
        "career": "适合法律、教育、传媒、咨询",
        "relationship": "夫妻沟通至关重要，宜坦诚交流",
        "health": "消化系统、口腔",
    },
    "天相": {
        "element": "水", "yin_yang": "阳", "nature": "印星/辅佐星",
        "traits": "正直善良、人缘极好、善服务、缺乏主见",
        "career": "适合行政、管理、公关、法律",
        "relationship": "配偶善良正直，是人生好伴侣",
        "health": "皮肤、排泄系统",
    },
    "天梁": {
        "element": "土", "yin_yang": "阳", "nature": "荫星/寿星",
        "traits": "有长者之风、乐于助人、固执、好为人师",
        "career": "适合教育、医疗、公益、法律",
        "relationship": "配偶稳重有担当，但可能较强势",
        "health": "脾胃、寿命长",
    },
    "七杀": {
        "element": "金/火", "yin_yang": "阳", "nature": "将星",
        "traits": "性格刚烈、敢作敢为、适合开拓、易冲动",
        "career": "适合军警、工程、外科、创业",
        "relationship": "感情充满激情但易争执",
        "health": "意外伤害、外科",
    },
    "破军": {
        "element": "水", "yin_yang": "阴", "nature": "耗星",
        "traits": "个性独立、不喜约束、一生多变、破旧立新",
        "career": "适合创新、科技、创业、改造类工作",
        "relationship": "感情多变，需找能包容变化的对象",
        "health": "生殖系统、突发疾病",
    },

    # ─── 宫位职能 ───
    "宫位": {
        "命宫": "代表命主自身，性格、命运基调、一生格局的关键宫位。",
        "兄弟": "代表兄弟姐妹、同辈关系、合作运势、社交圈。",
        "夫妻": "代表婚姻、配偶特质、感情模式、异性缘。",
        "子女": "代表子女、创造力、享受/娱乐、桃花。",
        "财帛": "代表正财运、赚钱能力、理财风格、物质生活。",
        "疾厄": "代表身体健康、疾病倾向、意外、遗传。",
        "迁移": "代表外出运势、环境变动、对外表现、社会形象。",
        "交友": "代表朋友、下属、社交圈、大众关系。",
        "官禄": "代表事业、工作、职场环境、社会地位。",
        "田宅": "代表房产、家庭、不动产、家居环境。",
        "福德": "代表精神世界、享乐、内心满足感、来世福报。",
        "父母": "代表父母、长辈、上司、学历、文书运。",
    },

    # ─── 四化 ───
    "四化": {
        "化禄": "代表财运、资源、机遇、得到。化禄为福，主顺利通达，财运亨通。",
        "化权": "代表权力、掌控力、执行力。化权为势，主主导和控制。",
        "化科": "代表名声、学业、专业度。化科为名，主声誉和考运。",
        "化忌": "代表阻碍、执着、课题。化忌为困，主波折和需要修炼的人生课题。",
    },

    # ─── 五行局 ───
    "五行局": {
        "水二局": "水性主智，灵活多变，善于适应环境。情绪波动较大，需学会情绪管理。",
        "木三局": "木性主仁，向上生长，有学习能力和进取心。但需耐心，成长需要时间。",
        "金四局": "金性主义，刚毅果断，执行力强。但需磨砺方能成器，苦难是最好的老师。",
        "土五局": "土性主信，稳重务实，厚德载物。为人可靠，但偶尔需放下顾虑大胆尝试。",
        "火六局": "火性主礼，热情奔放，感染力强。但火焰既能照亮前路也能灼伤自己，掌握火候是关键。",
    },

    # ─── 常见问题解答 ───
    "FAQ": {
        "配偶": "看夫妻宫主星。夫妻宫星曜决定了配偶的性格特质和婚姻模式。同时要结合迁移宫（外在表现）和福德宫（内心期待）综合判断。",
        "财运": "看财帛宫、田宅宫、以及化禄/禄存的位置。财帛宫看赚钱能力，田宅宫看资产积累，禄星看财源方向。",
        "事业": "看官禄宫和迁移宫。官禄宫看事业方向和职场环境，迁移宫看外在机遇和社会评价。命宫主星也影响职业选择偏好。",
        "健康": "看疾厄宫。疾厄宫星曜揭示先天体质弱点和疾病倾向。配合命宫和五行局综合判断。",
        "子女": "看子女宫。子女宫星曜影响生育运、子女数量和亲子关系。廉贞、贪狼在子女宫多子，七杀、破军则可能较少。",
        "大限": "大限每十年一换，从命宫开始按特定方向轮转。阳男阴女顺行，阴男阳女逆行。每个大限有对应的宫位和主题。",
        "身宫": "身宫代表后半生的重心和命运走向，约35岁后影响力逐渐增大。身宫所在宫位是人生后半程的舞台。",
        "格局": "格局由星曜的特殊排列组合形成，如'紫府同宫'、'日月并明'、'杀破狼'等。格局决定了命盘的特殊性和层次高低。",
        "化忌": "化忌并非全然是凶。化忌代表'执着'——正如激光之所以能切割，是因为聚焦。化忌是人生最需要修炼的课题，跨过去就是蜕变。",
        "桃花": "桃花星包括贪狼（主桃花）、廉贞（次桃花）、天姚、咸池、沐浴等。桃花星在夫妻宫或命宫，异性缘旺。桃花不是坏事，关键看如何善用。",
        "空宫": "宫位无主星称为'空宫'。空宫不代完全无事，而是该领域较受环境和他人影响。需借对宫星曜为参考。",
        "年龄差": "看夫妻宫辅星和宫位方位。左辅/右弼在夫妻宫常指向配偶偏小。夫妻宫在命宫顺时针方向，配偶偏大；逆时针偏小。天姚指向老少配。太阳指大，太阴指小。",
    },
}


# ═══════════════════════════════════════════════════
# 问题分类与路由
# ═══════════════════════════════════════════════════

QUESTION_CATEGORIES = {
    "spouse": re.compile(r"配偶|丈夫|妻子|老婆|老公|对象|伴侣|婚姻|结婚|感情|桃花|夫妻|嫁|娶|另一半|年龄差|比我大|比我小"),
    "career": re.compile(r"事业|工作|职业|行业|升职|跳槽|创业|老板|上司|适合做什么"),
    "wealth": re.compile(r"财运|赚钱|收入|财富|投资|理财|存款|有钱|发财|穷|经济"),
    "health": re.compile(r"健康|疾病|身体|生病|体质|注意什么病|寿命|活多久"),
    "personality": re.compile(r"性格|个性|特点|脾气|优点|缺点|是什么样的人|为人"),
    "children": re.compile(r"子女|孩子|小孩|生育|怀孕|什么时候有"),
    "family": re.compile(r"父母|爸妈|家庭|原生|出身|背景|兄弟姐妹"),
    "fortune": re.compile(r"运势|运气|流年|今年|明年|什么时候|哪年|时机|大运"),
    "compatibility": re.compile(r"合盘|合婚|配对|配不配|合适吗|在一起|缘分|相配"),
    "knowledge": re.compile(r"什么是|什么意思|怎么看|如何看|怎么解读|请教|解释|科普|介绍"),
    "general": re.compile(r".*"),  # fallback
}


# ═══════════════════════════════════════════════════
# 主分析函数
# ═══════════════════════════════════════════════════

def answer_question(
    question: str,
    chart_dict: dict = None,
) -> dict:
    """
    智能回答紫微斗数相关问题.

    Args:
        question: 用户问题
        chart_dict: 可选，命盘数据（有则进行个性化分析）

    Returns:
        {
            "question": str,
            "answer": str,
            "category": str,
            "confidence": str,
            "needs_chart": bool,
            "used_knowledge": list,
            "chart_references": list,
        }
    """
    result = {
        "question": question,
        "answer": "",
        "category": "general",
        "confidence": "medium",
        "needs_chart": False,
        "used_knowledge": [],
        "chart_references": [],
    }

    # ── 1. 过滤离谱问题 ──
    rejection = _check_question_validity(question)
    if rejection:
        result["answer"] = rejection
        result["confidence"] = "high"
        return result

    # ── 2. 分类 ──
    category = _classify_question(question)
    result["category"] = category

    # ── 3. 检查是否需要命盘 ──
    needs_chart = category in ("spouse", "career", "wealth", "health", "personality",
                                "children", "family", "fortune")
    if needs_chart and not chart_dict:
        result["needs_chart"] = True
        result["answer"] = _format_answer_without_chart(category, question)
        return result

    # ── 4. 构建回答 ──
    if chart_dict:
        answer = _answer_with_chart(question, chart_dict, category)
    else:
        answer = _answer_knowledge_only(question, category)

    result["answer"] = answer
    result["confidence"] = "high" if chart_dict else "medium"
    result["used_knowledge"] = _get_used_knowledge(category, question)

    if chart_dict:
        result["chart_references"] = _get_chart_references(question, chart_dict)

    return result


# ═══════════════════════════════════════════════════
# 问题校验
# ═══════════════════════════════════════════════════

REJECTED_PATTERNS = [
    (re.compile(r"彩票|中奖|号码|选号|双色球|大乐透|六合彩"), "命理分析不适用于博彩预测。紫微斗数看的是人生趋势和性格特质，而非随机事件的数字。" ),
    (re.compile(r"股票代码|明天涨|明天跌|哪只股票|买什么股"), "紫微斗数无法预测具体股票的涨跌。建议通过正规金融分析渠道获取投资建议。" ),
    (re.compile(r"死|去世|什么时候走|能活到|寿命多长"), "生死之事非命理可断。紫微斗数可以看健康趋势和体质弱点，但不会预测具体的寿命。" ),
    (re.compile(r"具体门牌|号码|密码"), "命理分析不会涉及具体数字（号码、密码等）。这些属于随机和客观现实，不在紫微斗数的分析范围内。" ),
]


def _check_question_validity(question: str) -> Optional[str]:
    """检查问题是否合理，不合理返回拒绝原因."""
    for pattern, reason in REJECTED_PATTERNS:
        if pattern.search(question):
            return reason
    return None


def _classify_question(question: str) -> str:
    """分类用户问题."""
    for cat, pattern in QUESTION_CATEGORIES.items():
        if pattern.search(question):
            return cat
    return "general"


# ═══════════════════════════════════════════════════
# 回答生成
# ═══════════════════════════════════════════════════

def _format_answer_without_chart(category: str, question: str) -> str:
    """没有命盘时的回复."""
    tips = {
        "spouse": "配偶和感情分析需要提供出生信息（年月日时）才能排盘分析。如果您提供出生日期、时间、性别和出生城市，我可以为您做详细的婚姻感情解读。",
        "career": "事业和职业分析需要命盘支撑才能给出针对性的建议。请提供出生信息（年月日时性别城市），我帮您详细看。",
        "wealth": "财运分析需要结合具体命盘的财帛宫、田宅宫和四化禄星来解读。请提供出生信息。",
        "health": "健康分析需要疾厄宫的星曜配置才能准确判断。请提供出生信息。",
        "personality": "性格分析需要命宫和福德宫的星曜数据。请提供出生信息，我帮您做详细的性格画像。",
        "children": "子女运分析需要出生信息排盘。请提供您的出生日期和时间。",
        "family": "原生家庭分析需要父母宫等宫位数据。请提供出生信息。",
        "fortune": "运势分析需要命盘的大限和流年数据。请提供出生信息以便详细解读。",
    }
    base = tips.get(category, "如需详细的个性化分析，请提供出生年月日时、性别和城市信息，我为您排盘解读。")
    return f"🔮 {base}\n\n如果您只是想了解紫微斗数的基本知识，可以重新描述您的问题，我会用专业知识为您解答。"


def _answer_with_chart(question: str, chart_dict: dict, category: str) -> str:
    """结合命盘的专业回答."""
    palaces = {p["name"]: p for p in chart_dict.get("palaces", [])}
    analysis = chart_dict.get("analysis", {})
    name = chart_dict.get("name", "命主")

    main_set = {"紫微","天机","太阳","武曲","天同","廉贞",
                "天府","太阴","贪狼","巨门","天相","天梁","七杀","破军"}

    if category == "spouse":
        return _answer_spouse(question, chart_dict, palaces, analysis, name, main_set)
    elif category == "career":
        return _answer_career(question, chart_dict, palaces, analysis, name, main_set)
    elif category == "wealth":
        return _answer_wealth(question, chart_dict, palaces, analysis, name, main_set)
    elif category == "health":
        return _answer_health(question, chart_dict, palaces, analysis, name, main_set)
    elif category == "personality":
        return _answer_personality(question, chart_dict, palaces, analysis, name, main_set)
    elif category == "fortune":
        return _answer_fortune(question, chart_dict, palaces, analysis, name, main_set)
    elif category == "children":
        return _answer_children(question, chart_dict, palaces, analysis, name, main_set)
    elif category == "family":
        return _answer_family(question, chart_dict, palaces, analysis, name, main_set)
    elif category == "compatibility":
        return _answer_compatibility(question, chart_dict, palaces, analysis, name, main_set)
    else:
        return _answer_general(question, chart_dict, palaces, analysis, name, main_set)


def _answer_knowledge_only(question: str, category: str) -> str:
    """纯知识回答（不需要命盘）."""
    # 查找FAQ
    for key, answer in KNOWLEDGE_BASE["FAQ"].items():
        if key in question:
            return f"💡 关于「{key}」：\n\n{answer}"

    # 查找星曜知识
    for star_name, info in KNOWLEDGE_BASE.items():
        if star_name in question and star_name not in ("宫位","四化","五行局","FAQ"):
            return _format_star_knowledge(star_name, info)

    # 宫位
    if "宫位" in KNOWLEDGE_BASE:
        for pname, desc in KNOWLEDGE_BASE["宫位"].items():
            if pname in question:
                return f"💡 关于「{pname}」：\n\n{desc}"

    # 四化
    if "四化" in KNOWLEDGE_BASE:
        for sname, desc in KNOWLEDGE_BASE["四化"].items():
            if sname in question:
                return f"💡 关于「{sname}」：\n\n{desc}"

    # 默认
    return _answer_general_knowledge(question)


# ═══════════════════════════════════════════════════
# 各类别回答函数
# ═══════════════════════════════════════════════════

def _answer_spouse(question, chart_dict, palaces, analysis, name, main_set):
    """配偶/婚姻相关回答."""
    parts = [f"🔮 {name}的婚姻感情分析\n"]

    fuqi = palaces.get("夫妻", {})
    fuqi_stars = fuqi.get("stars", [])
    fuqi_mains = [s for s in fuqi_stars if s in main_set]
    fuqi_aux = [s for s in fuqi_stars if s not in main_set]

    parts.append(f"**夫妻宫**（{fuqi.get('ganzhi', '')}）：{'、'.join(fuqi_stars) if fuqi_stars else '无主星'}")

    # 主星解读
    for star in fuqi_mains:
        info = KNOWLEDGE_BASE.get(star, {})
        if info:
            parts.append(f"- {star}坐夫妻宫：{info.get('relationship', '')}")

    # 辅星影响
    for star in fuqi_aux:
        interpretations = {
            "左辅": "左辅在夫妻宫，配偶在关系中扮演'辅助'角色，常见于配偶比自己小的格局。配偶善解人意，是得力助手。",
            "右弼": "右弼在夫妻宫，配偶温柔体贴，婚姻和谐。配偶在背后默默支持。",
            "文昌": "文昌在夫妻宫，配偶有学识才华，可能有师生恋或办公室恋情倾向。",
            "文曲": "文曲在夫妻宫，配偶有才艺或口才，但需注意感情中的沟通方式。",
            "天魁": "天魁在夫妻宫，配偶有贵人气质，可能是你的'贵人伴侣'。",
            "天钺": "天钺在夫妻宫，配偶有帮扶运，来自较好家庭背景的可能性。",
            "禄存": "禄存在夫妻宫，婚姻有财运加持，配偶能助旺你的财运。",
            "擎羊": "擎羊在夫妻宫，感情中容易有冲突和争执，需学会以柔克刚。",
            "陀罗": "陀罗在夫妻宫，感情进度偏慢，婚姻可能较晚，但一旦结合较为稳定。",
            "火星": "火星在夫妻宫，感情来得快去得也快，激情有余但持久不足。",
            "铃星": "铃星在夫妻宫，感情中有暗藏的矛盾，需要耐心沟通化解。",
            "地劫": "地劫在夫妻宫，感情路上有波折，需防第三者或外部干扰。",
            "地空": "地空在夫妻宫，感情中容易有空虚感，需要精神层面的充实。",
            "天马": "天马在夫妻宫，配偶可能来自外地，或两人聚少离多。",
        }
        if star in interpretations:
            parts.append(f"- {star}：{interpretations[star]}")

    # 夫妻宫四化
    sihua_str = fuqi.get("sihua", [])
    if sihua_str:
        parts.append(f"- 四化：{'、'.join(sihua_str)}")

    # 年龄差
    if "年龄" in question or "大" in question or "小" in question:
        age_analysis = _analyze_age_gap(chart_dict, palaces, main_set)
        parts.append(f"\n**关于配偶年龄差**：\n{age_analysis}")

    # 大限
    daxian = chart_dict.get("daxian", {}).get("夫妻", "")
    if daxian:
        parts.append(f"\n**感情大限**：{daxian}岁，这是婚姻感情的关键时期。")

    # 桃花
    peach_stars = [s for s in fuqi_stars if s in ("贪狼","廉贞","天姚")]
    if peach_stars:
        parts.append("\n⚠️ 夫妻宫见桃花星，异性缘旺。需注意保持感情界限，已有的感情要用心经营。")

    # 来自深度分析的内容
    relationship = analysis.get("relationship", {})
    if relationship.get("summary"):
        parts.append(f"\n**系统解读**：{relationship['summary']}")

    return "\n".join(parts)


def _analyze_age_gap(chart_dict, palaces, main_set) -> str:
    """分析配偶年龄差."""
    fuqi = palaces.get("夫妻", {})
    ming = palaces.get("命宫", {})

    fuqi_branch = fuqi.get("branch", "")
    ming_branch = ming.get("branch", "")
    fuqi_stars = fuqi.get("stars", [])

    reasons = []
    direction = None  # "bigger" or "smaller"

    # 辅星判断
    if "左辅" in fuqi_stars:
        reasons.append("左辅入夫妻宫，辅佐之星，传统上指向配偶偏小")
        direction = "smaller"
    if "右弼" in fuqi_stars:
        reasons.append("右弼入夫妻宫，辅助之星，同龄或略小")
        if direction is None:
            direction = "smaller"
    if "太阳" in fuqi_stars:
        reasons.append("太阳入夫妻宫，阳气旺盛，可能指向配偶偏大或有担当")
        if direction is None:
            direction = "bigger"

    # 方位
    if fuqi_branch and ming_branch:
        try:
            fb = EARTHLY_BRANCHES.index(fuqi_branch)
            mb = EARTHLY_BRANCHES.index(ming_branch)

            # 顺时针
            cw = (mb - fb) % 12
            # 逆时针
            ccw = (fb - mb) % 12

            if cw <= ccw:
                # 夫妻宫在命宫顺时针方向 → 偏大
                if "bigger" not in str(direction):
                    reasons.append(f"夫妻宫在命宫顺时针方向（{ming_branch}→{fuqi_branch}），传统上配偶偏大")
                if direction is None or direction == "bigger" or "太阴" in fuqi_stars:
                    direction = "bigger" if direction is None else direction
            else:
                if direction is None or direction == "smaller":
                    reasons.append(f"夫妻宫在命宫逆时针方向（{ming_branch}→{fuqi_branch}），传统上配偶偏小")
                    direction = "smaller"
        except ValueError:
            pass

    # 太阴入夫妻
    if "太阴" in [s for s in fuqi_stars if s in main_set]:
        reasons.append("太阴入夫妻宫，为至阴之星，指向配偶偏小")

    # 干支
    gan = fuqi.get("stem", "")
    zhi = fuqi.get("branch", "")
    yang_stems = set("甲丙戊庚壬")
    yin_stems = set("乙丁己辛癸")
    yang_branches = set("子寅辰午申戌")
    yin_branches = set("丑卯巳未酉亥")

    if gan in yin_stems and zhi in yin_branches:
        reasons.append(f"夫妻宫{gan}{zhi}干支双阴，阴主幼，指向配偶偏小")

    # 天姚
    if "天姚" in fuqi_stars:
        reasons.append("天姚在夫妻宫，有老少配的可能")

    # 综合判断
    if not reasons:
        return "从当前命盘配置来看，没有明确的年龄差信号。配偶年龄可能与你接近，或差距不大（1-3岁）。"

    if direction == "smaller":
        verdict = "综合以上信号，**配偶比自己小的概率较高**。"
    elif direction == "bigger":
        verdict = "综合以上信号，**配偶比自己大的概率较高**。"
    else:
        verdict = "信号混合，**配偶年龄可能与你接近**，差距不大。"

    return verdict + "\n" + "\n".join(f"- {r}" for r in reasons)


def _answer_career(question, chart_dict, palaces, analysis, name, main_set):
    """事业相关回答."""
    parts = [f"🔮 {name}的事业分析\n"]

    guanlu = palaces.get("官禄", {})
    caibo = palaces.get("财帛", {})
    qianyi = palaces.get("迁移", {})

    guanlu_mains = [s for s in guanlu.get("stars", []) if s in main_set]

    # 官禄宫
    parts.append(f"**官禄宫**（{guanlu.get('ganzhi', '')}）：{'、'.join(guanlu.get('stars', [])) if guanlu.get('stars') else '无主星'}")
    for star in guanlu_mains:
        info = KNOWLEDGE_BASE.get(star, {})
        if info:
            parts.append(f"- {star}：{info.get('career', '')}")

    # 迁移宫
    qianyi_stars = qianyi.get("stars", [])
    if qianyi_stars:
        parts.append(f"\n**迁移宫**：{'、'.join(qianyi_stars)}")
        if "天马" in qianyi_stars:
            parts.append("- 天马在迁移宫，宜外出发展，远行有利事业。")

    # 职业建议
    career_path = analysis.get("career_path", {})
    if career_path.get("industries"):
        parts.append(f"\n**适合领域**：{'、'.join(career_path['industries'])}")
    if career_path.get("work_style"):
        parts.append(f"**工作风格**：{'、'.join(career_path['work_style'])}")

    # 大限
    daxian = chart_dict.get("daxian", {}).get("官禄", "")
    if daxian:
        parts.append(f"\n**事业大限**：{daxian}岁，这是职业发展的黄金时期。")

    return "\n".join(parts)


def _answer_wealth(question, chart_dict, palaces, analysis, name, main_set):
    """财运回答."""
    parts = [f"🔮 {name}的财运分析\n"]

    caibo = palaces.get("财帛", {})
    tianzhai = palaces.get("田宅", {})

    caibo_mains = [s for s in caibo.get("stars", []) if s in main_set]
    parts.append(f"**财帛宫**（{caibo.get('ganzhi', '')}）：{'、'.join(caibo.get('stars', [])) if caibo.get('stars') else '无主星'}")

    for star in caibo_mains:
        info = KNOWLEDGE_BASE.get(star, {})
        if info:
            parts.append(f"- {star}：理财风格偏{info.get('traits', '')[:30]}")

    # 禄存/化禄
    has_lucun = "禄存" in caibo.get("stars", [])
    sihua = chart_dict.get("sihua", {})
    for stype, star in sihua.items():
        if stype == "化禄":
            parts.append(f"- {star}化禄：财源方向与{star}相关的领域")

    if has_lucun:
        parts.append("- 禄存入财帛，有稳定积蓄运，宜建立长期储蓄计划。")

    # 田宅
    tianzhai_stars = tianzhai.get("stars", [])
    if tianzhai_stars:
        parts.append(f"\n**田宅宫**（不动产运）：{'、'.join(tianzhai_stars)}")
        if "禄存" in tianzhai_stars:
            parts.append("- 禄存在田宅，房产运旺，有置业优势。")

    # 四化
    for stype, star in sihua.items():
        if stype == "化忌":
            for p in chart_dict["palaces"]:
                if star in p.get("stars", []) and p["name"] == "财帛":
                    parts.append(f"\n⚠️ {star}化忌入财帛宫，赚钱辛苦，宜守不宜攻，不适合高风险投资。")

    return "\n".join(parts)


def _answer_health(question, chart_dict, palaces, analysis, name, main_set):
    """健康回答."""
    parts = [f"🔮 {name}的健康分析\n"]

    jier = palaces.get("疾厄", {})
    jier_stars = jier.get("stars", [])
    jier_mains = [s for s in jier_stars if s in main_set]

    parts.append(f"**疾厄宫**（{jier.get('ganzhi', '')}）：{'、'.join(jier_stars) if jier_stars else '无主星'}")

    sha_stars = {"擎羊","陀罗","火星","铃星","地劫","地空"}

    health_notes = {
        "七杀": ("注意意外伤害和外科手术，建议定期体检，避免高风险运动。", "warning"),
        "天机": ("神经系统较敏感，注意压力管理和睡眠质量，避免过度用脑。", "info"),
        "巨门": ("注意消化系统和口腔健康，饮食宜清淡规律。", "info"),
        "太阳": ("注意心血管系统和眼睛保健，不宜过度劳累，控制血压。", "info"),
        "太阴": ("注意妇科/泌尿系统（女）和情绪健康，保持心情舒畅。", "info"),
        "武曲": ("注意呼吸系统和骨骼健康，避免过度劳累。", "info"),
        "破军": ("注意生殖系统和突发性疾病，保持良好生活习惯。", "info"),
    }

    for star in jier_mains:
        if star in health_notes:
            note, ntype = health_notes[star]
            prefix = "⚠️ " if ntype == "warning" else "💡 "
            parts.append(f"{prefix}{star}：{note}")

    # 煞星
    sha_in_jier = [s for s in jier_stars if s in sha_stars]
    if sha_in_jier:
        parts.append(f"\n疾厄宫有煞星{'、'.join(sha_in_jier)}，需额外注意身体健康。")

    # 来自分析
    health = analysis.get("health", {})
    if health.get("summary"):
        parts.append(f"\n{health['summary']}")
    if health.get("warning"):
        parts.append(f"⚠️ {health['warning']}")

    return "\n".join(parts)


def _answer_personality(question, chart_dict, palaces, analysis, name, main_set):
    """性格回答."""
    parts = [f"🔮 {name}的性格画像\n"]

    ar = analysis.get("archetype", {})
    personality = analysis.get("personality", {})
    destiny = analysis.get("destiny_code", {})

    if ar.get("archetype_name"):
        parts.append(f"**人格原型**：{ar['archetype_name']}（{ar.get('tagline', '')}）")
        parts.append(f"- 五行: {ar.get('element', '')}")
        if ar.get("strengths"):
            parts.append(f"- 优势: {'、'.join(ar['strengths'])}")
        if ar.get("shadows"):
            parts.append(f"- 需注意: {'、'.join(ar['shadows'])}")

    if destiny.get("keywords"):
        parts.append(f"\n**命格关键词**：{'、'.join(destiny['keywords'])}")

    if personality.get("summary"):
        parts.append(f"\n{personality['summary']}")
    if personality.get("detail"):
        parts.append(f"\n{personality['detail']}")

    # 命宫星曜详解
    ming = palaces.get("命宫", {})
    ming_stars = ming.get("stars", [])
    ming_mains = [s for s in ming_stars if s in main_set]
    for star in ming_mains:
        info = KNOWLEDGE_BASE.get(star, {})
        if info:
            parts.append(f"\n**{star}坐命的核心特质**：{info.get('traits', '')}")

    return "\n".join(parts)


def _answer_fortune(question, chart_dict, palaces, analysis, name, main_set):
    """运势回答."""
    parts = [f"🔮 {name}的运势分析\n"]

    # 大限
    daxian = chart_dict.get("daxian", {})
    parts.append("**大限分布**：")
    for palace, range_str in daxian.items():
        parts.append(f"- {palace}：{range_str}岁")

    # 关键年龄
    key_ages = analysis.get("key_ages", [])
    if key_ages:
        parts.append(f"\n**关键人生节点**：")
        for ka in key_ages[:5]:
            emoji = {"milestone":"🎯","career":"💼","relationship":"💝","health":"🏥",
                     "family":"👨‍👩‍👧","wealth":"💰","property":"🏠","spiritual":"🧘",
                     "social":"🤝"}.get(ka.get("type",""),"📌")
            parts.append(f"- {emoji} {ka['age_range']}：{ka.get('event','')}")

    # 四化影响
    sihua = chart_dict.get("sihua", {})
    if sihua:
        parts.append(f"\n**四化动力**：")
        for stype, star in sihua.items():
            parts.append(f"- {star}{stype}，关注{star}所在宫位的运势起伏")

    # 是否有具体年份
    year_match = re.search(r'(20\d{2}|今年|明年|后年)', question)
    if year_match:
        year_str = year_match.group(1)
        parts.append(f"\n💡 针对{year_str}的流年分析需要使用流年排盘功能（/api/liunian）。当前为大限层面的分析。")

    return "\n".join(parts)


def _answer_children(question, chart_dict, palaces, analysis, name, main_set):
    """子女运回答."""
    parts = [f"🔮 {name}的子女运分析\n"]

    zinv = palaces.get("子女", {})
    zinv_stars = zinv.get("stars", [])
    zinv_mains = [s for s in zinv_stars if s in main_set]

    parts.append(f"**子女宫**（{zinv.get('ganzhi', '')}）：{'、'.join(zinv_stars) if zinv_stars else '无主星'}")

    child_notes = {
        "紫微":"紫微在子女宫，子女有贵气，较有出息，但亲子关系需注意尊卑界限。",
        "天机":"天机在子女宫，子女聪明灵活，可能有一子一女。",
        "贪狼":"贪狼在子女宫，桃花旺，可能子女较多，但需注意亲子沟通。",
        "廉贞":"廉贞在子女宫，子女有才华个性强，亲子关系需要用心经营。",
        "七杀":"七杀在子女宫，子女较少但个性强，独立有主见。",
        "破军":"破军在子女宫，子女育养过程多变动，可能较晚或较少。",
        "天府":"天府在子女宫，子女稳重可靠，晚来有靠。",
    }

    for star in zinv_mains:
        if star in child_notes:
            parts.append(f"- {child_notes[star]}")

    # 子女宫大限
    daxian = chart_dict.get("daxian", {}).get("子女", "")
    if daxian:
        parts.append(f"\n**子女大限**：{daxian}岁")

    return "\n".join(parts)


def _answer_family(question, chart_dict, palaces, analysis, name, main_set):
    """原生家庭回答."""
    parts = [f"🔮 {name}的原生家庭分析\n"]

    fumu = palaces.get("父母", {})
    xiongdi = palaces.get("兄弟", {})

    parts.append(f"**父母宫**（{fumu.get('ganzhi', '')}）：{'、'.join(fumu.get('stars', [])) if fumu.get('stars') else '无主星'}")
    parts.append(f"**兄弟宫**（{xiongdi.get('ganzhi', '')}）：{'、'.join(xiongdi.get('stars', [])) if xiongdi.get('stars') else '无主星'}")

    # 父母宫主星
    fumu_mains = [s for s in fumu.get("stars", []) if s in main_set]
    for star in fumu_mains:
        info = KNOWLEDGE_BASE.get(star, {})
        if info:
            parts.append(f"- 父母宫{star}：与父母的缘分受{star}特质影响")

    # 大限
    daxian = chart_dict.get("daxian", {}).get("父母", "")
    if daxian:
        parts.append(f"\n**父母大限**：{daxian}岁，与长辈关系和学业的关键期。")

    return "\n".join(parts)


def _answer_compatibility(question, chart_dict, palaces, analysis, name, main_set):
    """合盘相关回答（单人查询时提示需要两个盘）."""
    parts = [f"🔮 合盘分析\n"]
    parts.append("合盘需要两个人的出生信息。目前只有一个命盘的数据。")
    parts.append(f"当前命盘为：**{name}**（{chart_dict.get('zodiac', '')}年生）")
    parts.append("\n如需合盘分析，请提供另一个人的出生日期、时间、性别和城市。")
    parts.append("也可以使用合盘API接口 `/api/hepan` 进行专业的双盘合婚分析。")
    return "\n".join(parts)


def _answer_general(question, chart_dict, palaces, analysis, name, main_set):
    """综合回答."""
    parts = [f"🔮 {name}的命盘综合分析\n"]

    overview = analysis.get("overview", "")
    if overview:
        parts.append(f"**命盘概览**：{overview[:300]}")

    # 命宫
    ming = palaces.get("命宫", {})
    ming_stars = ming.get("stars", [])
    if ming_stars:
        parts.append(f"\n**命宫**：{'、'.join(ming_stars)}")
        ming_mains = [s for s in ming_stars if s in main_set]
        for star in ming_mains:
            info = KNOWLEDGE_BASE.get(star, {})
            if info:
                parts.append(f"- {star}({info.get('element', '')}/{info.get('yin_yang', '')}): {info.get('traits', '')[:80]}")

    # 四化概览
    sihua = chart_dict.get("sihua", {})
    if sihua:
        parts.append(f"\n**四化**：{'、'.join(f'{k}:{v}' for k,v in sihua.items())}")

    # 五行局
    wx = chart_dict.get("wuxing_ju", "")
    if wx in KNOWLEDGE_BASE.get("五行局", {}):
        parts.append(f"\n**五行局**：{KNOWLEDGE_BASE['五行局'][wx]}")

    # 亮点与警示
    highlights = analysis.get("highlights", [])
    cautions = analysis.get("cautions", [])
    if highlights:
        parts.append(f"\n**命盘亮点**：")
        for h in highlights[:3]:
            parts.append(f"- {h}")
    if cautions:
        parts.append(f"\n**注意事项**：")
        for c in cautions[:3]:
            parts.append(f"- {c}")

    parts.append("\n💡 如需深入了解某个方面，可以继续提问，如'我适合做什么工作？'或'我的财运如何？'")

    return "\n".join(parts)


def _answer_general_knowledge(question: str) -> str:
    """纯知识回答（无命盘，无明确分类）."""
    # 尝试匹配FAQ
    for key, answer in KNOWLEDGE_BASE["FAQ"].items():
        if any(w in question for w in [key, *key.split()]):
            return f"💡 关于「{key}」：\n\n{answer}"

    # 宫位
    for pname, desc in KNOWLEDGE_BASE.get("宫位", {}).items():
        if pname in question:
            return f"💡 关于「{pname}」：\n\n{desc}"

    # 星曜
    for star_name, info in KNOWLEDGE_BASE.items():
        if star_name in question and star_name not in ("宫位","四化","五行局","FAQ"):
            return _format_star_knowledge(star_name, info)

    # 默认响应
    return f"""🔮 紫微斗数知识简介

紫微斗数是中国传统命理学的重要分支，以出生年月日时排定命盘，通过星曜在十二宫的分布来推断人生各方面运势。

**核心要素**：
- **十四主星**：紫微、天机、太阳、武曲、天同、廉贞、天府、太阴、贪狼、巨门、天相、天梁、七杀、破军
- **十二宫**：命宫、兄弟、夫妻、子女、财帛、疾厄、迁移、交友、官禄、田宅、福德、父母
- **四化**：化禄（财/机遇）、化权（权/执行力）、化科（名/学业）、化忌（阻碍/人生课题）
- **五行局**：水二局、木三局、金四局、土五局、火六局

您对哪个方面感兴趣？我可以为您详细解读。"""


def _format_star_knowledge(star_name: str, info: dict) -> str:
    """格式化星曜知识."""
    return f"""💡 关于「{star_name}」：

- **五行**：{info.get('element', '未知')}
- **阴阳**：{info.get('yin_yang', '未知')}
- **性质**：{info.get('nature', '未知')}
- **性格特质**：{info.get('traits', '未知')}
- **职业倾向**：{info.get('career', '未知')}
- **感情特点**：{info.get('relationship', '未知')}
- **健康关注**：{info.get('health', '未知')}

💡 如需了解{star_name}在您命盘中的具体影响，请提供出生信息排盘后提问。"""


def _get_used_knowledge(category: str, question: str) -> List[str]:
    """返回用到的知识条目."""
    used = []
    for star_name in KNOWLEDGE_BASE:
        if star_name in question and star_name not in ("宫位","四化","五行局","FAQ"):
            used.append(f"星曜:{star_name}")

    for pname in KNOWLEDGE_BASE.get("宫位", {}):
        if pname in question:
            used.append(f"宫位:{pname}")

    for key in KNOWLEDGE_BASE.get("FAQ", {}):
        if key in question:
            used.append(f"FAQ:{key}")

    if category in KNOWLEDGE_BASE.get("FAQ", {}):
        used.append(f"FAQ:{category}")

    return used[:5]


def _get_chart_references(question: str, chart_dict: dict) -> List[dict]:
    """返回引用的命盘要素."""
    refs = []
    for p in chart_dict.get("palaces", []):
        if p["name"] in question:
            refs.append({"type": "palace", "name": p["name"], "data": p})
    return refs[:5]
