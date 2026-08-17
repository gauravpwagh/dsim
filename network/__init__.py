"""
network.py — merge the three boards into ONE network for the simulation.

Each board's *_blocksections_data.py must import ITS OWN *_stations_data.py
(not a shared 'stations_data'); they are wired that way here.
"""
from blocksections import block_sec
from stations import populate_connections

from . import psa_scmn_stations_data as A
from . import krpu_ktv_stations_data  as B
from . import krdl_vzm_stations_data  as C
from . import psa_scmn_blocksections_data as Abs
from . import krpu_ktv_blocksections_data as Bbs
from . import krdl_vzm_blocksections_data as Cbs

# 1) merged station_dict 
station_dict = {**A.station_dict, **C.station_dict, **B.station_dict}

# 2) merged station OBJECTS, if any station is duplicated at junction it willjust consider it as once only. that is why  _seen is used
stations_list = []
_seen = set()
for s in A.stations_list + C.stations_list + B.stations_list:
    if s.name in _seen:
        continue
    _seen.add(s.name)
    stations_list.append(s)

# 3) all per-board block sections
blsec_list = (
    list(Abs.blocksections_list)
    + list(Bbs.blocksections_list)
    + list(Cbs.blocksections_list)
)


# 4) the two inter-board link sections (dropped from individual boards because the
#    far endpoint wasn't in scope there). Build them ONCE against the merged list.
#    (krpu_suku is NOT a link — krpu & suku both live in the krpu_ktv board.) 
mvw_ktv_dn1 = block_sec('dn1', 'mvw', 'ktv', 8.93, {'mvw': ['s1', 's2', 's3', 's4', 's5'], 'ktv': ['s1', 's2', 's4', 's5', 's6', 's7', 's8', 's9']}, stations_list)
mvw_ktv_up1 = block_sec('up1', 'mvw', 'ktv', 8.93, {'mvw': ['s1', 's2', 's3', 's5'], 'ktv': ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's9']}, stations_list)
gtlm_vzm_dn1 = block_sec('dn1', 'gtlm', 'vzm', 5.64, {'gtlm': ['s1', 's2', 's4'], 'vzm': ['s1', 's2', 's3', 's4', 's5', 's6', 's8', 's9']}, stations_list)
gtlm_vzm_up1 = block_sec('up1', 'gtlm', 'vzm', 5.64, {'gtlm': [ 's1', 's3', 's4'], 'vzm': ['s1', 's2', 's3', 's4', 's5', 's7', 's8', 's9']}, stations_list)

blsec_list += [mvw_ktv_dn1, mvw_ktv_up1, gtlm_vzm_dn1, gtlm_vzm_up1]  
blocksections_list = blsec_list

# 5) re-populate connections across the merged network so the boundary stations
#    (ktv, vzm, krpu) pick up the cross-board links too.
populate_connections(blocksections_list, station_dict, stations_list)
