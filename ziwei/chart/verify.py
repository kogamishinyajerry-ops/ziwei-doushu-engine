"""
命盘指纹校验 + 可分享二维码 (② 指纹做成可分享的二维码/校验页)。

差异化闭环: 指纹不只是"展示一串 hash", 而是任何人拿到出生数据(+流派)就能
**独立复算并比对**——把"结果你只能信"翻转成"结果你能自己验"。

- verify_fingerprint(): 用同一出生输入重排命盘, 复算指纹, 与声称值比对。
- build_verify_url(): 生成可分享/可扫码的校验链接 (前端 ?verify=1 自动复算)。
- make_verify_qr_svg(): 纯 Python (segno) 生成内联 SVG 二维码, 离线可用、无 CDN。
"""

from typing import Dict, Optional
from urllib.parse import urlencode

from .engine import generate_chart
from .fingerprint import chart_fingerprint

# 复算指纹所需的出生输入 (name/gender 不影响指纹 payload, 故不参与)
FINGERPRINT_INPUT_FIELDS = ("year", "month", "day", "hour", "minute", "city", "huoling")


def verify_fingerprint(
    year: int, month: int, day: int, hour: int,
    minute: int = 0, city: str = "",
    huoling: str = "mainstream",
    claimed_fingerprint: Optional[str] = None,
) -> Dict:
    """
    用同一出生输入重排命盘并复算指纹, 与声称的指纹比对。

    Returns:
        {
          "computed": {fingerprint, sha256, version, verify},
          "claimed": "<声称值或 None>",
          "match": True/False/None,   # None = 未提供声称值, 仅复算
          "inputs": {...},
        }
    """
    chart = generate_chart(
        year, month, day, hour, minute,
        name="", gender="男", city=city or "",
        huoling_variant=huoling or "mainstream",
    )
    fp = chart_fingerprint(chart)

    claimed = (claimed_fingerprint or "").strip()
    match: Optional[bool] = None
    if claimed:
        # 同时接受短指纹 (ZW1-xxxx, 大小写不敏感) 与完整 sha256
        c = claimed
        match = (
            c.upper() == fp["fingerprint"].upper()
            or c.lower() == fp["sha256"].lower()
        )

    return {
        "computed": fp,
        "claimed": claimed or None,
        "match": match,
        "inputs": {
            "year": year, "month": month, "day": day, "hour": hour,
            "minute": minute, "city": city or "",
            "huoling": huoling or "mainstream",
        },
    }


def build_verify_url(
    year: int, month: int, day: int, hour: int,
    minute: int = 0, city: str = "",
    huoling: str = "mainstream",
    fingerprint: str = "",
    base_url: str = "",
) -> str:
    """
    生成可分享的校验链接。打开后前端读取 ?verify=1 自动复算并比对指纹。

    只编码复算指纹必需的字段 (不含姓名/性别, 隐私更友好)。
    """
    params = {
        "verify": "1",
        "year": year, "month": month, "day": day, "hour": hour,
        "minute": minute, "city": city or "",
        "huoling": huoling or "mainstream",
    }
    if fingerprint:
        params["fp"] = fingerprint
    base = (base_url or "").rstrip("/")
    return f"{base}/?{urlencode(params)}"


def make_verify_qr_svg(data: str, scale: int = 4, dark: str = "#0a0a14") -> str:
    """
    把字符串 (通常是 build_verify_url 的结果) 编码成内联 SVG 二维码。

    纯 Python (segno), 零外部网络/CDN 依赖, 适合离线工作台。
    返回可直接塞进 HTML 的 <svg> 字符串。
    """
    import io

    import segno

    qr = segno.make(data, error="m")
    buf = io.BytesIO()
    qr.save(
        buf, kind="svg", scale=scale, border=2,
        dark=dark, light="#ffffff", xmldecl=False, svgns=True,
    )
    return buf.getvalue().decode("utf-8")
