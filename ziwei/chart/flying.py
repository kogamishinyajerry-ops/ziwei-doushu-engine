"""
宫干飞化 (Flying transformations) —— 飞星派核心可视化数据。

每个宫位的【天干】会引动四化 (化禄/权/科/忌), 落在持有对应四化星的宫位上。
连成线即"飞星连线图"。本模块在后端用 transformations.determine_sihua (SSOT)
算出飞化边, 前端只负责画线, 避免在 JS 里硬编码四化表导致漂移。
"""

from typing import Dict, List

from ..calendar.constants import EARTHLY_BRANCHES
from .transformations import determine_sihua

B = EARTHLY_BRANCHES


def compute_flying_sihua(chart) -> Dict[str, object]:
    """
    返回宫干飞化边集合。

    {
      "edges": [
        {"from_palace","from_branch","from_index","type","star",
         "to_palace","to_branch","to_index","self": bool},
        ...
      ],
      "note": "..."
    }
    self=True 表示自化 (四化星就落在本宫)。
    """
    # 星 → (palace_name, branch_index)
    star_loc: Dict[str, tuple] = {}
    branch_palace: Dict[int, str] = {}
    for p in chart.palaces:
        bi = B.index(p.branch)
        branch_palace[bi] = p.name
        for s in p.stars:
            star_loc[s] = (p.name, bi)

    edges: List[dict] = []
    for p in chart.palaces:
        stem = p.stem
        if stem not in "甲乙丙丁戊己庚辛壬癸":
            continue
        from_bi = B.index(p.branch)
        try:
            sihua = determine_sihua(stem)  # {星: 化X}
        except ValueError:
            continue
        for star, htype in sihua.items():
            loc = star_loc.get(star)
            if not loc:
                continue  # 该四化星未在盘面 (极少数情况)
            to_palace, to_bi = loc
            edges.append({
                "from_palace": p.name,
                "from_branch": p.branch,
                "from_index": from_bi,
                "type": htype,
                "star": star,
                "to_palace": to_palace,
                "to_branch": B[to_bi],
                "to_index": to_bi,
                "self": from_bi == to_bi,
            })
    return {
        "edges": edges,
        "note": "宫干飞化: 各宫天干引动四化, 落于持有该星之宫; self=自化。",
    }
