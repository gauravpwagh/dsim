"""Stage 4 of docs/event-manager-design.md: unit tests for the sibling-redirect
decision (BlockSection.find_free_sibling, moved from resolve.py's
find_free_sibling_blsec) built directly against synthetic block sections, rather
than trying to force an exact full-simulation timing coincidence -- which
tests/test_branch_coverage.py's docstring documents as having failed ~10 times.
That's the whole point of stage 4: this logic was already essentially
self-contained (every read was self/sib/explicit parameters), so once it moved
onto BlockSection it became directly testable without a network, trains, or an
event loop at all.

Fixtures build real iidsim.domain.block_sec objects (not a reimplementation) so
these tests exercise the actual production class, with minimal station stand-ins
since block_sec's constructor only needs station .name/.longitude to determine
west/east ordering -- it doesn't touch anything else this function reads.
"""
from iidsim.domain import block_sec


class _Station:
    """Minimal stand-in: block_sec's constructor only needs .name/.longitude;
    find_free_sibling's stn_obj filter only needs .connections."""

    def __init__(self, name, longitude):
        self.name = name
        self.longitude = longitude
        self.connections = {}


def _make_blsec(suffix, stn_a, stn_b):
    """A block section between stn_a and stn_b with direction suffix 'dn1'/'up1'/
    'mid1'. conns is empty on both ends -- find_free_sibling never reads stn_conns."""
    return block_sec(suffix, stn_a.name, stn_b.name, 5.0, {stn_a.name: [], stn_b.name: []}, [stn_a, stn_b])


def _lookup(*blsecs):
    return {b.name: b for b in blsecs}


# Two stations, fixed longitudes so every block section built from them shares
# the same west/east ordering (and therefore the same name base) -- exactly the
# "different suffix, same station pair" relationship find_free_sibling relies on.
A = _Station("A", 0.0)
B = _Station("B", 1.0)


def test_no_sibling_exists():
    dn1 = _make_blsec("dn1", A, B)
    assert dn1.find_free_sibling(_lookup(dn1)) is None


def test_never_returns_itself():
    # blsec_lookup contains only the section itself under every name it might
    # look for -- the `sib_name == self.name` guard must still skip it.
    dn1 = _make_blsec("dn1", A, B)
    lookup = {dn1.name: dn1}
    assert dn1.find_free_sibling(lookup) is None


def test_occupied_sibling_is_skipped():
    dn1 = _make_blsec("dn1", A, B)
    up1 = _make_blsec("up1", A, B)
    up1.occ_ind = 1
    assert dn1.find_free_sibling(_lookup(dn1, up1)) is None


def test_free_empty_sibling_is_returned():
    dn1 = _make_blsec("dn1", A, B)
    up1 = _make_blsec("up1", A, B)
    assert dn1.find_free_sibling(_lookup(dn1, up1)) is up1


def test_sibling_with_nonempty_queue_is_skipped():
    # occ_ind == 0 alone isn't "free" for redirect purposes -- a queued train
    # still waiting on it disqualifies it too.
    dn1 = _make_blsec("dn1", A, B)
    up1 = _make_blsec("up1", A, B)
    up1.blsec_queue = ["some_train_0", "some_train", "p", 3, 0, 0]
    assert dn1.find_free_sibling(_lookup(dn1, up1)) is None


def test_train_dir_filter_excludes_opposite_direction():
    dn1 = _make_blsec("dn1", A, B)
    up1 = _make_blsec("up1", A, B)
    assert dn1.find_free_sibling(_lookup(dn1, up1), train_dir="dn") is None


def test_train_dir_filter_allows_matching_direction():
    dn1 = _make_blsec("dn1", A, B)
    up1 = _make_blsec("up1", A, B)
    assert dn1.find_free_sibling(_lookup(dn1, up1), train_dir="up") is up1


def test_train_dir_filter_allows_mid_regardless_of_direction():
    dn1 = _make_blsec("dn1", A, B)
    mid1 = _make_blsec("mid1", A, B)
    assert dn1.find_free_sibling(_lookup(dn1, mid1), train_dir="up") is mid1
    assert dn1.find_free_sibling(_lookup(dn1, mid1), train_dir="dn") is mid1


def test_station_connection_filter_excludes_unconnected_sibling():
    dn1 = _make_blsec("dn1", A, B)
    up1 = _make_blsec("up1", A, B)
    A.connections = {}  # up1's connection key is absent
    assert dn1.find_free_sibling(_lookup(dn1, up1), stn_obj=A, stn_line_name="s1") is None


def test_station_connection_filter_allows_connected_sibling():
    dn1 = _make_blsec("dn1", A, B)
    up1 = _make_blsec("up1", A, B)
    A.connections = {up1.name + "_s1": ["up1", ""]}
    assert dn1.find_free_sibling(_lookup(dn1, up1), stn_obj=A, stn_line_name="s1") is up1
    A.connections = {}  # reset for other tests sharing station A


def test_priority_order_dn1_before_up1_before_mid1():
    dn1 = _make_blsec("dn1", A, B)
    up1 = _make_blsec("up1", A, B)
    mid1 = _make_blsec("mid1", A, B)
    # Called from up1 and mid1's perspective too, since find_free_sibling looks at
    # every OTHER suffix regardless of which section it's called on.
    assert up1.find_free_sibling(_lookup(dn1, up1, mid1)) is dn1
    # With dn1 occupied, up1 (called from mid1) should win over... itself is not a
    # candidate, so this checks dn1 excluded, up1 wins over nothing else free.
    dn1.occ_ind = 1
    assert mid1.find_free_sibling(_lookup(dn1, up1, mid1)) is up1
