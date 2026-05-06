"""
四化模块 — Four Transformations (化禄、化权、化科、化忌)

根据生年天干确定四化星曜.
"""

from typing import Dict, List, Tuple
from ..calendar.constants import GAN_SIHUA_TABLE, SIHUA_NAMES


def determine_sihua(year_stem: str) -> Dict[str, str]:
    """
    确定四化.
    
    根据生年天干查表, 返回{星名: 四化类型}.
    
    Args:
        year_stem: 年干 (甲/乙/丙/...)
    
    Returns:
        {星名: 四化} 例如 {"廉贞": "化禄", "破军": "化权", ...}
    """
    if year_stem not in GAN_SIHUA_TABLE:
        raise ValueError(f"无效的天干: {year_stem}")
    
    return dict(GAN_SIHUA_TABLE[year_stem])


def apply_sihua(star_layout, year_stem: str) -> Dict[str, str]:
    """
    将四化应用到星曜布局中.
    
    返回标记了四化的星曜列表: {星名: 四化类型}
    
    Args:
        star_layout: StarLayout (含有所有星曜位置)
        year_stem: 年干
    
    Returns:
        {星名: 四化} 已确定的四化星
    """
    sihua_map = determine_sihua(year_stem)
    
    result = {}
    for star_name, sihua_type in sihua_map.items():
        if star_name in star_layout.stars:
            result[star_name] = sihua_type
    
    return result


def get_sihua_stars(year_stem: str) -> Dict[str, str]:
    """
    获取四化星 (便捷函数).
    
    Returns:
        {"化禄": "星名", "化权": "星名", "化科": "星名", "化忌": "星名"}
    """
    star_to_type = determine_sihua(year_stem)
    
    # 反转映射
    type_to_star = {}
    for star, stype in star_to_type.items():
        type_to_star[stype] = star
    
    return type_to_star
