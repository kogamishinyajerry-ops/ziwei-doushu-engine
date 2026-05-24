"""
紫微斗数主引擎 — 排盘总入口

生成完整的紫微斗数命盘, 包含:
- 四柱八字
- 十二宫天干地支
- 五行局
- 所有星曜布局
- 四化
- 大限小限
"""

import json
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional

from ..calendar.ganzhi import calculate_four_pillars, chinese_hour_from_time
from ..calendar.constants import (
    EARTHLY_BRANCHES, HEAVENLY_STEMS,
    PALACE_NAMES, SEXAGENARY_CYCLE,
    ZODIAC, WUXING_JU_NUMBER, SIHUA_NAMES,
)
from ..calendar.solar_terms import get_lunar_month_by_jieqi
from ..calendar.lunar import solar_to_lunar

from .palaces import place_palaces, place_stems_branches, determine_wuxing_ju, PalaceLayout
from .stars import place_all_stars, StarLayout
from .transformations import determine_sihua, get_sihua_stars
from .limits import calculate_daxian, calculate_xiaoxian


# ──────────────────────────────────────
# 完整命盘数据模型
# ──────────────────────────────────────

@dataclass
class PalaceInfo:
    """单个宫位信息."""
    name: str           # 宫名
    branch: str         # 地支
    stem: str           # 天干
    stars: List[str]    # 该宫星曜列表
    sihua: List[str]    # 该宫四化标记
    is_body: bool = False  # 是否身宫
    daxian_range: str = ""  # 大限范围


@dataclass
class ChartData:
    """完整命盘."""
    # 基本信息
    name: str = ""
    gender: str = "男"
    birth_date: str = ""        # 公历生日
    birth_time: str = ""        # 出生时间
    birth_city: str = ""        # 出生城市
    solar_correction: dict = field(default_factory=dict)  # 真太阳时校正信息
    quality_flags: Dict[str, dict] = field(default_factory=dict)  # 回退/质量信号
    
    # 四柱
    year_pillar: str = ""
    month_pillar: str = ""
    day_pillar: str = ""
    hour_pillar: str = ""
    chinese_hour: str = ""
    zodiac: str = ""
    
    # 农历
    lunar_date: str = ""
    lunar_month: int = 0
    lunar_day: int = 0
    
    # 命宫/身宫
    ming_palace: str = ""
    shen_palace: str = ""
    
    # 五行局
    wuxing_ju: int = 0
    wuxing_ju_name: str = ""
    ming_nayin: str = ""
    
    # 十二宫
    palaces: List[PalaceInfo] = field(default_factory=list)
    
    # 四化
    sihua_map: Dict[str, str] = field(default_factory=dict)
    
    # 大限
    daxian: Dict[str, str] = field(default_factory=dict)
    
    # 辅助信息
    stem_yinyang: str = ""
    branch_yinyang: str = ""


