"""
LLM Prompt引擎 — Personalized LLM Interpretation Engine

功能:
- 命盘全量数据 → 结构化中文prompt模板
- OpenAI/DeepSeek兼容API调用
- 本地回退生成器 (无需API key)
- 流式输出支持
"""

import os
import json
from typing import Dict, Optional, Callable, Generator

# ══════════════════════════════════════════════════════════════
# Prompt 构建器
# ══════════════════════════════════════════════════════════════

def build_chart_prompt(chart_dict: dict, mode: str = "full") -> str:
    """
    将命盘数据转换为结构化中文提示词.
    
    Args:
        chart_dict: chart_to_dict 的输出
        mode: full / personality / career / relationship / yearly
    
    Returns:
        完整的LLM prompt
    """
    d = chart_dict
    fp = d.get("four_pillars", {})
    analysis = d.get("analysis", {})
    
    # ── 基础信息 ──
    parts = []
    parts.append("# 紫微斗数命盘数据\n")
    parts.append("## 基本信息")
    parts.append(f"- 四柱八字: {fp.get('year','')} {fp.get('month','')} {fp.get('day','')} {fp.get('hour','')}")
    parts.append(f"- 命宫: {d.get('ming_palace','')}  身宫: {d.get('shen_palace','')}")
    parts.append(f"- 五行局: {d.get('wuxing_ju','')}")
    parts.append(f"- 生肖: {d.get('zodiac','')}")
    parts.append(f"- 农历: {d.get('lunar_date','')}")
    
    # ── 四化 ──
    sihua = d.get("sihua", {})
    if sihua:
        parts.append("\n## 生年四化")
        sihua_desc = "、".join(f"{stype}: {star}" for stype, star in sihua.items())
        parts.append(f"{sihua_desc}")
    
    # ── 十二宫 ──
    parts.append("\n## 十二宫星曜分布")
    for p in d.get("palaces", []):
        stars = "、".join(p.get("stars", [])) if p.get("stars") else "无"
        sihua_marks = "、".join(p.get("sihua", [])) if p.get("sihua") else ""
        body_mark = " [身宫]" if p.get("is_body") else ""
        dx = f" 大限:{p.get('daxian','')}" if p.get("daxian") else ""
        line = f"- {p['name']}({p.get('ganzhi','')}){body_mark}: {stars}"
        if sihua_marks:
            line += f" [{sihua_marks}]"
        line += dx
        parts.append(line)
    
    # ── 已有分析 ──
    if analysis:
        # 格局
        patterns = analysis.get("patterns", [])
        if patterns:
            parts.append("\n## 检测到的格局")
            for pat in patterns[:8]:
                quality = "吉" if pat.get("quality") == "吉" else ("凶" if pat.get("quality") == "凶" else "中平")
                parts.append(f"- [{quality}] {pat.get('name','')}: {pat.get('description','')[:80]}")
        
        # 概览
        overview = analysis.get("overview", "")
        if overview:
            parts.append(f"\n## 系统概览\n{overview}")
        
        # 星曜互涉
        interactions = analysis.get("interactions", [])
        if interactions:
            parts.append("\n## 关键星曜互涉")
            for ix in interactions[:6]:
                parts.append(f"- [{ix.get('type','')}] {ix.get('effect','')}")
        
        # 姓名学
        name_data = analysis.get("name_analysis")
        if name_data:
            parts.append(f"\n## 姓名五格")
            parts.append(f"- 姓名分数: {name_data.get('score','')}/100")
            parts.append(f"- 评价: {name_data.get('overall','')}")
            parts.append(f"- 三才: {'→'.join(name_data.get('sancai',{}).get('sancai',[]))}")
        
        # 原型
        archetype = analysis.get("archetype")
        if archetype:
            parts.append(f"\n## 人格原型")
            parts.append(f"- 原型: {archetype.get('archetype_name','')} ({archetype.get('tagline','')})")
            parts.append(f"- 五行: {archetype.get('element','')}")
            parts.append(f"- 优势: {'、'.join(archetype.get('strengths',[]))}")
            parts.append(f"- 阴影: {'、'.join(archetype.get('shadows',[]))}")
        
        # 稀有度
        rarity = analysis.get("rarity")
        if rarity:
            parts.append(f"\n## 稀有度")
            parts.append(f"- 分数: {rarity.get('score','')}/1000 [{rarity.get('tier_label','')}]")
            for b in rarity.get("bonuses", [])[:3]:
                parts.append(f"  - {b.get('desc','')} (+{b.get('points','')})")
    
    # ── 模式指令 ──
    parts.append(f"\n## 解读指令\n")
    
    if mode == "full":
        parts.append("请作为一位资深的紫微斗数命理师，基于以上完整的命盘数据，为命主提供一份全面的命盘解读。")
        parts.append("请包含以下部分:")
        parts.append("1. **性格画像**: 基于命宫星曜和人格原型，分析命主的性格特质、优势和需要注意的阴影面。")
        parts.append("2. **事业财运**: 基于官禄宫、财帛宫星曜和四化，分析事业发展方向和财运特点。")
        parts.append("3. **感情婚姻**: 基于夫妻宫、子女宫星曜，分析感情运势和婚姻建议。")
        parts.append("4. **健康提示**: 基于疾厄宫星曜，给出健康方面的注意事项。")
        parts.append("5. **人生建议**: 结合格局和星曜互涉，给出最重要的3条人生建议。")
        parts.append("\n请用优雅流畅的中文书写，避免使用markdown表格，使用自然段落。控制在800-1200字。")
    elif mode == "personality":
        parts.append("请作为一位资深的紫微斗数命理师，基于以上命盘数据，专注分析命主的性格特质。")
        parts.append("请深入分析: 命宫主星如何塑造性格基调，人格原型如何体现，福德宫如何影响内心世界，以及身宫如何影响后半生。")
        parts.append("控制在400-600字，用自然流畅的中文段落。")
    elif mode == "career":
        parts.append("请作为一位资深的紫微斗数命理师，基于以上命盘数据，专注分析命主的事业和财运。")
        parts.append("请分析: 官禄宫星曜适合什么行业，财帛宫的理财特点，迁移宫对事业的影响，以及四化如何推动事业发展。")
        parts.append("控制在400-600字，用自然流畅的中文段落。")
    elif mode == "relationship":
        parts.append("请作为一位资深的紫微斗数命理师，基于以上命盘数据，专注分析命主的感情和婚姻。")
        parts.append("请分析: 夫妻宫星曜的感情模式，子女宫和父母宫对婚姻观的影响，桃花星的配置，以及感情中需要注意的事项。")
        parts.append("控制在400-600字，用自然流畅的中文段落。")
    elif mode == "yearly":
        parts.append("请作为一位资深的紫微斗数命理师，基于以上命盘数据，分析命主在当前年份的整体运势。")
        parts.append("请分析: 大限所在宫位的影响，流年需要注意的关键事项，以及在不同领域(事业/感情/健康)的机遇和挑战。")
        parts.append("控制在400-600字，用自然流畅的中文段落。")
    
    parts.append("\n注意: 你的解读应基于提供的具体命盘数据，避免泛泛而谈。引用具体星曜和宫位来支撑你的观点。")
    
    return "\n".join(parts)


