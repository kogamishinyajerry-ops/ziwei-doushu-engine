"""
专属命盘深度报告 (Personal chart signature & report)。

差异化核心: 不是"谁读都觉得对"的巴纳姆套话, 而是把**这张盘独有的结构特征**
拎出来具体讲——命主星组合、最强/最弱宫、化忌落宫(最大隐性成本)、化禄(天赋红利)、
优势引擎、能量漏洞、大限红利窗口、稀缺度——让用户读到"这说的就是我"。

两层 (复用 advisor 的"确定性骨架 + LLM 润色 + 离线回退"模式):
1. extract_signature(): 规则引擎确定性抽取专属特征 (可测, 离线)。
2. generate_personal_report(): 犀利专业直言型 LLM 长文; 无 key 回退本地犀利拼装。
"""

from typing import Dict, List, Optional

MAIN_STARS = {
    "紫微", "天机", "太阳", "武曲", "天同", "廉贞", "天府",
    "太阴", "贪狼", "巨门", "天相", "天梁", "七杀", "破军",
}


def _pg(name: str) -> str:
    """宫名加'宫'后缀, 避免'命宫宫'这类重复 (仅命宫自带'宫'字)。"""
    name = name or "?"
    return name if name.endswith("宫") else name + "宫"
LUCKY_STARS = {"左辅", "右弼", "文昌", "文曲", "天魁", "天钺", "禄存", "天马"}
SHA_STARS = {"擎羊", "陀罗", "火星", "铃星", "地空", "地劫"}


# ═══════════════════════════════════════════════════
# 1. 专属特征提取 (确定性)
# ═══════════════════════════════════════════════════

def _star_palace_map(palaces: List[dict]) -> Dict[str, str]:
    return {s: p["name"] for p in palaces for s in p.get("stars", [])}


def _palace_score(p: dict, brightness: dict) -> float:
    """宫位强弱打分: 吉星/庙旺加分, 煞星/陷/化忌减分 (确定性)。"""
    score = 0.0
    pname = p.get("name", "")
    pb = brightness.get(pname, {})
    for s in p.get("stars", []):
        if s in LUCKY_STARS:
            score += 1
        if s in SHA_STARS:
            score -= 1
        if s in MAIN_STARS:
            lv = (pb.get(s) or {}).get("level")
            if isinstance(lv, int):
                if lv >= 6:
                    score += 1      # 庙/旺
                elif lv <= 1:
                    score -= 1      # 陷
    for mark in p.get("sihua", []):
        if "化忌" in mark:
            score -= 2
        elif "化禄" in mark:
            score += 1.5
        elif "化权" in mark or "化科" in mark:
            score += 1
    return score


def _palace_of(star: str, star_palace: Dict[str, str]) -> str:
    return star_palace.get(star, "")


def _daxian_of(palaces: List[dict], palace_name: str) -> str:
    for p in palaces:
        if p.get("name") == palace_name:
            return p.get("daxian", "")
    return ""


