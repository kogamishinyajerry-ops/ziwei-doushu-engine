"""
紫微斗数分析解读模块 — Analysis & Interpretation

包含:
- analyzer: 星曜亮度、格局识别、宫位解读
- deep_analyzer: 深度分析引擎 (星曜互涉、四化飞星、多层次解读)
- liunian: 流年运势分析 (流年命宫、流年四化、年度解读)
- archetype: 人格原型 + 稀有度系统
- personality: 命格个性系统 (命码/五维雷达/分享文本)
- name_analysis: 姓名学五格数理
- llm_prompt: LLM增强解读引擎
"""

from .analyzer import (
    get_star_brightness,
    detect_patterns,
    analyze_triad_palaces,
    interpret_palace,
    full_analysis,
    Pattern,
)

from .deep_analyzer import (
    analyze_star_interactions,
    generate_deep_report,
    generate_enhanced_output,
    InteractionResult,
    DeepReport,
)

from .liunian import (
    calculate_liunian_info,
    analyze_liunian,
    analyze_multi_years,
    liunian_to_dict,
    year_ganzhi,
    LiunianInfo,
    LiunianAnalysis,
)

from .archetype import (
    compute_archetype,
    compute_rarity,
    Archetype,
)

from .personality import (
    generate_destiny_code,
    calculate_dimensions,
    generate_share_text,
    get_element_theme,
    Dimension,
)

from .name_analysis import (
    analyze_name,
    calculate_five_grid,
    full_name_analysis,
)

from .llm_prompt import (
    build_chart_prompt,
    call_llm,
    enhance_chart_with_llm,
    enhance_chart_local,
    generate_local_reading,
)

__all__ = [
    # Analyzer
    "get_star_brightness", "detect_patterns", "analyze_triad_palaces",
    "interpret_palace", "full_analysis", "Pattern",
    # Deep Analyzer
    "analyze_star_interactions", "generate_deep_report",
    "generate_enhanced_output", "InteractionResult", "DeepReport",
    # Liunian
    "calculate_liunian_info", "analyze_liunian", "analyze_multi_years",
    "liunian_to_dict", "year_ganzhi", "LiunianInfo", "LiunianAnalysis",
    # Archetype
    "compute_archetype", "compute_rarity", "Archetype",
    # Personality
    "generate_destiny_code", "calculate_dimensions",
    "generate_share_text", "get_element_theme", "Dimension",
    # Name Analysis
    "analyze_name", "calculate_five_grid", "full_name_analysis",
    # LLM Prompt
    "build_chart_prompt", "call_llm", "enhance_chart_with_llm",
    "enhance_chart_local", "generate_local_reading",
]
