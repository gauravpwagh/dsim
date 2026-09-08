"""Unit tests for iidsim.domain.Segment -- the station-pair grouping wrapping
SimulationState.blsec_by_pair's line objects with real identity (endpoints,
length, up/down direction from branch order). See docs/segment-redesign.md
for why this exists and how Simulation.direction_of_travel() (resolve.py)
uses it in place of the engine's old longitude comparisons. Every line
(block_sec) object keeps its own occupancy/queue state exactly as before --
Segment holds no mutable simulation state of its own.

Fixtures build real iidsim.domain.block_sec objects, same approach as
tests/test_sibling_redirect.py.
"""
import pytest

from iidsim.domain import Segment, block_sec


class _Station:
    def __init__(self, name, longitude):
        self.name = name
        self.longitude = longitude
        self.connections = {}


def _make_blsec(suffix, stn_a, stn_b, length=5.0):
    return block_sec(suffix, stn_a.name, stn_b.name, length, {stn_a.name: [], stn_b.name: []}, [stn_a, stn_b])


A = _Station("A", 0.0)
B = _Station("B", 1.0)


def test_identity_taken_from_lines():
    dn1 = _make_blsec("dn1", A, B, length=9.0)
    up1 = _make_blsec("up1", A, B, length=9.0)
    seg = Segment("a_b", [dn1, up1])
    assert seg.name == "a_b"
    assert seg.stn_west.name == "A"
    assert seg.stn_east.name == "B"
    assert seg.length == 9.0


def test_lines_preserves_given_order():
    dn1 = _make_blsec("dn1", A, B)
    up1 = _make_blsec("up1", A, B)
    mid1 = _make_blsec("mid1", A, B)
    seg = Segment("a_b", [dn1, up1, mid1])
    assert seg.lines == [dn1, up1, mid1]


def test_init_copies_the_lines_list_not_aliases_it():
    dn1 = _make_blsec("dn1", A, B)
    up1 = _make_blsec("up1", A, B)
    original = [dn1, up1]
    seg = Segment("a_b", original)
    original.append("intruder")
    assert seg.lines == [dn1, up1]


def test_rejects_empty_lines():
    with pytest.raises(ValueError):
        Segment("a_b", [])


def test_rejects_lines_with_mismatched_endpoints_or_length():
    dn1 = _make_blsec("dn1", A, B, length=5.0)
    other_pair = _make_blsec("up1", A, B, length=7.0)  # same pair, different length
    with pytest.raises(ValueError):
        Segment("a_b", [dn1, other_pair])


def test_lines_for_direction_none_returns_everything():
    dn1 = _make_blsec("dn1", A, B)
    up1 = _make_blsec("up1", A, B)
    seg = Segment("a_b", [dn1, up1])
    assert seg.lines_for_direction(None) == [dn1, up1]


def test_lines_for_direction_filters_to_matching_and_mid():
    dn1 = _make_blsec("dn1", A, B)
    up1 = _make_blsec("up1", A, B)
    mid1 = _make_blsec("mid1", A, B)
    seg = Segment("a_b", [dn1, up1, mid1])
    assert seg.lines_for_direction("dn") == [dn1, mid1]
    assert seg.lines_for_direction("up") == [up1, mid1]


def test_lines_for_direction_no_match_returns_empty():
    up1 = _make_blsec("up1", A, B)
    seg = Segment("a_b", [up1])
    assert seg.lines_for_direction("dn") == []


def test_stn_up_down_default_to_none():
    dn1 = _make_blsec("dn1", A, B)
    seg = Segment("a_b", [dn1])
    assert seg.stn_up is None
    assert seg.stn_down is None
    with pytest.raises(ValueError):
        seg.direction_of_travel("A", "B")


def test_stn_up_down_must_be_given_together():
    dn1 = _make_blsec("dn1", A, B)
    with pytest.raises(ValueError):
        Segment("a_b", [dn1], stn_up="A")
    with pytest.raises(ValueError):
        Segment("a_b", [dn1], stn_down="B")