def extract_signature(chart_dict: dict) -> dict:
    """
    抽取使这张盘独特的结构化特征 (犀利直言的骨架)。

    Returns dict: ming_stars / ming_combo / strongest_palace / weakest_palace /
    ji(化忌落宫=隐性成本) / lu(化禄=天赋红利) / engine(优势引擎) / leak(能量漏洞) /
    peak_daxian / rarity / patterns / anchors(开篇 top3 专属锚点)。
    """
    d = chart_dict or {}
    palaces = d.get("palaces", [])
    analysis = d.get("analysis", {}) or {}
    brightness = analysis.get("brightness", {}) or {}
    sihua = d.get("sihua", {}) or {}
    star_palace = _star_palace_map(palaces)

    # 命宫主星组合
    ming = next((p for p in palaces if p.get("name") == "命宫"), {})
    ming_mains = [s for s in ming.get("stars", []) if s in MAIN_STARS]
    destiny = analysis.get("destiny_code", {}) or {}
    archetype = analysis.get("archetype", {}) or {}
    ming_combo = destiny.get("full_name") or "、".join(ming_mains) or (
        archetype.get("archetype_name") or "空宫借对宫"
    )

    # 最强 / 最弱宫
    scored = [(p.get("name", ""), _palace_score(p, brightness), p) for p in palaces]
    scored_sorted = sorted(scored, key=lambda x: x[1])
    weakest = scored_sorted[0] if scored_sorted else ("", 0, {})
    strongest = scored_sorted[-1] if scored_sorted else ("", 0, {})

    def _palace_brief(entry):
        name, sc, p = entry
        mains = [s for s in p.get("stars", []) if s in MAIN_STARS]
        lucky = [s for s in p.get("stars", []) if s in LUCKY_STARS]
        sha = [s for s in p.get("stars", []) if s in SHA_STARS]
        return {
            "palace": name, "score": round(sc, 1),
            "main_stars": mains, "lucky": lucky, "sha": sha,
            "daxian": p.get("daxian", ""),
        }

    # 四化落点
    ji_star = sihua.get("化忌", "")
    lu_star = sihua.get("化禄", "")
    quan_star = sihua.get("化权", "")
    ji_palace = _palace_of(ji_star, star_palace)
    lu_palace = _palace_of(lu_star, star_palace)
    quan_palace = _palace_of(quan_star, star_palace)

    ji = {"star": ji_star, "palace": ji_palace} if ji_star else {}
    lu = {"star": lu_star, "palace": lu_palace} if lu_star else {}

    # 优势引擎 / 能量漏洞
    engine = []
    if lu_star:
        engine.append(f"{lu_star}化禄落{_pg(lu_palace)}(天赋红利)")
    if quan_star:
        engine.append(f"{quan_star}化权落{_pg(quan_palace)}(掌控力)")
    leak = []
    if ji_star:
        leak.append(f"{ji_star}化忌落{_pg(ji_palace)}(最大隐性成本)")
    weak_sha = _palace_brief(weakest).get("sha", [])
    if weak_sha:
        leak.append(f"{_pg(weakest[0])}煞星{'、'.join(weak_sha)}聚集")

    # 大限红利窗口 = 化禄落宫的大限 (能量集中期)
    peak_daxian = {
        "palace": lu_palace or strongest[0],
        "range": _daxian_of(palaces, lu_palace) or _daxian_of(palaces, strongest[0]),
    }

    # 稀缺度
    rarity = analysis.get("rarity", {}) or {}
    bonuses = rarity.get("bonuses", []) or []
    top_bonus = max(bonuses, key=lambda b: b.get("points", 0), default=None)

    patterns = analysis.get("patterns", []) or []
    good_patterns = [p for p in patterns if p.get("quality") == "吉"]
    bad_patterns = [p for p in patterns if p.get("quality") == "凶"]

    # ── 开篇 top3 专属锚点 (优先级挑选, 越独特越靠前) ──
    anchors = []
    # 注意: 不把"生年四化俱全"当锚点 — 几乎每张盘都四化俱全(年干定四化, 主星必落盘),
    # 它没有区分度, 当"专属锚点"既千篇一律又违背诚实/专属定位。锚点只取真正区分盘的特征。

    # a) 化忌落宫 = 隐性成本 (犀利抓手, 12 宫各异 → 高区分度)
    if ji_star and ji_palace:
        anchors.append({
            "tag": "成本",
            "title": f"你最大的隐性成本在{_pg(ji_palace)}",
            "detail": f"{ji_star}化忌坐{ji_palace}, 这是你这辈子最容易'用力过猛却反噬自己'的地方, "
                      "不是命不好, 是这股能量需要被你看见并驯服。",
        })
    # b) 命主星组合 (不同盘命主主星不同 → 高区分度)
    if ming_mains:
        anchors.append({
            "tag": "命主",
            "title": f"你是{ming_combo}坐命",
            "detail": (destiny.get("tagline", "") or (archetype.get("tagline", "")) or
                       f"命宫主星{'、'.join(ming_mains)}, 奠定你的性格基调与人生主线。"),
        })
    # c) 最强格局 (成局与否、何种格局各异)
    if good_patterns:
        gp = good_patterns[0]
        anchors.append({
            "tag": "格局",
            "title": f"你成局了:{gp.get('name', '')}",
            "detail": gp.get("description", "")[:60],
        })
    # d) 罕见星曜组合 (排除 sihua 类的真正稀有组合)
    combo_bonus = max(
        (b for b in bonuses if b.get("type") != "sihua"),
        key=lambda b: b.get("points", 0), default=None,
    )
    if combo_bonus and len(anchors) < 3:
        anchors.append({
            "tag": "稀有",
            "title": f"你有罕见组合:{combo_bonus.get('desc', '')}",
            "detail": f"稀缺度 {rarity.get('tier_label', '')}({rarity.get('score', '')}分), "
                      "这类配置在多数盘里见不到。",
        })
    # e) 最强宫兜底
    if strongest[0] and len(anchors) < 3:
        sb = _palace_brief(strongest)
        anchors.append({
            "tag": "强项",
            "title": f"你的盘面最强宫是{strongest[0]}",
            "detail": f"{('、'.join(sb['main_stars'] + sb['lucky'])) or '吉星会照'}集中于此, 是你最该押注的领域。",
        })
    anchors = anchors[:3]

    return {
        "ming_stars": ming_mains,
        "ming_combo": ming_combo,
        "ming_palace": d.get("ming_palace", ""),
        "shen_palace": d.get("shen_palace", ""),
        "wuxing_ju": d.get("wuxing_ju", ""),
        "strongest_palace": _palace_brief(strongest),
        "weakest_palace": _palace_brief(weakest),
        "ji": ji,
        "lu": lu,
        "engine": engine,
        "leak": leak,
        "peak_daxian": peak_daxian,
        "rarity": {
            "score": rarity.get("score"),
            "tier_label": rarity.get("tier_label"),
            "tier_emoji": rarity.get("tier_emoji"),
            "top_bonus": (top_bonus or {}).get("desc"),
        },
        "good_patterns": [p.get("name") for p in good_patterns],
        "bad_patterns": [p.get("name") for p in bad_patterns],
        "anchors": anchors,
        "dimensions": {
            k: {"score": v.get("score"), "label": v.get("label")}
            for k, v in (analysis.get("dimensions", {}) or {}).items()
        },
    }


