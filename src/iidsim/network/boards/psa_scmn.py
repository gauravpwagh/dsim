"""psa_scmn board: stations + block sections. Merged from network/psa_scmn_stations_data.py
and network/psa_scmn_blocksections_data.py during the src/ package restructure."""
import pandas as pd

from iidsim.domain import create_station_class, populate_connections, Segment
from iidsim.data.geography import station_longitudes as _station_longitudes_fn

station_longitudes = _station_longitudes_fn()


# Converted from the old single-file format (psa_scmn_stations.py).
# Connections are intentionally left EMPTY here; they are filled by
# populate_connections() (called from psa_scmn_blocksections_data.py)
# from each block section's conns argument.

station_dict = {
    'pun'  : {"tracks": {"s1": 1, "s2": 2, "s3": 0, "s4": 3}, "connections": {}},
    'nwp'  : {"tracks": {"s1": 1, "s2": 0, "s3": 3, "s4": 4, "s5": 0}, "connections": {}},
    'kbm'  : {"tracks": {"s1": 1, "s2": 0, "s3": 2, "s4": 3}, "connections": {}},
    'tiu'  : {"tracks": {"s1": 1, "s2": 2, "s3": 3, "s4": 4}, "connections": {}},
    'ulm'  : {"tracks": {"s1": 1, "s2": 2, "s3": 3, "s4": 4}, "connections": {}},
    'che'  : {"tracks": {"s1": 1, "s2": 2, "s3": 3, "s4": 4, "s5": 0}, "connections": {}},
    'dusi' : {"tracks": {"s1": 1, "s2": 2, "s3": 3, "s4": 0}, "connections": {}},
    'pdu'  : {"tracks": {"s1": 1, "s2": 2, "s3": 3, "s4": 0}, "connections": {}},
    'sgdm' : {"tracks": {"s1": 1, "s2": 2, "s3": 3, "s4": 4}, "connections": {}},
    'cpp'  : {"tracks": {"s1": 1, "s2": 0, "s3": 2, "s4": 3, "s5": 0}, "connections": {}},
    'gvi'  : {"tracks": {"s1": 1, "s2": 2, "s3": 3, "s4": 4}, "connections": {}},
    'nml'  : {"tracks": {"s1": 1, "s2": 0, "s3": 2}, "connections": {}},
    'vzm'  : {"tracks": {"s1": 1, "s2": 2, "s3": 3, "s4": 4, "s5": 5, "s6": 0, "s7": 0, "s8": 0, "s9": 0}, "connections": {}},
    'kuk'  : {"tracks": {"s1": 1, "s2": 2, "s3": 3, "s4": 4, "s5": 5}, "connections": {}},
    'alm'  : {"tracks": {"s1": 1, "s2": 2, "s3": 3, "s4": 4, "s5": 5}, "connections": {}},
    'kpl'  : {"tracks": {"s1": 1, "s2": 2, "s3": 3, "s4": 4, "s5": 5, "s6": 0}, "connections": {}},
    'ktv'  : {"tracks": {"s1": 1, "s2": 2, "s3": 3, "s4": 4, "s5": 5, "s6": 0, "s7": 0, "s8": 0, "s9": 6}, "connections": {}},
    'pdt'  : {"tracks": {"s1": 1, "s2": 2, "s3": 0, "s4": 3, "s5": 4, "s6": 5, "s7": 6, "s8": 7}, "connections": {}},
    'scmn' : {"tracks": {"s1": 0, "s2": 0, "s3": 0, "s4": 0, "s5": 0, "s6": 0, "s7": 0, "s8": 1, "s9": 2, "s10": 3, "s11": 4, "s12": 0}, "connections": {}},
}

# -- Station object instantiation (longitude from stations_longitude.py) --
pun  = create_station_class('pun', station_longitudes['pun'], station_dict['pun'])
nwp  = create_station_class('nwp', station_longitudes['nwp'], station_dict['nwp'])
kbm  = create_station_class('kbm', station_longitudes['kbm'], station_dict['kbm'])
tiu  = create_station_class('tiu', station_longitudes['tiu'], station_dict['tiu'])
ulm  = create_station_class('ulm', station_longitudes['ulm'], station_dict['ulm'])
che  = create_station_class('che', station_longitudes['che'], station_dict['che'])
dusi = create_station_class('dusi', station_longitudes['dusi'], station_dict['dusi'])
pdu  = create_station_class('pdu', station_longitudes['pdu'], station_dict['pdu'])
sgdm = create_station_class('sgdm', station_longitudes['sgdm'], station_dict['sgdm'])
cpp  = create_station_class('cpp', station_longitudes['cpp'], station_dict['cpp'])
gvi  = create_station_class('gvi', station_longitudes['gvi'], station_dict['gvi'])
nml  = create_station_class('nml', station_longitudes['nml'], station_dict['nml'])
vzm  = create_station_class('vzm', station_longitudes['vzm'], station_dict['vzm'])
kuk  = create_station_class('kuk', station_longitudes['kuk'], station_dict['kuk'])
alm  = create_station_class('alm', station_longitudes['alm'], station_dict['alm'])
kpl  = create_station_class('kpl', station_longitudes['kpl'], station_dict['kpl'])
ktv  = create_station_class('ktv', station_longitudes['ktv'], station_dict['ktv'])
pdt  = create_station_class('pdt', station_longitudes['pdt'], station_dict['pdt'])
scmn = create_station_class('scmn', station_longitudes['scmn'], station_dict['scmn'])

