"""
Structural invariant tests for chart generation.

These do not assert school-specific interpretive values. They lock in
hard structural rules that ANY correct Zi Wei Dou Shu chart must satisfy,
which makes them robust regression guards independent of style/school.

Background: a P0 bug placed the 天府 star system on the wrong reflection
axis (卯酉 instead of the canonical 寅申), misplacing 8 of the 14 main
stars on every chart. test_ziwei_tianfu_yin_shen_axis locks the fix.
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ziwei.chart.engine import generate_chart
from ziwei.chart.stars import (
    ZIWEI_IDX_TO_TIANFU_IDX,
    StarLayout,
    place_tianfu_series,
    place_ziwei_series,
)
from ziwei.calendar.constants import EARTHLY_BRANCHES, PALACE_NAMES


def _layout_for_ziwei(ziwei_idx: int) -> StarLayout:
    """构造仅由紫微位置决定的 14 主星布局 (绕过历法, 直接验证安星律)."""
    layout = StarLayout(ziwei_index=ziwei_idx)
    layout.stars["紫微"] = ziwei_idx
    layout = place_tianfu_series(layout)
    layout = place_ziwei_series(layout)
    return layout


ZIWEI_SERIES = {"紫微", "天机", "太阳", "武曲", "天同", "廉贞"}
TIANFU_SERIES = {"天府", "太阴", "贪狼", "巨门", "天相", "天梁", "七杀", "破军"}
MAIN_14 = ZIWEI_SERIES | TIANFU_SERIES
SIHUA_TYPES = {"化禄", "化权", "化科", "化忌"}
# 身宫只可能落在这六宫之一
SHEN_PALACES = {"命宫", "夫妻", "财帛", "迁移", "官禄", "福德"}

# 跨月/日/时/性别的确定性网格 (不用随机, 保证可复现)
GRID = [
    (1984, 1, 5, 0, "男"),
    (1990, 2, 14, 3, "女"),
    (1995, 4, 1, 6, "男"),
    (1998, 3, 21, 8, "男"),
    (2000, 6, 18, 11, "女"),
    (2003, 8, 8, 13, "男"),
    (2008, 10, 24, 16, "女"),
    (2012, 11, 30, 19, "男"),
    (2016, 12, 25, 22, "女"),
    (2020, 5, 5, 23, "男"),
    (1976, 7, 7, 5, "女"),
    (1962, 9, 9, 9, "男"),
]


def _branch_idx(branch: str) -> int:
    return EARTHLY_BRANCHES.index(branch)


def test_ziwei_tianfu_yin_shen_axis():
    """天府与紫微关于寅申轴对称: 天府_idx = (4 - 紫微_idx) % 12."""
    m = ZIWEI_IDX_TO_TIANFU_IDX
    # 寅(2)/申(8) 同宫 (canonical anchor)
    assert m[2] == 2, "紫微在寅时天府应同宫于寅"
    assert m[8] == 8, "紫微在申时天府应同宫于申"
    # 其它公开锚点
    assert m[0] == 4, "紫微子 → 天府辰"
    assert m[6] == 10, "紫微午 → 天府戌"
    # 全周对称律
    for z in range(12):
        assert m[z] == (4 - z) % 12


def test_twelve_palaces_occupy_distinct_branches():
    for params in GRID:
        chart = generate_chart(*params[:4], 0, "T", params[4])
        branches = [_branch_idx(p.branch) for p in chart.palaces]
        assert len(branches) == 12
        assert len(set(branches)) == 12, f"{params}: 宫位地支不是双射"


def test_ming_and_qianyi_palaces_are_opposite():
    for params in GRID:
        chart = generate_chart(*params[:4], 0, "T", params[4])
        pb = {p.name: _branch_idx(p.branch) for p in chart.palaces}
        assert (pb["命宫"] - pb["迁移"]) % 12 == 6, f"{params}: 命宫/迁移非对宫"


def test_all_fourteen_main_stars_placed_once():
    for params in GRID:
        chart = generate_chart(*params[:4], 0, "T", params[4])
        mains = [s for p in chart.palaces for s in p.stars if s in MAIN_14]
        assert sorted(mains) == sorted(MAIN_14), (
            f"{params}: 主星缺失/重复 -> 缺 {sorted(MAIN_14 - set(mains))}"
        )


def test_ziwei_tianfu_symmetry_holds_in_generated_charts():
    for params in GRID:
        chart = generate_chart(*params[:4], 0, "T", params[4])
        sb = {}
        for p in chart.palaces:
            for s in p.stars:
                if s in ("紫微", "天府"):
                    sb[s] = _branch_idx(p.branch)
        assert sb["天府"] == (4 - sb["紫微"]) % 12, f"{params}: 紫微天府未在寅申轴对称"


def test_sihua_is_exactly_four_canonical_types():
    for params in GRID:
        chart = generate_chart(*params[:4], 0, "T", params[4])
        assert len(chart.sihua_map) == 4, f"{params}: 四化数量 != 4"
        assert set(chart.sihua_map.values()) == SIHUA_TYPES, f"{params}: 四化类型异常"


def test_main_star_offsets_are_canonical_for_all_ziwei_positions():
    """对全部 12 个紫微位置, 校验紫微系/天府系系内偏移符合 canonical 安星诀."""
    zw_off = {"天机": -1, "太阳": -3, "武曲": -4, "天同": -5, "廉贞": -8}
    tf_off = {"太阴": 1, "贪狼": 2, "巨门": 3, "天相": 4,
              "天梁": 5, "七杀": 6, "破军": 10}
    for zw in range(12):
        layout = _layout_for_ziwei(zw)
        fu = layout.stars["天府"]
        assert fu == (4 - zw) % 12
        for star, off in zw_off.items():
            assert layout.stars[star] == (zw + off) % 12, f"紫微{zw} {star} 偏移错"
        for star, off in tf_off.items():
            assert layout.stars[star] == (fu + off) % 12, f"天府{fu} {star} 偏移错"


def test_pojun_always_opposite_tianxiang():
    """破军永远与天相对宫 (差6) — 锁死破军 '七杀空三' 定位修复。"""
    for zw in range(12):
        layout = _layout_for_ziwei(zw)
        assert (layout.stars["破军"] - layout.stars["天相"]) % 12 == 6


def test_qisha_always_opposite_tianfu():
    """七杀永远与天府对宫 (差6)。"""
    for zw in range(12):
        layout = _layout_for_ziwei(zw)
        assert (layout.stars["七杀"] - layout.stars["天府"]) % 12 == 6


def test_lianzhen_tianxiang_conjunct_when_ziwei_in_shen():
    """紫微在申(8)时, 廉贞天相同宫于子 — 锁死廉贞 紫微-8 定位修复。"""
    layout = _layout_for_ziwei(8)
    assert layout.stars["廉贞"] == layout.stars["天相"] == 0


def test_shen_palace_falls_in_valid_palace():
    for params in GRID:
        chart = generate_chart(*params[:4], 0, "T", params[4])
        shen_idx = _branch_idx(chart.shen_palace[-1])
        names = {p.name for p in chart.palaces if _branch_idx(p.branch) == shen_idx}
        assert names & SHEN_PALACES, f"{params}: 身宫落在非法宫位 {names}"
