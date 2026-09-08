"""Unit tests for SimulationState.hop_segments -- the per-train precomputed
(Segment, direction) sequence added in docs/segment-redesign.md's final step (the
"block section sequence per train" idea that document's "what's still open" section
tracked). Computed once at Simulation() construction from each train's own planned
route, not re-derived by blsec_id() at event time (that consolidation is separate,
unstarted follow-up work -- this only covers the precomputation itself).

Constructs real Simulation instances against the real network (same approach as
tests/test_sibling_redirect.py and tests/test_segment.py), rather than calling
.run() -- hop_segments is fully populated by the end of __init__, before the event
loop ever starts.
"""
import pandas as pd
import pytest

from iidsim.domain import train
from iidsim.engine.run import Simulation

BASE = pd.Timestamp("2025-04-01 08:00:00")


def _make_train(train_id, stations, instance_index=0):
    """stations: [(name, arrival_offset_minutes), ...] -- same arrival/departure
    time at each stop (a through train, no halting), for simplicity."""
    sched = {}
    for name, offset in stations:
        t = BASE + pd.Timedelta(minutes=offset)
        sched[name] = [t, t]
    return train(train_id, "p", sched, stations[0][0], stations[-1][0], 80, instance_index)


def _sim(trains, network_section="krdl_ktv", output_dir="."):
    return Simulation("scn_hop_segments", network_section, trains_override=trains, output_dir=output_dir)


def test_hop_segments_keyed_by_instance_id():
    tr = _make_train("T1", [("krdl", 0), ("bchl", 10)])
    sim = _sim([tr])
    assert set(sim.hop_segments.keys()) == {"T1_0"}


def test_hop_segments_one_entry_per_hop():
    tr = _make_train("T1", [("krdl", 0), ("bchl", 10), ("bhns", 20), ("kmlr", 32)])
    sim = _sim([tr])
    assert len(sim.hop_segments["T1_0"]) == 3  # 4 stations -> 3 hops


def test_hop_segments_single_station_route_has_no_hops():
    tr = _make_train("T1", [("krdl", 0)])
    sim = _sim([tr])
    assert sim.hop_segments["T1_0"] == []


def test_hop_segments_values_are_segment_and_direction_pairs():
    tr = _make_train("T1", [("krdl", 0), ("bchl", 10)])
    sim = _sim([tr])
    [(segment, direction)] = sim.hop_segments["T1_0"]
    assert segment.name == "krdl_bchl"
    assert direction in ("up", "dn")


def test_hop_segments_direction_matches_direction_of_travel():
    tr = _make_train("T1", [("krdl", 0), ("bchl", 10), ("bhns", 20)])
    sim = _sim([tr])
    for (segment, direction), (stn_a, stn_b) in zip(sim.hop_segments["T1_0"], [("krdl", "bchl"), ("bchl", "bhns")]):
        assert direction == sim.direction_of_travel(stn_a, stn_b)
        assert segment is sim.segments_by_pair[sim.conn_base(stn_a, stn_b)]


def test_hop_segments_reversed_route_gives_opposite_directions():
    forward = _make_train("T1", [("krdl", 0), ("bchl", 10)])
    reverse = _make_train("T2", [("bchl", 0), ("krdl", 10)])
    sim = _sim([forward, reverse])
    [(_, dir_fwd)] = sim.hop_segments["T1_0"]
    [(_, dir_rev)] = sim.hop_segments["T2_0"]
    assert dir_fwd != dir_rev


def test_hop_segments_covers_every_train():
    t1 = _make_train("T1", [("krdl", 0), ("bchl", 10)], instance_index=0)
    t2 = _make_train("T2", [("bchl", 0), ("bhns", 8)], instance_index=1)
    sim = _sim([t1, t2])
    assert set(sim.hop_segments.keys()) == {"T1_0", "T2_1"}


def test_hop_segments_raises_clearly_for_a_disconnected_hop():
    bad = train("BAD", "p", {
        "krdl": [BASE, BASE],
        "vzm": [BASE + pd.Timedelta(minutes=20), BASE + pd.Timedelta(minutes=20)],
    }, "krdl", "vzm", 80, 0)
    with pytest.raises(ValueError, match=r"BAD_0.*krdl.*vzm"):
        _sim([bad])