# ══════════════════════════════════════════════════════════════
# LLM 客户端
# ══════════════════════════════════════════════════════════════

def _get_api_config(api_key: str = None, base_url: str = None, model: str = None, provider: str = None):
    """
    获取API配置，支持自动检测可用提供者.
    
    优先级: 参数指定 > 环境变量指定 > 默认(Minimax > DeepSeek > OpenAI)
    
    Args:
        api_key: 显式API密钥
        base_url: 显式API地址
        model: 显式模型名
        provider: 提供者名称 (minimax/deepseek/openai/auto)
    
    Returns:
        (api_key, base_url, model, provider_name)
    """
    if provider == "auto":
        provider = None

    # 如果显式指定了 provider
    if provider == "minimax":
        key = api_key or os.environ.get("MINIMAX_API_KEY") or ""
        url = base_url or os.environ.get("MINIMAX_BASE_URL") or "https://api.minimax.chat/v1"
        mdl = model or os.environ.get("MINIMAX_MODEL") or "MiniMax-M2.7"
        return key, url, mdl, "minimax"
    elif provider == "deepseek":
        key = api_key or os.environ.get("DEEPSEEK_API_KEY") or ""
        url = base_url or os.environ.get("DEEPSEEK_BASE_URL") or "https://api.deepseek.com/v1"
        mdl = model or os.environ.get("DEEPSEEK_MODEL") or "deepseek-chat"
        return key, url, mdl, "deepseek"
    elif provider == "openai":
        key = api_key or os.environ.get("OPENAI_API_KEY") or ""
        url = base_url or os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1"
        mdl = model or os.environ.get("OPENAI_MODEL") or "gpt-4o"
        return key, url, mdl, "openai"
    
    # 自动检测 (优先级: Minimax > DeepSeek > OpenAI)
    # 1. Minimax
    mm_key = os.environ.get("MINIMAX_API_KEY", "")
    if mm_key and not api_key:
        url = base_url or os.environ.get("MINIMAX_BASE_URL") or "https://api.minimax.chat/v1"
        mdl = model or os.environ.get("MINIMAX_MODEL") or "MiniMax-M2.7"
        return mm_key, url, mdl, "minimax"
    
    # 2. DeepSeek
    ds_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if ds_key and not api_key:
        url = base_url or os.environ.get("DEEPSEEK_BASE_URL") or "https://api.deepseek.com/v1"
        mdl = model or os.environ.get("DEEPSEEK_MODEL") or "deepseek-chat"
        return ds_key, url, mdl, "deepseek"

    # 3. OpenAI
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    if openai_key and not api_key:
        url = base_url or os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1"
        mdl = model or os.environ.get("OPENAI_MODEL") or "gpt-4o"
        return openai_key, url, mdl, "openai"

    # No detected key: keep DeepSeek defaults for local fallback metadata.
    key = api_key or ""
    url = base_url or os.environ.get("DEEPSEEK_BASE_URL") or "https://api.deepseek.com/v1"
    mdl = model or os.environ.get("DEEPSEEK_MODEL") or "deepseek-chat"
    return key, url, mdl, "deepseek"


