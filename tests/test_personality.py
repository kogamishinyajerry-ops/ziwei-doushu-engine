"""
Focused tests for the personality / destiny-code layer.

Covers the 空宫借对宫 (empty Ming palace borrows the opposite Migration
palace) rule, which previously fell back to a global "first 2 main stars"
simplification regardless of palace position.
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ziwei.analysis.personality import generate_destiny_code


def test_empty_ming_borrows_opposite_palace_main_stars():
    # 命宫地支 "子" (idx 0) → 迁移宫 "午" (idx 6, 对宫).
    # 紫微 在对宫午, 破军/七杀 在别处; 正确实现应借午宫的紫微,
    # 而不是按盘面顺序取破军/七杀。
    star_to_branch = {"破军": "寅", "七杀": "辰", "紫微": "午"}

    result = generate_destiny_code(
        ming_stars=[],
        shen_stars=[],
        sihua_stars=[],
        star_to_branch=star_to_branch,
        ming_branch="子",
    )

    assert "紫微" in result["full_name"]
    # 不应误取非对宫的破军作为首要借星
    assert not result["full_name"].startswith("破军")


def test_empty_ming_without_branch_falls_back_compatibly():
    # 不提供 ming_branch 时保持向后兼容: 取盘面主星候补, 不应抛错。
    star_to_branch = {"破军": "寅", "七杀": "辰", "紫微": "午"}

    result = generate_destiny_code(
        ming_stars=[],
        shen_stars=[],
        sihua_stars=[],
        star_to_branch=star_to_branch,
    )

    assert result["full_name"]
    assert result["element"]


def test_opposite_palace_also_empty_falls_back():
    # 命宫与对宫都无主星时, 回退到盘面主星候补而非崩溃。
    star_to_branch = {"紫微": "寅", "天府": "辰"}  # 子/午 均无主星

    result = generate_destiny_code(
        ming_stars=[],
        shen_stars=[],
        sihua_stars=[],
        star_to_branch=star_to_branch,
        ming_branch="子",
    )

    assert result["full_name"]