# ═══════════════════════════════════════════════════
# 2. 本地犀利报告 (无 LLM 时的离线回退)
# ═══════════════════════════════════════════════════

def _local_report(sig: dict, name: str = "") -> str:
    who = name or "你"
    L = []
    L.append(f"## {who}的专属命盘解读")
    L.append("（犀利直言版 · 基于你这张盘的独有结构，不是通用套话）\n")

    L.append("### 先说三件你这张盘最该知道的事")
    for i, a in enumerate(sig.get("anchors", []), 1):
        L.append(f"{i}. **{a['title']}** — {a['detail']}")
    if not sig.get("anchors"):
        L.append("- 这张盘结构相对均衡，没有极端突出的单点。")
    L.append("")

    # 优势引擎
    L.append("### 你的优势引擎")
    eng = sig.get("engine", [])
    if eng:
        L.append("、".join(eng) + "。")
        sp = sig.get("strongest_palace", {})
        if sp.get("palace"):
            extra = "、".join(sp.get("main_stars", []) + sp.get("lucky", []))
            L.append(f"最强宫在 **{sp['palace']}**（{extra or '吉星会照'}），这是你最该押注、回报最高的领域。别分散火力。")
    else:
        L.append("四化未形成明显引擎，优势更多靠后天选择堆叠。")
    L.append("")

    # 隐性成本 (犀利)
    L.append("### 你的隐性成本（直说，别回避）")
    ji = sig.get("ji", {})
    if ji.get("star"):
        L.append(
            f"{ji['star']}化忌坐 **{_pg(ji.get('palace', '?'))}**——这是你最容易内耗、最容易'明明很努力却反被自己拖住'的地方。"
            f"它不是诅咒，是一股需要你正面驯服的能量：越逃避越放大，越看清越能转成专注力。"
        )
    wp = sig.get("weakest_palace", {})
    if wp.get("sha"):
        L.append(f"另外 **{_pg(wp['palace'])}** 煞星（{'、'.join(wp['sha'])}）聚集，这块少冒进、做好预案。")
    L.append("")

    # 红利窗口
    pk = sig.get("peak_daxian", {})
    if pk.get("range"):
        L.append("### 你的红利窗口")
        L.append(f"能量最集中的大限在 **{pk.get('palace', '')}**（{pk['range']}），这十年是主动出击的窗口，别等。")
        L.append("")

    # 稀缺度收尾
    r = sig.get("rarity", {})
    if r.get("tier_label"):
        L.append(f"### 一句话定位")
        L.append(f"你这张盘 {r.get('tier_emoji', '')} **{r['tier_label']}**"
                 f"（{r.get('score', '?')}分）。{r.get('top_bonus') or ''}。"
                 "稀缺不等于躺赢——它只是把起点抬高，剩下的看你怎么打。")
    L.append("")
    L.append("> 命理是参考视角不是确定性预测；健康/婚否/财务/法律等重大决定，请结合现实与专业意见，别只凭一张盘。")
    return "\n".join(L)


# ═══════════════════════════════════════════════════
# 3. 犀利专业直言型 LLM 报告 (复用回退模式)
# ═══════════════════════════════════════════════════

SIGNATURE_REPORT_SYSTEM = (
    "你是一位犀利、专业、直言不讳的紫微斗数命理师。你要写的不是讨好客户的套话，"
    "而是一份让用户'被戳中'的专属深度解读。请严格遵守：\n"
    "1. 只能基于给定的【命盘事实】与【专属特征】作答，绝不编造盘面上不存在的星曜/宫位/四化。\n"
    "2. 犀利=具体且直接：点破隐性成本、瓶颈、能量漏洞，引用具体的星、宫、四化、大限，"
    "让用户清楚'这说的就是我'。但犀利不等于武断算命。\n"
    "3. 命理是参考视角而非确定性预测：用倾向、概率、课题的措辞，避免'一定/必然/注定'。\n"
    "4. 健康、生死、婚否、财务、法律等高风险话题，绝不下确定性结论，提示结合现实与专业意见。\n"
    "5. 第二人称'你'，简体中文，结构清晰(开篇三大专属特征 → 优势引擎 → 隐性成本 → 红利窗口 → 一句定位)，"
    "600-900 字，有锋芒也有建设性，结尾给方向不给宿命。"
)


