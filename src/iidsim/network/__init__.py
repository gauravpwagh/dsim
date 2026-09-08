"""network.py -- merge the three boards into ONE network for the simulation.

Each board module (network/boards/*.py) owns its own station/block-section objects;
this module merges them and adds the hand-specified inter-board link sections.
"""
from iidsim.domain import populate_connections, Segment

from .boards import psa_scmn as A
from .boards import krpu_ktv as B
from .boards import krdl_vzm as C

# 1) merged station_dict
station_dict = {**A.station_dict, **C.station_dict, **B.station_dict}

# 2) merged station OBJECTS -- a station duplicated at a junction is only kept once
stations_list = []
_seen = set()
for s in A.stations_list + C.stations_list + B.stations_list:
    if s.name in _seen:
        continue
    _seen.add(s.name)
    stations_list.append(s)

# 3) all per-board block sections
blsec_list = (
    list(A.blocksections_list)
    + list(B.blocksections_list)
    + list(C.blocksections_list)
)

# 4) the two inter-board link sections (dropped from individual boards because the
#    far endpoint wasn't in scope there). Built once against the merged list.
_seg_mvw_ktv = Segment.new('mvw', 'ktv', 8.93, stations_list)
mvw_ktv_dn1 = _seg_mvw_ktv.add_line('dn1', {'mvw': ['s1', 's2', 's3', 's4', 's5'], 'ktv': ['s1', 's2', 's4', 's5', 's6', 's7', 's8', 's9']})
mvw_ktv_up1 = _seg_mvw_ktv.add_line('up1', {'mvw': ['s1', 's2', 's3', 's5'], 'ktv': ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's9']})
_seg_gtlm_vzm = Segment.new('gtlm', 'vzm', 5.64, stations_list)
gtlm_vzm_dn1 = _seg_gtlm_vzm.add_line('dn1', {'gtlm': ['s1', 's2', 's4'], 'vzm': ['s1', 's2', 's3', 's4', 's5', 's6', 's8', 's9']})
gtlm_vzm_up1 = _seg_gtlm_vzm.add_line('up1', {'gtlm': [ 's1', 's3', 's4'], 'vzm': ['s1', 's2', 's3', 's4', 's5', 's7', 's8', 's9']})

blsec_list += [mvw_ktv_dn1, mvw_ktv_up1, gtlm_vzm_dn1, gtlm_vzm_up1]
blocksections_list = blsec_list

# 4.5) merged segments -- one Segment per station pair, across all three boards
#      plus the two inter-board bridges above. state.py consumes this dict
#      directly (see docs/segment-redesign.md) instead of re-deriving fresh
#      Segment objects from blocksections_list on every Simulation() call, so
#      this dict -- built once, here, at import time -- is the actual source
#      of truth the engine uses. A board's own segments_by_pair only ever
#      covers pairs that board itself declared (verified no two boards ever
#      define the same pair -- checked directly before relying on this, not
#      assumed, since a naive dict-merge would otherwise silently drop one
#      side of a collision), so a plain dict update is safe; still asserted
#      here rather than silently trusted, in case a future board changes that.
segments_by_pair = {}
for _board_segments in (A.segments_by_pair, B.segments_by_pair, C.segments_by_pair):
    _collisions = set(segments_by_pair) & set(_board_segments)
    if _collisions:
        raise ValueError(f"network: two boards both define segment(s) {_collisions}")
    segments_by_pair.update(_board_segments)
for _seg in (_seg_mvw_ktv, _seg_gtlm_vzm):
    if _seg.name in segments_by_pair:
        raise ValueError(f"network: inter-board bridge {_seg.name!r} collides with a board's own segment")
    segments_by_pair[_seg.name] = _seg

# 5) re-populate connections across the merged network so the boundary stations
#    (ktv, vzm, krpu) pick up the cross-board links too.
populate_connections(blocksections_list, station_dict, stations_list)

# 6) one-time sanity check, paid once here at import time rather than on every
#    Simulation() call: segments_by_pair's lines and blocksections_list should
#    be the exact same set of block_sec objects, just organized two different
#    ways (grouped by segment vs. one flat list) -- not a value-agreement
#    check (that's structurally guaranteed now, see docs/segment-redesign.md),
#    but a check that the two merges above didn't omit or duplicate anything.
#
#    One known, pre-existing exception: krdl_vzm.py declares vbl_dnv_mid1 (a
#    third, mid1, line alongside vbl_dnv's dn1/up1) but never includes it in
#    blocksections_list -- unlike similar unused extra lines elsewhere in that
#    file, which are left as disabled comments, this one is live code that
#    just never made it into the list. Predates this check entirely (verified
#    against the pre-step-4 board file too, not introduced by this rewrite).
#    Left exactly as found rather than guessed at -- excluded here by name so
#    it doesn't mask a *different*, future omission.
_KNOWN_ORPHANED_LINES = {'vbl_dnv_mid1'}
_from_segments = {
    line for seg in segments_by_pair.values() for line in seg.lines
    if line.name not in _KNOWN_ORPHANED_LINES
}
if _from_segments != set(blocksections_list):
    raise ValueError(
        "network: segments_by_pair's lines and blocksections_list disagree -- "
        f"only in segments: {[l.name for l in _from_segments - set(blocksections_list)]}, "
        f"only in blocksections_list: {[l.name for l in set(blocksections_list) - _from_segments]}"
    )