def call_llm(
    prompt: str,
    api_key: str = None,
    model: str = None,
    base_url: str = None,
    max_tokens: int = 2048,
    temperature: float = 0.8,
    provider: str = None,
) -> dict:
    """
    调用 LLM API (OpenAI兼容接口).
    
    Returns:
        {"content": "...", "model": "...", "usage": {...}}
        或 {"error": "..."}
    """
    key, url, mdl, provider_name = _get_api_config(api_key, base_url, model, provider=provider)
    
    if not key:
        return {"error": "未设置API密钥 (MINIMAX_API_KEY / DEEPSEEK_API_KEY / OPENAI_API_KEY)", "content": ""}
    
    try:
        import requests
    except ImportError:
        return {"error": "未安装 requests 库", "content": ""}
    
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": mdl,
        "messages": [
            {"role": "system", "content": "你是一位资深的紫微斗数命理师，精通星曜解读和命盘分析。你的回复应基于具体命盘数据，专业、详细、有洞察力。使用优雅流畅的中文。"},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    
    try:
        resp = requests.post(
            f"{url.rstrip('/')}/chat/completions",
            headers=headers,
            json=payload,
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        
        return {
            "content": data["choices"][0]["message"]["content"],
            "model": data.get("model", mdl),
            "provider": provider_name,
            "usage": {
                "prompt_tokens": data.get("usage", {}).get("prompt_tokens", 0),
                "completion_tokens": data.get("usage", {}).get("completion_tokens", 0),
            },
        }
    except Exception as e:
        return {"error": str(e), "content": ""}


def call_llm_stream(
    prompt: str,
    callback: Callable[[str], None],
    api_key: str = None,
    model: str = None,
    base_url: str = None,
    max_tokens: int = 2048,
    temperature: float = 0.8,
    provider: str = None,
) -> dict:
    """
    流式调用 LLM API, 每收到一个token调用callback.
    
    Returns:
        {"content": "完整文本", "model": "...", "usage": {...}}
    """
    key, url, mdl, provider_name = _get_api_config(api_key, base_url, model, provider=provider)
    
    if not key:
        return {"error": "未设置API密钥 (MINIMAX_API_KEY / DEEPSEEK_API_KEY)", "content": ""}
    
    try:
        import requests
    except ImportError:
        return {"error": "未安装 requests 库", "content": ""}
    
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": mdl,
        "messages": [
            {"role": "system", "content": "你是一位资深的紫微斗数命理师，精通星曜解读和命盘分析。使用优雅流畅的中文。"},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": True,
    }
    
    try:
        resp = requests.post(
            f"{url.rstrip('/')}/chat/completions",
            headers=headers,
            json=payload,
            timeout=120,
            stream=True,
        )
        resp.raise_for_status()
        
        full_text = ""
        for line in resp.iter_lines():
            if not line:
                continue
            line_str = line.decode("utf-8")
            if line_str.startswith("data: "):
                data_str = line_str[6:]
                if data_str == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                    delta = chunk["choices"][0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        full_text += content
                        callback(content)
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue
        
        return {"content": full_text, "model": mdl, "provider": provider_name, "usage": {}}
    except Exception as e:
        return {"error": str(e), "content": ""}


# ══════════════════════════════════════════════════════════════
# 本地回退生成器 (无需 LLM)
# ══════════════════════════════════════════════════════════════

def generate_local_reading(chart_dict: dict, mode: str = "full") -> str:
    """
    不依赖 LLM 的生成本地化解读.
    
    基于命盘数据生成结构化的个性化文本,
    所有输出均为中文, 500-800字.
    """
    d = chart_dict
    fp = d.get("four_pillars", {})
    analysis = d.get("analysis", {})
    palaces = {p["name"]: p for p in d.get("palaces", [])}
    
    lines = []
    
    # ── 标题 ──
    name_str = d.get("name", "命主")
    lines.append(f"「{name_str or '命主'}」命盘解读")
    lines.append("")
    
    if mode in ("full", "personality"):
        lines.append("## 性格画像")
        
        # 命宫主星
        ming = palaces.get("命宫", {})
        ming_stars = ming.get("stars", [])
        main_set = {"紫微","天机","太阳","武曲","天同","廉贞",
                    "天府","太阴","贪狼","巨门","天相","天梁","七杀","破军"}
        ming_mains = [s for s in ming_stars if s in main_set]
        
        if ming_mains:
            lines.append(f"命宫{'、'.join(ming_mains)}坐守，奠定了命主的性格基调。")
        
        # 原型
        archetype = analysis.get("archetype", {})
        if archetype.get("archetype_name"):
            lines.append(f"人格原型为「{archetype['archetype_name']}」——{archetype.get('tagline','')}。")
            if archetype.get("strengths"):
                lines.append(f"天赋优势在于{'，'.join(archetype['strengths'][:2])}。")
            if archetype.get("shadows"):
                lines.append(f"需注意{'，'.join(archetype['shadows'][:2])}。")
        
        # 身宫
        shen_palace_name = None
        for pname, pdata in palaces.items():
            if pdata.get("is_body") and pname != "命宫":
                shen_palace_name = pname
                shen_stars = pdata.get("stars", [])
                shen_mains = [s for s in shen_stars if s in main_set]
                if shen_mains:
                    lines.append(f"身宫在{shen_palace_name}，{'、'.join(shen_mains)}的能量将在后半生逐渐显现，人生的重心会向此领域转移。")
        
        # 福德宫
        fude = palaces.get("福德", {})
        fude_stars = fude.get("stars", [])
        fude_mains = [s for s in fude_stars if s in main_set]
        if fude_mains:
            lines.append(f"福德宫{'、'.join(fude_mains)}影响内心世界，精神追求和幸福感与此密切相关。")
        
        lines.append("")
    
    if mode in ("full", "career"):
        lines.append("## 事业财运")
        
        guanlu = palaces.get("官禄", {})
        guanlu_stars = guanlu.get("stars", [])
        caibo = palaces.get("财帛", {})
        caibo_stars = caibo.get("stars", [])
        qianyi = palaces.get("迁移", {})
        qianyi_stars = qianyi.get("stars", [])
        
        guanlu_mains = [s for s in guanlu_stars if s in main_set]
        caibo_mains = [s for s in caibo_stars if s in main_set]
        
        if guanlu_mains:
            lines.append(f"官禄宫{'、'.join(guanlu_mains)}，事业发展方向与此星曜特质密切相关。")
            # 个性化建议
            career_tips = {
                "紫微": "适合领导岗位或自主创业，发挥统御才能。",
                "太阳": "适合公共事业、教育、传媒等需要曝光度的工作。",
                "武曲": "适合金融、管理、技术等专业能力驱动的工作。",
                "天相": "适合行政、管理、服务行业，能获得上级赏识。",
                "天机": "适合策划、咨询、研发等需要灵活思维的工作。",
                "巨门": "适合法律、教育、传媒等以口才取胜的工作。",
                "七杀": "适合竞争性强、需要决断力的开拓性工作。",
                "破军": "适合创业、项目制工作，不喜按部就班。",
            }
            for s in guanlu_mains:
                if s in career_tips:
                    lines.append(career_tips[s])
        
        if caibo_mains:
            lines.append(f"财帛宫{'、'.join(caibo_mains)}，理财风格和财富积累方式与之相关。")
        
        if "天马" in qianyi_stars:
            lines.append("天马在迁移宫，远行有利，适合在外地发展事业。")
        
        lines.append("")
    
    if mode in ("full", "relationship"):
        lines.append("## 感情婚姻")
        
        fuqi = palaces.get("夫妻", {})
        fuqi_stars = fuqi.get("stars", [])
        fuqi_mains = [s for s in fuqi_stars if s in main_set]
        
        if fuqi_mains:
            lines.append(f"夫妻宫{'、'.join(fuqi_mains)}，这是婚姻和感情的基本面貌。")
            love_tips = {
                "太阴": "配偶温柔体贴，婚姻和谐美满。",
                "贪狼": "桃花运旺，配偶多才多艺，但需注意感情专一。",
                "巨门": "夫妻沟通至关重要，坦诚交流是幸福的关键。",
                "天同": "配偶性格温和，婚姻平稳幸福。",
                "紫微": "配偶有地位或能力，婚姻需要相互尊重与包容。",
                "太阳": "配偶性格开朗，婚姻光明正大，但需注意双方平衡。",
                "廉贞": "感情浓烈但也多波折，需用心经营。",
                "七杀": "感情中充满激情，但也容易出现争执。",
            }
            for s in fuqi_mains:
                if s in love_tips:
                    lines.append(love_tips[s])
        
        if not fuqi_mains:
            lines.append("夫妻宫无主星，感情模式较受环境影响。需借对宫星曜为参考，建议多观察和了解后再做决定。")
        
        lines.append("")
    
    if mode in ("full",):
        lines.append("## 健康提示")
        jier = palaces.get("疾厄", {})
        jier_stars = jier.get("stars", [])
        jier_mains = [s for s in jier_stars if s in main_set]
        
        sha_in_jier = [s for s in jier_stars if s in ["擎羊","陀罗","火星","铃星","地劫","地空"]]
        
        health_notes = {
            "七杀": "注意意外伤害和外科手术，建议定期体检。",
            "天机": "神经系统较敏感，注意压力管理和睡眠。",
            "巨门": "注意消化系统和口腔健康，饮食宜清淡。",
            "太阳": "注意心血管和眼睛保健，不宜过度劳累。",
            "太阴": "关注情绪健康，保持心情舒畅。",
        }
        
        if jier_mains:
            for s in jier_mains:
                if s in health_notes:
                    lines.append(health_notes[s])
        
        if sha_in_jier:
            lines.append(f"疾厄宫有煞星{'、'.join(sha_in_jier)}，需注意{'意外伤害' if any(s in sha_in_jier for s in ['擎羊','火星']) else '慢性疾病'}。")
        
        if not jier_mains and not sha_in_jier:
            lines.append("疾厄宫平稳，保持健康的生活习惯即可。")
        
        lines.append("")
    
    if mode in ("full", "yearly"):
        lines.append("## 人生建议")
        
        overview = analysis.get("overview", "")
        if overview:
            # 从概览中提取关键句
            lines.append(overview[:200])
        else:
            # 基于命盘生成
            wuxing_ju = d.get("wuxing_ju", "")
            lines.append(f"命主五行局为{wuxing_ju}，这决定了人生的基本节奏和运势特点。")
        
        # 格局提示
        patterns = analysis.get("patterns", [])
        good_patterns = [p for p in patterns if p.get("quality") == "吉"]
        if good_patterns:
            lines.append(f"命中{len(good_patterns)}个吉利格局加持，在{'、'.join(p['name'] for p in good_patterns[:2])}等方面有天然优势。")
        
        # 大限提示
        daxian = d.get("daxian", {})
        if daxian:
            current_relevant = []
            for palace, range_str in daxian.items():
                if "-" in range_str:
                    start = range_str.split("-")[0]
                    try:
                        if 20 <= int(start) <= 40:
                            current_relevant.append(f"{palace}({range_str}岁)")
                    except ValueError:
                        pass
            if current_relevant:
                lines.append(f"青年至中年阶段的关键大限在{'、'.join(current_relevant[:2])}，这是人生发展的重要时期。")
        
        # 稀有度
        rarity = analysis.get("rarity", {})
        if rarity:
            lines.append(f"此命盘稀有度为{rarity.get('tier_label','')}({rarity.get('score','')}分)，{rarity.get('tier','')}级别。")
        
        lines.append("")
        lines.append("以上解读基于紫微斗数命盘数据生成，仅供参考。命由天定，运由己造。")
    
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════
# API 便捷函数
# ══════════════════════════════════════════════════════════════

def enhance_chart_with_llm(
    chart_dict: dict,
    api_key: str = None,
    mode: str = "full",
    provider: str = None,
) -> dict:
    """
    调用 LLM 增强命盘解读.
    
    Args:
        chart_dict: chart_to_dict 的输出
        api_key: API密钥 (可选, 默认从环境变量自动检测)
        mode: full / personality / career / relationship / yearly
        provider: 提供者 (minimax/deepseek/openai/auto), 默认 auto
    
    Returns:
        包含 llm_reading 的 dict, 如果失败则包含 local_reading
    """
    key, _, _, provider_name = _get_api_config(api_key, provider=provider)
    
    if key:
        prompt = build_chart_prompt(chart_dict, mode)
        result = call_llm(prompt, api_key=api_key, provider=provider_name)
        if result.get("content"):
            return {
                "llm_reading": result["content"],
                "llm_model": result.get("model", ""),
                "llm_provider": provider_name,
                "llm_usage": result.get("usage", {}),
            }
    
    # 回退到本地生成
    local = generate_local_reading(chart_dict, mode)
    return {"local_reading": local, "note": "未配置LLM API密钥, 使用本地生成"}


def enhance_chart_local(chart_dict: dict, mode: str = "full") -> dict:
    """使用本地引擎生成解读."""
    local = generate_local_reading(chart_dict, mode)
    return {"local_reading": local}