def generate_chart(
    year: int, month: int, day: int,
    hour: int, minute: int = 0,
    name: str = "", gender: str = "男",
    city: str = "",
    huoling_variant: str = "mainstream",
) -> ChartData:
    """
    生成完整的紫微斗数命盘.
    
    Args:
        year: 公历年
        month: 公历月
        day: 公历日
        hour: 出生小时 (0-23)
        minute: 出生分钟
        name: 姓名
        gender: 性别 (男/女)
    
    Returns:
        ChartData 完整命盘
    """
    chart = ChartData()
    chart.name = name
    chart.gender = gender
    chart.birth_date = f"{year}-{month:02d}-{day:02d}"
    chart.birth_time = f"{hour:02d}:{minute:02d}"
    chart.birth_city = city
    chart.quality_flags = {
        "solar_time": {"status": "not_requested", "fallback": False},
        "lunar": {"status": "pending", "fallback": False},
    }
    
    # ── 0. 真太阳时校正 ──
    corrected_hour, corrected_minute = hour, minute
    solar_info = {}
    if city:
        try:
            from ..calendar.solar_time import get_chinese_hour_with_correction
            solar_info = get_chinese_hour_with_correction(year, month, day, hour, minute, city)
            corrected_hour = solar_info["corrected_hour"]
            corrected_minute = solar_info["corrected_minute"]
            chart.solar_correction = solar_info
            if solar_info.get("province") == "未知":
                chart.quality_flags["solar_time"] = {
                    "status": "unknown_city",
                    "fallback": True,
                    "city": city,
                    "message": "未匹配城市经纬度，使用钟表时间",
                }
            else:
                chart.quality_flags["solar_time"] = {
                    "status": "corrected" if solar_info.get("hour_changed") else "checked",
                    "fallback": False,
                    "city": city,
                    "hour_changed": bool(solar_info.get("hour_changed")),
                }
        except Exception as e:
            chart.quality_flags["solar_time"] = {
                "status": "failed",
                "fallback": True,
                "city": city,
                "reason": str(e),
            }
    
    # ── 1. 四柱 ──
    pillars = calculate_four_pillars(year, month, day, corrected_hour, corrected_minute)
    chart.year_pillar = pillars["year_ganzhi"]
    chart.month_pillar = pillars["month_ganzhi"]
    chart.day_pillar = pillars["day_ganzhi"]
    chart.hour_pillar = pillars["hour_ganzhi"]
    chart.chinese_hour = pillars["chinese_hour"]
    chart.zodiac = pillars["zodiac"]
    
    year_stem = pillars["year_stem"]
    year_branch = pillars["year_branch"]
    month_stem = pillars["month_stem"]
    month_branch = pillars["month_branch"]
    day_stem = pillars["day_stem"]
    day_branch = pillars["day_branch"]
    hour_stem = pillars["hour_stem"]
    hour_branch = pillars["hour_branch"]
    
    # ── 2. 农历 ──
    try:
        lunar = solar_to_lunar(year, month, day)
        chart.lunar_month = lunar.month
        chart.lunar_day = lunar.day
        chart.lunar_date = str(lunar)
        chart.quality_flags["lunar"] = {"status": "ok", "fallback": False}
    except Exception as e:
        # fallback: 用节气推算月数
        dt = datetime(year, month, day, hour, minute)
        chart.lunar_month = get_lunar_month_by_jieqi(dt)
        chart.lunar_day = day  # 近似
        chart.lunar_date = f"农历{chart.lunar_month}月{chart.lunar_day}日"
        chart.quality_flags["lunar"] = {
            "status": "fallback",
            "fallback": True,
            "reason": str(e),
        }
    
    # ── 3. 排十二宫 ──
    layout = place_palaces(chart.lunar_month, hour_branch)
    layout = place_stems_branches(layout, year_stem)
    layout = determine_wuxing_ju(layout)
    
    chart.ming_palace = f"{layout.ming_stem}{layout.ming_branch}"
    shen_palace_name = next(
        name for name, branch_idx in layout.palaces.items()
        if branch_idx == layout.shen_index
    )
    chart.shen_palace = f"{layout.stems.get(shen_palace_name, '')}{EARTHLY_BRANCHES[layout.shen_index]}"
    chart.wuxing_ju = layout.wuxing_ju
    chart.wuxing_ju_name = layout.wuxing_ju_name
    chart.ming_nayin = layout.ming_nayin
    
    # ── 4. 安星 ──
    stars = place_all_stars(
        wuxing_ju=layout.wuxing_ju,
        lunar_day=chart.lunar_day,
        year_stem=year_stem,
        year_branch=year_branch,
        month_branch=month_branch,
        hour_branch=hour_branch,
        lunar_month=chart.lunar_month,
        huoling_variant=huoling_variant,
    )
    # 记录采用的流派变体, 供前端/explain 显式标注 (默认 mainstream)
    chart.quality_flags["school"] = {
        "huoling": huoling_variant,
        "fallback": False,
    }
    
    # ── 5. 四化 ──
    sihua_raw = determine_sihua(year_stem)
    chart.sihua_map = sihua_raw  # {星名: 四化类型}
    
    # ── 6. 大限 ──
    is_male = (gender in ["男", "male", "Male", "M"])
    daxian_layout = calculate_daxian(
        ming_index=layout.ming_index,
        wuxing_ju=layout.wuxing_ju,
        year_stem=year_stem,
        is_male=is_male,
    )
    
    # ── 7. 构建宫位信息 ──
    palaces_info = []
    for palace_name in PALACE_NAMES:
        branch_idx = layout.palaces[palace_name]
        branch = EARTHLY_BRANCHES[branch_idx]
        stem = layout.stems.get(palace_name, "?")
        
        # 该宫星曜
        stars_here = [s for s, idx in stars.stars.items() if idx == branch_idx]
        
        # 四化标记
        sihua_marks = []
        for star_name in stars_here:
            if star_name in sihua_raw:
                sihua_marks.append(f"{star_name}({sihua_raw[star_name]})")
        
        # 是否身宫
        is_body = (branch_idx == layout.shen_index)
        
        # 大限
        daxian_str = ""
        for dx_key, (start_age, end_age, dx_idx) in daxian_layout.daxian.items():
            if dx_idx == branch_idx:
                daxian_str = f"{start_age}-{end_age}岁"
                break
        
        pi = PalaceInfo(
            name=palace_name,
            branch=branch,
            stem=stem,
            stars=stars_here,
            sihua=sihua_marks,
            is_body=is_body,
            daxian_range=daxian_str,
        )
        palaces_info.append(pi)
    
    chart.palaces = palaces_info
    
    # 大限字符串
    daxian_map = {}
    for palace_name in PALACE_NAMES:
        branch_idx = layout.palaces[palace_name]
        for dx_key, (start_age, end_age, dx_idx) in daxian_layout.daxian.items():
            if dx_idx == branch_idx:
                daxian_map[palace_name] = f"{start_age}-{end_age}"
                break
    chart.daxian = daxian_map
    
    return chart


