"""
命盘可验证指纹 (Verifiable chart fingerprint)。

把一张命盘的【结构化排盘结果】做确定性序列化 + SHA-256, 产出可复算、可分享、
可校验的指纹。差异化价值: 任何人用同一生辰(+流派)重排即得同一指纹, 证明这张盘
不是凭空编造或事后篡改——与测测式黑箱"结果你只能信"相反。

指纹只覆盖【排盘事实】(命身宫/十二宫干支星曜/四化/五行局/四柱), 不含 name、city
显示、quality_flags、解读文本等非结构字段——因为城市/真太阳时的影响已经体现在最终
落宫里, 指纹认的是"盘", 不是"怎么填的表"。
"""

import hashlib
import json
from typing import Dict

FINGERPRINT_VERSION = "zw1"


def _canonical_payload(chart) -> dict:
    """命盘结构化排盘事实的规范化表示 (确定性, 与显示/解读无关)。"""
    palaces = []
    for p in chart.palaces:
        palaces.append({
            "name": p.name,
            "stem": p.stem,
            "branch": p.branch,
            "stars": sorted(p.stars or []),
            "is_body": bool(p.is_body),
        })
    # 按宫名排序, 消除潜在顺序差异
    palaces.sort(key=lambda x: x["name"])
    return {
        "v": FINGERPRINT_VERSION,
        "ming_palace": chart.ming_palace,
        "shen_palace": chart.shen_palace,
        "wuxing_ju": chart.wuxing_ju_name,
        "four_pillars": [
            chart.year_pillar, chart.month_pillar,
            chart.day_pillar, chart.hour_pillar,
        ],
        "sihua": dict(sorted((chart.sihua_map or {}).items())),
        "palaces": palaces,
    }


def chart_fingerprint(chart) -> Dict[str, str]:
    """
    返回命盘指纹。

    {
      "fingerprint": "ZW1-a1b2c3d4e5f6",   # 可分享的短指纹
      "sha256": "<full hex>",               # 完整哈希, 供严格校验
      "version": "zw1",
      "verify": "用同一出生数据(+流派)重排可复算此指纹"
    }
    """
    payload = _canonical_payload(chart)
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    digest = hashlib.sha256(blob.encode("utf-8")).hexdigest()
    short = f"ZW1-{digest[:12]}"
    return {
        "fingerprint": short,
        "sha256": digest,
        "version": FINGERPRINT_VERSION,
        "verify": "用同一出生数据(含火铃流派)重排可复算此指纹; 不依赖姓名/城市显示字段。",
    }