def _default_report_llm_caller(provider=None, api_key=None):
    def _call(system: str, user: str) -> dict:
        from .llm_prompt import call_llm
        return call_llm(user, system=system, provider=provider, api_key=api_key,
                        temperature=0.7, max_tokens=1500)
    return _call


def _facts_block(chart_dict: dict) -> str:
    from .advisor import _chart_facts_for_advisor
    return _chart_facts_for_advisor(chart_dict)


def _signature_block(sig: dict) -> str:
    lines = [
        f"命主组合: {sig.get('ming_combo', '')} (命宫{sig.get('ming_palace', '')})",
        f"最强宫: {sig.get('strongest_palace', {}).get('palace', '')} "
        f"(主星 {'、'.join(sig.get('strongest_palace', {}).get('main_stars', [])) or '无'})",
        f"最弱宫: {sig.get('weakest_palace', {}).get('palace', '')} "
        f"(煞星 {'、'.join(sig.get('weakest_palace', {}).get('sha', [])) or '无'})",
        f"优势引擎: {'; '.join(sig.get('engine', [])) or '无明显四化引擎'}",
        f"能量漏洞: {'; '.join(sig.get('leak', [])) or '无突出漏洞'}",
        f"红利大限: {sig.get('peak_daxian', {}).get('palace', '')} "
        f"{sig.get('peak_daxian', {}).get('range', '')}",
        f"稀缺度: {sig.get('rarity', {}).get('tier_label', '')} "
        f"{sig.get('rarity', {}).get('score', '')}分; {sig.get('rarity', {}).get('top_bonus', '') or ''}",
        f"吉格: {'、'.join(sig.get('good_patterns', [])) or '无'}",
    ]
    lines.append("开篇必须点出的三大专属锚点:")
    for a in sig.get("anchors", []):
        lines.append(f"  - [{a.get('tag', '')}] {a.get('title', '')}: {a.get('detail', '')}")
    return "\n".join(lines)


def generate_personal_report(
    chart_dict: dict,
    *,
    use_llm: bool = True,
    provider: str = None,
    api_key: str = None,
    llm_caller=None,
) -> dict:
    """
    生成专属命盘深度报告 (犀利专业直言型)。

    确定性 signature 骨架 + 犀利 LLM 长文; 无 key/失败/use_llm=False → 本地犀利拼装。

    Returns: {signature, report, report_source: "llm"/"local", llm: {...}, honesty: {...}}
    """
    sig = extract_signature(chart_dict)
    name = (chart_dict or {}).get("name", "")
    local = _local_report(sig, name)
    honesty = {
        "grounding": "chart_signature",
        "basis": "基于本盘独有结构特征(命主组合/最强弱宫/四化落点/大限/稀缺度)逐项推导, 可在「为什么」层核验。",
        "limits": "命理是参考视角而非确定性预测; 重大决定请结合现实与专业意见综合判断。",
    }
    result = {
        "signature": sig,
        "report": local,
        "local_report": local,
        "report_source": "local",
        "llm": {"used": False, "reason": "local_only"},
        "honesty": honesty,
    }

    if not use_llm:
        result["llm"] = {"used": False, "reason": "disabled"}
        return result

    caller = llm_caller or _default_report_llm_caller(provider=provider, api_key=api_key)
    user = (
        "请为这张命盘写一份犀利专业直言型的【专属深度解读】。\n\n"
        f"## 命盘事实（唯一可用依据，不得编造未列出的星曜/宫位/四化）\n{_facts_block(chart_dict)}\n\n"
        f"## 已抽取的专属特征（你的解读必须围绕这些独有结构展开）\n{_signature_block(sig)}\n\n"
        "要求: 开篇先点出三大专属锚点让用户立刻'对号入座', 然后优势引擎、隐性成本(犀利直说)、"
        "红利窗口、一句定位。引用具体星/宫/四化/大限。结尾给方向不给宿命。"
    )
    try:
        out = caller(SIGNATURE_REPORT_SYSTEM, user) or {}
    except Exception as e:  # noqa: BLE001 - 任何 LLM 故障回退本地
        result["llm"] = {"used": False, "reason": f"llm_error: {e}"}
        return result

    content = (out.get("content") or "").strip()
    if not content:
        result["llm"] = {"used": False, "reason": out.get("error") or "empty_response"}
        return result

    result["report"] = content
    result["report_source"] = "llm"
    result["llm"] = {
        "used": True,
        "provider": out.get("provider"),
        "model": out.get("model"),
        "system_honesty": True,
        "tone": "incisive_professional",
    }
    return result
