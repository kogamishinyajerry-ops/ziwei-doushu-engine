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
from ziwei.chart.stars import ZIWEI_IDX_TO_TIANFU_IDX
from ziwei.calendar.constants import EARTHLY_BRANCHES, PALACE_NAMES


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


def test_shen_palace_falls_in_valid_palace():
    for params in GRID:
        chart = generate_chart(*params[:4], 0, "T", params[4])
        shen_idx = _branch_idx(chart.shen_palace[-1])
        names = {p.name for p in chart.palaces if _branch_idx(p.branch) == shen_idx}
        assert names & SHEN_PALACES, f"{params}: 身宫落在非法宫位 {names}"