def chart_to_dict(chart: ChartData, include_analysis: bool = False) -> dict:
    """将命盘转为字典 (用于 JSON 序列化)."""
    result = {
        "name": chart.name,
        "gender": chart.gender,
        "birth_date": chart.birth_date,
        "birth_time": chart.birth_time,
        "four_pillars": {
            "year": chart.year_pillar,
            "month": chart.month_pillar,
            "day": chart.day_pillar,
            "hour": chart.hour_pillar,
        },
        "chinese_hour": chart.chinese_hour,
        "zodiac": chart.zodiac,
        "lunar_date": chart.lunar_date,
        "ming_palace": chart.ming_palace,
        "shen_palace": chart.shen_palace,
        "wuxing_ju": chart.wuxing_ju_name,
        "ming_nayin": chart.ming_nayin,
        "palaces": [
            {
                "name": p.name,
                "stem": p.stem,
                "branch": p.branch,
                "ganzhi": f"{p.stem}{p.branch}",
                "stars": p.stars,
                "sihua": p.sihua,
                "is_body": p.is_body,
                "daxian": p.daxian_range,
            }
            for p in chart.palaces
        ],
        "sihua": {v: k for k, v in chart.sihua_map.items()}
        if chart.sihua_map else {},
        "daxian": chart.daxian,
        "quality_flags": chart.quality_flags,
    }

    # 可验证指纹 (确定性, 可复算校验)
    from .fingerprint import chart_fingerprint
    result["fingerprint"] = chart_fingerprint(chart)

    if include_analysis:
        # 记录各扩展分析子模块的降级情况，便于前端/调用方观测，
        # 而不是像以前那样静默 pass 丢失信号。
        _analysis_degraded: Dict[str, str] = {}
        try:
            # 优先使用深度分析引擎
            from ..analysis.deep_analyzer import (
                analyze_star_interactions, generate_deep_report, generate_enhanced_output
            )
            # 构建星→宫映射
            star_to_branch = {}
            star_to_palace = {}
            palace_stars_map = {}
            for p in chart.palaces:
                palace_stars_map[p.name] = p.stars
                for s in p.stars:
                    star_to_branch[s] = p.branch
                    star_to_palace[s] = p.name
            
            interactions = analyze_star_interactions(
                star_to_branch, star_to_palace, palace_stars_map, chart.sihua_map
            )
            deep_report = generate_deep_report(chart, interactions)
            enhanced = generate_enhanced_output(chart, interactions, deep_report)
            
            # 保留旧版格局数据
            from ..analysis.analyzer import full_analysis
            old = full_analysis(chart)
            enhanced["patterns"] = old.get("patterns", [])
            enhanced["brightness"] = old.get("brightness", {})
            enhanced["overview"] = old.get("overview", "")
            enhanced["palace_interpretations"] = old.get("palace_interpretations", {})
            
            # ── 姓名学分析 ──
            if chart.name:
                try:
                    from ..analysis.name_analysis import analyze_name
                    name_result = analyze_name(chart.name, chart.wuxing_ju_name)
                    if name_result:
                        enhanced["name_analysis"] = name_result
                except Exception as e:
                    _analysis_degraded["name_analysis"] = str(e)
            
            # ── 人格原型 + 稀有度 ──
            try:
                from ..analysis.archetype import compute_archetype, compute_rarity
                enhanced["archetype"] = compute_archetype(chart, palace_stars_map, star_to_branch)
                enhanced["rarity"] = compute_rarity(chart)
            except Exception as e:
                _analysis_degraded["archetype_rarity"] = str(e)
            
            # ── 命格个性系统 (小红书分享核心) ──
            try:
                from ..analysis.personality import (
                    generate_destiny_code, calculate_dimensions,
                    generate_share_text, get_element_theme
                )
                # 找命宫/身宫星曜
                ming_stars_for_code = palace_stars_map.get("命宫", [])
                shen_palace_name = None
                for p in chart.palaces:
                    if p.is_body and p.name != "命宫":
                        shen_palace_name = p.name
                        break
                shen_stars_for_code = palace_stars_map.get(shen_palace_name, []) if shen_palace_name else []
                sihua_stars_list = list(chart.sihua_map.keys())
                ming_branch_for_code = next(
                    (p.branch for p in chart.palaces if p.name == "命宫"), ""
                )

                destiny_code = generate_destiny_code(
                    ming_stars_for_code, shen_stars_for_code,
                    sihua_stars_list, star_to_branch,
                    ming_branch=ming_branch_for_code,
                )
                dimensions = calculate_dimensions(
                    chart, palace_stars_map, star_to_branch,
                    chart.sihua_map, interactions
                )
                element = destiny_code.get("element", "土")
                theme = get_element_theme(element)
                rarity = enhanced.get("rarity", {})
                share = generate_share_text(destiny_code, dimensions, rarity, element)
                
                enhanced["destiny_code"] = destiny_code
                enhanced["dimensions"] = {
                    k: {"name": v.name, "emoji": v.emoji, "score": v.score,
                        "label": v.label, "description": v.description}
                    for k, v in dimensions.items()
                }
                enhanced["element_theme"] = theme
                enhanced["share"] = share
            except Exception as e:
                _analysis_degraded["personality"] = str(e)

            result["analysis"] = enhanced
        except Exception as e:
            _analysis_degraded["core"] = str(e)

        # 暴露分析层降级信号 (纯新增兼容字段, 不改变既有 analysis 内容)
        result["quality_flags"]["analysis_modules"] = {
            "status": "partial" if _analysis_degraded else "full",
            "fallback": bool(_analysis_degraded),
            "degraded": sorted(_analysis_degraded.keys()),
            "errors": _analysis_degraded,
        }

    # 添加真太阳时信息
    if chart.solar_correction:
        result["solar_correction"] = chart.solar_correction
    
    return result


