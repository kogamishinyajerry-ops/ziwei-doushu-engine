from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def test_daxian_layout_has_twelve_ten_year_segments():
    from ziwei.chart.limits import calculate_daxian

    layout = calculate_daxian(
        ming_index=2,
        wuxing_ju=4,
        year_stem="甲",
        is_male=True,
    )

    assert len(layout.daxian) == 12
    assert list(layout.daxian.keys()) == list(range(12))

    for start, end, branch_idx in layout.daxian.values():
        assert isinstance(start, int)
        assert isinstance(end, int)
        assert isinstance(branch_idx, int)
        assert end - start == 9
        assert 0 <= branch_idx <= 11


def test_daxian_age_ranges_are_contiguous_for_all_wuxing_ju():
    from ziwei.calendar.constants import JU_TO_DAXIAN_START
    from ziwei.chart.limits import calculate_daxian

    for wuxing_ju, start_age in JU_TO_DAXIAN_START.items():
        layout = calculate_daxian(
            ming_index=6,
            wuxing_ju=wuxing_ju,
            year_stem="乙",
            is_male=False,
        )

        starts = [layout.daxian[i][0] for i in range(12)]
        ends = [layout.daxian[i][1] for i in range(12)]

        assert starts[0] == start_age
        assert starts == list(range(start_age, start_age + 120, 10))
        assert all(end == start + 9 for start, end in zip(starts, ends))
        assert all(starts[i + 1] == ends[i] + 1 for i in range(11))


def test_chart_daxian_map_matches_limit_layout():
    from ziwei.calendar.constants import EARTHLY_BRANCHES, PALACE_NAMES
    from ziwei.chart.engine import generate_chart
    from ziwei.chart.limits import calculate_daxian
    from ziwei.chart.palaces import (
        determine_wuxing_ju,
        place_palaces,
        place_stems_branches,
    )

    chart = generate_chart(
        1990,
        6,
        15,
        8,
        30,
        name="Limit Golden",
        gender="男",
    )
    layout = place_palaces(chart.lunar_month, chart.hour_pillar[1])
    layout = place_stems_branches(layout, chart.year_pillar[0])
    layout = determine_wuxing_ju(layout)
    daxian_layout = calculate_daxian(
        ming_index=layout.ming_index,
        wuxing_ju=layout.wuxing_ju,
        year_stem=chart.year_pillar[0],
        is_male=True,
    )

    branch_to_palace = {
        EARTHLY_BRANCHES[branch_idx]: palace_name
        for palace_name, branch_idx in layout.palaces.items()
    }
    expected = {}
    for start, end, branch_idx in daxian_layout.daxian.values():
        palace_name = branch_to_palace[EARTHLY_BRANCHES[branch_idx]]
        expected[palace_name] = f"{start}-{end}"

    assert len(chart.daxian) == 12
    assert set(chart.daxian.keys()) == set(PALACE_NAMES)
    assert chart.daxian == expected


def test_palace_daxian_ranges_are_consistent_with_chart_map():
    from ziwei.chart.engine import generate_chart

    chart = generate_chart(
        1991,
        12,
        8,
        23,
        15,
        name="Palace Limit Golden",
        gender="女",
    )

    assert len(chart.palaces) == 12

    for palace in chart.palaces:
        assert palace.daxian_range
        assert palace.daxian_range == f"{chart.daxian[palace.name]}岁"

        start, end = map(int, chart.daxian[palace.name].split("-"))
        assert end - start == 9