stations_list = [pun, nwp, kbm, tiu, ulm, che, dusi, pdu, sgdm, cpp, gvi, nml, vzm, kuk, alm, kpl, ktv, pdt, scmn]



# Converted from psa_scmn_blocksections.py (old int dir 0/1/2 -> dn1/up1/mid1).
# block_sec decides west_east naming from longitude; conns inverted from the
# old station-side connection lists. ktv_pdt / pdt_scmn each had TWO single-
# line sections (old _20 / _21) -> emitted as mid1 / mid2.


segments_by_pair = {}
_seg_pun_nwp = Segment.new('pun', 'nwp', 13.24, stations_list)
segments_by_pair[_seg_pun_nwp.name] = _seg_pun_nwp
pun_nwp_dn1 = _seg_pun_nwp.add_line('dn1', {'pun': ['s1', 's2'], 'nwp': ['s2', 's3']})
pun_nwp_up1 = _seg_pun_nwp.add_line('up1', {'pun': ['s1', 's3', 's4'], 'nwp': ['s2', 's4', 's5']})

_seg_nwp_kbm = Segment.new('nwp', 'kbm', 13.92, stations_list)
segments_by_pair[_seg_nwp_kbm.name] = _seg_nwp_kbm
nwp_kbm_dn1 = _seg_nwp_kbm.add_line('dn1', {'nwp': ['s2', 's3'], 'kbm': ['s1', 's2']})
nwp_kbm_up1 = _seg_nwp_kbm.add_line('up1', {'nwp': ['s2', 's4', 's5'], 'kbm': ['s1', 's3', 's4']})

_seg_kbm_tiu = Segment.new('kbm', 'tiu', 13.72, stations_list)
segments_by_pair[_seg_kbm_tiu.name] = _seg_kbm_tiu
kbm_tiu_dn1 = _seg_kbm_tiu.add_line('dn1', {'kbm': ['s1', 's2'], 'tiu': ['s1', 's2']})
kbm_tiu_up1 = _seg_kbm_tiu.add_line('up1', {'kbm': ['s1', 's3', 's4'], 'tiu': ['s1', 's3', 's4']})

_seg_tiu_ulm = Segment.new('tiu', 'ulm', 9.63, stations_list)
segments_by_pair[_seg_tiu_ulm.name] = _seg_tiu_ulm
tiu_ulm_dn1 = _seg_tiu_ulm.add_line('dn1', {'tiu': ['s1', 's2'], 'ulm': ['s1', 's2']})
tiu_ulm_up1 = _seg_tiu_ulm.add_line('up1', {'tiu': ['s1', 's3', 's4'], 'ulm': ['s1', 's3', 's4']})

_seg_ulm_che = Segment.new('ulm', 'che', 10.04, stations_list)
segments_by_pair[_seg_ulm_che.name] = _seg_ulm_che
ulm_che_dn1 = _seg_ulm_che.add_line('dn1', {'ulm': ['s1', 's2'], 'che': ['s1', 's2', 's4', 's5']})
ulm_che_up1 = _seg_ulm_che.add_line('up1', {'ulm': ['s1', 's3', 's4'], 'che': ['s3', 's4', 's5']})

_seg_che_dusi = Segment.new('che', 'dusi', 6.46, stations_list)
segments_by_pair[_seg_che_dusi.name] = _seg_che_dusi
che_dusi_dn1 = _seg_che_dusi.add_line('dn1', {'che': ['s1', 's2', 's4', 's5'], 'dusi': ['s1', 's2']})
che_dusi_up1 = _seg_che_dusi.add_line('up1', {'che': ['s3', 's4', 's5'], 'dusi': ['s3', 's4']})

_seg_dusi_pdu = Segment.new('dusi', 'pdu', 8.82, stations_list)
segments_by_pair[_seg_dusi_pdu.name] = _seg_dusi_pdu
dusi_pdu_dn1 = _seg_dusi_pdu.add_line('dn1', {'dusi': ['s1', 's2'], 'pdu': ['s1', 's2', 's3']})
dusi_pdu_up1 = _seg_dusi_pdu.add_line('up1', {'dusi': ['s3', 's4'], 'pdu': ['s1', 's2', 's4']})