def chart_to_json(chart: ChartData, indent: int = 2) -> str:
    """将命盘导出为 JSON 字符串."""
    return json.dumps(chart_to_dict(chart), ensure_ascii=False, indent=indent)


def print_chart(chart: ChartData) -> str:
    """生成可打印的命盘文本."""
    lines = []
    lines.append("═" * 50)
    lines.append(f"紫微斗数命盘 — {chart.name or '未命名'}")
    lines.append("═" * 50)
    lines.append(f"公历: {chart.birth_date} {chart.birth_time}")
    lines.append(f"农历: {chart.lunar_date}")
    lines.append(f"四柱: {chart.year_pillar} {chart.month_pillar} {chart.day_pillar} {chart.hour_pillar}")
    lines.append(f"时辰: {chart.chinese_hour}时  生肖: {chart.zodiac}")
    lines.append(f"命宫: {chart.ming_palace}  身宫: {chart.shen_palace}")
    lines.append(f"五行局: {chart.wuxing_ju_name} ({chart.ming_nayin})")
    lines.append("")
    
    # 四化
    sihua_desc = ", ".join(f"{star}({stype})" for star, stype in chart.sihua_map.items())
    lines.append(f"四化: {sihua_desc}")
    lines.append("")
    
    # 十二宫
    lines.append("─" * 50)
    for p in chart.palaces:
        stars_str = ", ".join(p.stars) if p.stars else "—"
        sihua_str = " " + ", ".join(p.sihua) if p.sihua else ""
        body_mark = " [身宫]" if p.is_body else ""
        dx_mark = f" 大限:{p.daxian_range}" if p.daxian_range else ""
        lines.append(f"  {p.name}({p.stem}{p.branch}){body_mark}: {stars_str}{sihua_str}{dx_mark}")
    
    lines.append("═" * 50)
    return "\n".join(lines)
