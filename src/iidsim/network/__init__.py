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

# 5) re-populate connections across the merged network so the boundary stations
#    (ktv, vzm, krpu) pick up the cross-board links too.
populate_connections(blocksections_list, station_dict, stations_list)