_seg_pdu_sgdm = Segment.new('pdu', 'sgdm', 10.07, stations_list)
segments_by_pair[_seg_pdu_sgdm.name] = _seg_pdu_sgdm
pdu_sgdm_dn1 = _seg_pdu_sgdm.add_line('dn1', {'pdu': ['s1', 's2', 's3'], 'sgdm': ['s1', 's2', 's3']})
pdu_sgdm_up1 = _seg_pdu_sgdm.add_line('up1', {'pdu': ['s1', 's2', 's4'], 'sgdm': ['s3', 's4']})

_seg_sgdm_cpp = Segment.new('sgdm', 'cpp', 13.27, stations_list)
segments_by_pair[_seg_sgdm_cpp.name] = _seg_sgdm_cpp
sgdm_cpp_dn1 = _seg_sgdm_cpp.add_line('dn1', {'sgdm': ['s1', 's2', 's3'], 'cpp': ['s1', 's2', 's4']})
sgdm_cpp_up1 = _seg_sgdm_cpp.add_line('up1', {'sgdm': ['s3', 's4'], 'cpp': ['s2', 's3', 's4', 's5']})

_seg_cpp_gvi = Segment.new('cpp', 'gvi', 6.57, stations_list)
segments_by_pair[_seg_cpp_gvi.name] = _seg_cpp_gvi
cpp_gvi_dn1 = _seg_cpp_gvi.add_line('dn1', {'cpp': ['s1', 's2', 's4'], 'gvi': ['s1', 's2', 's4']})
cpp_gvi_up1 = _seg_cpp_gvi.add_line('up1', {'cpp': ['s3', 's4', 's5'], 'gvi': ['s3', 's4']})

_seg_gvi_nml = Segment.new('gvi', 'nml', 12.33, stations_list)
segments_by_pair[_seg_gvi_nml.name] = _seg_gvi_nml
gvi_nml_dn1 = _seg_gvi_nml.add_line('dn1', {'gvi': ['s1', 's2', 's4'], 'nml': ['s1', 's3']})
gvi_nml_up1 = _seg_gvi_nml.add_line('up1', {'gvi': ['s3', 's4'], 'nml': ['s2', 's3']})

_seg_nml_vzm = Segment.new('nml', 'vzm', 11.74, stations_list)
segments_by_pair[_seg_nml_vzm.name] = _seg_nml_vzm
nml_vzm_dn1 = _seg_nml_vzm.add_line('dn1', {'nml': ['s1', 's3'], 'vzm': ['s1', 's2', 's3', 's4', 's5', 's6', 's8', 's9']})
nml_vzm_up1 = _seg_nml_vzm.add_line('up1', {'nml': ['s2', 's3'], 'vzm': ['s1', 's2', 's3', 's4', 's5', 's7', 's8', 's9']})