def test_stn_up_down_must_match_segment_endpoints():
    dn1 = _make_blsec("dn1", A, B)
    with pytest.raises(ValueError):
        Segment("a_b", [dn1], stn_up="A", stn_down="somewhere_else")


def test_direction_of_travel_up_end_to_down_end_is_dn():
    dn1 = _make_blsec("dn1", A, B)
    seg = Segment("a_b", [dn1], stn_up="A", stn_down="B")
    assert seg.direction_of_travel("A", "B") == "dn"


def test_direction_of_travel_down_end_to_up_end_is_up():
    dn1 = _make_blsec("dn1", A, B)
    seg = Segment("a_b", [dn1], stn_up="A", stn_down="B")
    assert seg.direction_of_travel("B", "A") == "up"


def test_direction_of_travel_rejects_stations_not_on_this_segment():
    dn1 = _make_blsec("dn1", A, B)
    seg = Segment("a_b", [dn1], stn_up="A", stn_down="B")
    with pytest.raises(ValueError):
        seg.direction_of_travel("A", "somewhere_else")


# -- Segment.new() / add_line() -- the raw-input construction path -----------

def test_new_creates_empty_segment():
    seg = Segment.new("A", "B", 9.0, [A, B])
    assert seg.name == "A_B"
    assert seg.stn_west.name == "A"
    assert seg.stn_east.name == "B"
    assert seg.length == 9.0
    assert seg.lines == []


def test_new_west_east_follows_longitude_regardless_of_argument_order():
    seg_ab = Segment.new("A", "B", 9.0, [A, B])
    seg_ba = Segment.new("B", "A", 9.0, [A, B])
    assert seg_ab.stn_west.name == seg_ba.stn_west.name == "A"
    assert seg_ab.stn_east.name == seg_ba.stn_east.name == "B"


def test_new_raises_if_station_not_in_stations_list():
    with pytest.raises(ValueError):
        Segment.new("A", "nonexistent", 9.0, [A, B])


def test_new_has_no_branch_coverage_for_an_unknown_pair():
    seg = Segment.new("A", "B", 9.0, [A, B])
    assert seg.stn_up is None
    assert seg.stn_down is None
    with pytest.raises(ValueError):
        seg.direction_of_travel("A", "B")


def test_new_finds_branch_order_for_a_real_station_pair_by_name():
    # branch_order() is keyed purely by station name, independent of the
    # (here, arbitrary/synthetic) longitude values -- smlg/kvls are real,
    # adjacent stations in routes.KRPU_TO_KTV.
    smlg = _Station("smlg", 100.0)
    kvls = _Station("kvls", 200.0)
    seg = Segment.new("smlg", "kvls", 9.0, [smlg, kvls])
    assert seg.stn_up == "smlg"
    assert seg.stn_down == "kvls"
    assert seg.direction_of_travel("smlg", "kvls") == "dn"


def test_add_line_reuses_segment_endpoints_and_length():
    seg = Segment.new("A", "B", 9.0, [A, B])
    line = seg.add_line("dn1", {"A": ["s1"], "B": ["s1"]})
    assert line.name == "A_B_dn1"
    assert line.stn_west.name == "A"
    assert line.stn_east.name == "B"
    assert line.length == 9.0


def test_add_line_appends_to_segment_lines_and_returns_the_line():
    seg = Segment.new("A", "B", 9.0, [A, B])
    dn1 = seg.add_line("dn1", {"A": [], "B": []})
    up1 = seg.add_line("up1", {"A": [], "B": []})
    assert seg.lines == [dn1, up1]


def test_add_line_built_lines_pass_the_original_validated_constructor():
    # A Segment built the old way from add_line()'s own output should never
    # raise -- proof the two construction paths agree, not just individually
    # self-consistent.
    seg = Segment.new("A", "B", 9.0, [A, B])
    seg.add_line("dn1", {"A": [], "B": []})
    seg.add_line("up1", {"A": [], "B": []})
    rebuilt = Segment(seg.name, seg.lines, stn_up=seg.stn_up, stn_down=seg.stn_down)
    assert rebuilt.stn_west.name == "A"
    assert rebuilt.stn_east.name == "B"