_seg_vzm_kuk = Segment.new('vzm', 'kuk', 10.65, stations_list)
segments_by_pair[_seg_vzm_kuk.name] = _seg_vzm_kuk
vzm_kuk_dn1 = _seg_vzm_kuk.add_line('dn1', {'vzm': ['s1', 's2', 's3', 's4', 's5', 's6', 's8', 's9'], 'kuk': ['s1', 's2', 's3']})
vzm_kuk_up1 = _seg_vzm_kuk.add_line('up1', {'vzm': ['s1', 's2', 's3', 's4', 's5', 's7', 's8', 's9'], 'kuk': ['s2', 's3', 's4', 's5']})
vzm_kuk_mid1 = _seg_vzm_kuk.add_line('mid1', {'vzm': ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9'], 'kuk': ['s2', 's3']})

_seg_kuk_alm = Segment.new('kuk', 'alm', 7.11, stations_list)
segments_by_pair[_seg_kuk_alm.name] = _seg_kuk_alm
kuk_alm_dn1 = _seg_kuk_alm.add_line('dn1', {'kuk': ['s1', 's2', 's3'], 'alm': ['s1', 's2', 's3', 's5']})
kuk_alm_up1 = _seg_kuk_alm.add_line('up1', {'kuk': ['s2', 's3', 's4', 's5'], 'alm': ['s3', 's4', 's5']})
kuk_alm_mid1 = _seg_kuk_alm.add_line('mid1', {'kuk': ['s2', 's3', 's4', 's5'], 'alm': ['s2', 's3', 's4', 's5']})

_seg_alm_kpl = Segment.new('alm', 'kpl', 9.23, stations_list)
segments_by_pair[_seg_alm_kpl.name] = _seg_alm_kpl
alm_kpl_dn1 = _seg_alm_kpl.add_line('dn1', {'alm': ['s1', 's2', 's3', 's5'], 'kpl': ['s1', 's2', 's3', 's5', 's6']})
alm_kpl_up1 = _seg_alm_kpl.add_line('up1', {'alm': ['s3', 's4', 's5'], 'kpl': ['s3', 's4', 's5', 's6']})
alm_kpl_mid1 = _seg_alm_kpl.add_line('mid1', {'alm': ['s2', 's3', 's4', 's5', 's6'], 'kpl': ['s2', 's3', 's4', 's5', 's6']})

_seg_kpl_ktv = Segment.new('kpl', 'ktv', 7.74, stations_list)
segments_by_pair[_seg_kpl_ktv.name] = _seg_kpl_ktv
kpl_ktv_dn1 = _seg_kpl_ktv.add_line('dn1', {'kpl': ['s1', 's2', 's3', 's5', 's6'], 'ktv': ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9']})
kpl_ktv_up1 = _seg_kpl_ktv.add_line('up1', {'kpl': ['s3', 's4', 's5', 's6'], 'ktv': ['s1', 's2', 's3', 's6', 's7', 's8', 's9']})
kpl_ktv_mid1 = _seg_kpl_ktv.add_line('mid1', {'kpl': ['s1', 's2', 's3', 's4', 's5', 's6'], 'ktv': ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9']})

_seg_ktv_pdt = Segment.new('ktv', 'pdt', 8.92, stations_list)
segments_by_pair[_seg_ktv_pdt.name] = _seg_ktv_pdt
ktv_pdt_dn1 = _seg_ktv_pdt.add_line('dn1', {'ktv': ['s1', 's2', 's4', 's5', 's6', 's7', 's9'], 'pdt': ['s1', 's2', 's3', 's4', 's5', 's6', 's8']})
ktv_pdt_up1 = _seg_ktv_pdt.add_line('up1', {'ktv': ['s1', 's2', 's6', 's7', 's8', 's9'], 'pdt': ['s1', 's2', 's4', 's5', 's6', 's7', 's8']})
ktv_pdt_mid1 = _seg_ktv_pdt.add_line('mid1', {'ktv': ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9'], 'pdt': ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8']})
ktv_pdt_mid2 = _seg_ktv_pdt.add_line('mid2', {'ktv': ['s1', 's2', 's4', 's5', 's6', 's7', 's8', 's9'], 'pdt': ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8']})

_seg_pdt_scmn = Segment.new('pdt', 'scmn', 7.9, stations_list)
segments_by_pair[_seg_pdt_scmn.name] = _seg_pdt_scmn
pdt_scmn_dn1 = _seg_pdt_scmn.add_line('dn1', {'pdt': ['s1', 's2', 's3', 's4', 's5', 's6', 's8'], 'scmn': ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9']})
pdt_scmn_up1 = _seg_pdt_scmn.add_line('up1', {'pdt': ['s1', 's2', 's4', 's5', 's6', 's7', 's8'], 'scmn': ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's10', 's11', 's12']})
pdt_scmn_mid1 = _seg_pdt_scmn.add_line('mid1', {'pdt': ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8'], 'scmn': ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9', 's10', 's11', 's12']})
pdt_scmn_mid2 = _seg_pdt_scmn.add_line('mid2', {'pdt': ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8'], 'scmn': ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9', 's10', 's11', 's12']})

blocksections_list = [
    pun_nwp_dn1, pun_nwp_up1,
    nwp_kbm_dn1, nwp_kbm_up1,
    kbm_tiu_dn1, kbm_tiu_up1,
    tiu_ulm_dn1, tiu_ulm_up1,
    ulm_che_dn1, ulm_che_up1,
    che_dusi_dn1, che_dusi_up1,
    dusi_pdu_dn1, dusi_pdu_up1,
    pdu_sgdm_dn1, pdu_sgdm_up1,
    sgdm_cpp_dn1, sgdm_cpp_up1,
    cpp_gvi_dn1, cpp_gvi_up1,
    gvi_nml_dn1, gvi_nml_up1,
    nml_vzm_dn1, nml_vzm_up1,
    vzm_kuk_dn1, vzm_kuk_up1, vzm_kuk_mid1,
    kuk_alm_dn1, kuk_alm_up1, kuk_alm_mid1,
    alm_kpl_dn1, alm_kpl_up1, alm_kpl_mid1,
    kpl_ktv_dn1, kpl_ktv_up1, kpl_ktv_mid1,
    ktv_pdt_dn1, ktv_pdt_up1, ktv_pdt_mid1, ktv_pdt_mid2,
    pdt_scmn_dn1, pdt_scmn_up1, pdt_scmn_mid1, pdt_scmn_mid2,
]

# populate_connections(blocksections_list, station_dict, stations_list)

