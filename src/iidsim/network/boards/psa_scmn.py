"""psa_scmn board: stations + block sections. Merged from network/psa_scmn_stations_data.py
and network/psa_scmn_blocksections_data.py during the src/ package restructure."""
import pandas as pd

from iidsim.domain import create_station_class, block_sec, populate_connections
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


pun_nwp_dn1   = block_sec('dn1', 'pun', 'nwp', 13.24, {'pun': ['s1', 's2'], 'nwp': ['s2', 's3']}, stations_list)
pun_nwp_up1   = block_sec('up1', 'pun', 'nwp', 13.24, {'pun': ['s1', 's3', 's4'], 'nwp': ['s2', 's4', 's5']}, stations_list)

nwp_kbm_dn1   = block_sec('dn1', 'nwp', 'kbm', 13.92, {'nwp': ['s2', 's3'], 'kbm': ['s1', 's2']}, stations_list)
nwp_kbm_up1   = block_sec('up1', 'nwp', 'kbm', 13.92, {'nwp': ['s2', 's4', 's5'], 'kbm': ['s1', 's3', 's4']}, stations_list)

kbm_tiu_dn1   = block_sec('dn1', 'kbm', 'tiu', 13.72, {'kbm': ['s1', 's2'], 'tiu': ['s1', 's2']}, stations_list)
kbm_tiu_up1   = block_sec('up1', 'kbm', 'tiu', 13.72, {'kbm': ['s1', 's3', 's4'], 'tiu': ['s1', 's3', 's4']}, stations_list)

tiu_ulm_dn1   = block_sec('dn1', 'tiu', 'ulm', 9.63, {'tiu': ['s1', 's2'], 'ulm': ['s1', 's2']}, stations_list)
tiu_ulm_up1   = block_sec('up1', 'tiu', 'ulm', 9.63, {'tiu': ['s1', 's3', 's4'], 'ulm': ['s1', 's3', 's4']}, stations_list)

ulm_che_dn1   = block_sec('dn1', 'ulm', 'che', 10.04, {'ulm': ['s1', 's2'], 'che': ['s1', 's2', 's4', 's5']}, stations_list)
ulm_che_up1   = block_sec('up1', 'ulm', 'che', 10.04, {'ulm': ['s1', 's3', 's4'], 'che': ['s3', 's4', 's5']}, stations_list)

che_dusi_dn1  = block_sec('dn1', 'che', 'dusi', 6.46, {'che': ['s1', 's2', 's4', 's5'], 'dusi': ['s1', 's2']}, stations_list)
che_dusi_up1  = block_sec('up1', 'che', 'dusi', 6.46, {'che': ['s3', 's4', 's5'], 'dusi': ['s3', 's4']}, stations_list)

dusi_pdu_dn1  = block_sec('dn1', 'dusi', 'pdu', 8.82, {'dusi': ['s1', 's2'], 'pdu': ['s1', 's2', 's3']}, stations_list)
dusi_pdu_up1  = block_sec('up1', 'dusi', 'pdu', 8.82, {'dusi': ['s3', 's4'], 'pdu': ['s1', 's2', 's4']}, stations_list)

pdu_sgdm_dn1  = block_sec('dn1', 'pdu', 'sgdm', 10.07, {'pdu': ['s1', 's2', 's3'], 'sgdm': ['s1', 's2', 's3']}, stations_list)
pdu_sgdm_up1  = block_sec('up1', 'pdu', 'sgdm', 10.07, {'pdu': ['s1', 's2', 's4'], 'sgdm': ['s3', 's4']}, stations_list)

sgdm_cpp_dn1  = block_sec('dn1', 'sgdm', 'cpp', 13.27, {'sgdm': ['s1', 's2', 's3'], 'cpp': ['s1', 's2', 's4']}, stations_list)
sgdm_cpp_up1  = block_sec('up1', 'sgdm', 'cpp', 13.27, {'sgdm': ['s3', 's4'], 'cpp': ['s2', 's3', 's4', 's5']}, stations_list)

cpp_gvi_dn1   = block_sec('dn1', 'cpp', 'gvi', 6.57, {'cpp': ['s1', 's2', 's4'], 'gvi': ['s1', 's2', 's4']}, stations_list)
cpp_gvi_up1   = block_sec('up1', 'cpp', 'gvi', 6.57, {'cpp': ['s3', 's4', 's5'], 'gvi': ['s3', 's4']}, stations_list)

gvi_nml_dn1   = block_sec('dn1', 'gvi', 'nml', 12.33, {'gvi': ['s1', 's2', 's4'], 'nml': ['s1', 's3']}, stations_list)
gvi_nml_up1   = block_sec('up1', 'gvi', 'nml', 12.33, {'gvi': ['s3', 's4'], 'nml': ['s2', 's3']}, stations_list)

nml_vzm_dn1   = block_sec('dn1', 'nml', 'vzm', 11.74, {'nml': ['s1', 's3'], 'vzm': ['s1', 's2', 's3', 's4', 's5', 's6', 's8', 's9']}, stations_list)
nml_vzm_up1   = block_sec('up1', 'nml', 'vzm', 11.74, {'nml': ['s2', 's3'], 'vzm': ['s1', 's2', 's3', 's4', 's5', 's7', 's8', 's9']}, stations_list)

vzm_kuk_dn1   = block_sec('dn1', 'vzm', 'kuk', 10.65, {'vzm': ['s1', 's2', 's3', 's4', 's5', 's6', 's8', 's9'], 'kuk': ['s1', 's2', 's3']}, stations_list)
vzm_kuk_up1   = block_sec('up1', 'vzm', 'kuk', 10.65, {'vzm': ['s1', 's2', 's3', 's4', 's5', 's7', 's8', 's9'], 'kuk': ['s2', 's3', 's4', 's5']}, stations_list)
vzm_kuk_mid1  = block_sec('mid1', 'vzm', 'kuk', 10.65, {'vzm': ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9'], 'kuk': ['s2', 's3']}, stations_list)

kuk_alm_dn1   = block_sec('dn1', 'kuk', 'alm', 7.11, {'kuk': ['s1', 's2', 's3'], 'alm': ['s1', 's2', 's3', 's5']}, stations_list)
kuk_alm_up1   = block_sec('up1', 'kuk', 'alm', 7.11, {'kuk': ['s2', 's3', 's4', 's5'], 'alm': ['s3', 's4', 's5']}, stations_list)
kuk_alm_mid1  = block_sec('mid1', 'kuk', 'alm', 7.11, {'kuk': ['s2', 's3', 's4', 's5'], 'alm': ['s2', 's3', 's4', 's5']}, stations_list)

alm_kpl_dn1   = block_sec('dn1', 'alm', 'kpl', 9.23, {'alm': ['s1', 's2', 's3', 's5'], 'kpl': ['s1', 's2', 's3', 's5', 's6']}, stations_list)
alm_kpl_up1   = block_sec('up1', 'alm', 'kpl', 9.23, {'alm': ['s3', 's4', 's5'], 'kpl': ['s3', 's4', 's5', 's6']}, stations_list)
alm_kpl_mid1  = block_sec('mid1', 'alm', 'kpl', 9.23, {'alm': ['s2', 's3', 's4', 's5', 's6'], 'kpl': ['s2', 's3', 's4', 's5', 's6']}, stations_list)

kpl_ktv_dn1   = block_sec('dn1', 'kpl', 'ktv', 7.74, {'kpl': ['s1', 's2', 's3', 's5', 's6'], 'ktv': ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9']}, stations_list)
kpl_ktv_up1   = block_sec('up1', 'kpl', 'ktv', 7.74, {'kpl': ['s3', 's4', 's5', 's6'], 'ktv': ['s1', 's2', 's3', 's6', 's7', 's8', 's9']}, stations_list)
kpl_ktv_mid1  = block_sec('mid1', 'kpl', 'ktv', 7.74, {'kpl': ['s1', 's2', 's3', 's4', 's5', 's6'], 'ktv': ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9']}, stations_list)

ktv_pdt_dn1   = block_sec('dn1', 'ktv', 'pdt', 8.92, {'ktv': ['s1', 's2', 's4', 's5', 's6', 's7', 's9'], 'pdt': ['s1', 's2', 's3', 's4', 's5', 's6', 's8']}, stations_list)
ktv_pdt_up1   = block_sec('up1', 'ktv', 'pdt', 8.92, {'ktv': ['s1', 's2', 's6', 's7', 's8', 's9'], 'pdt': ['s1', 's2', 's4', 's5', 's6', 's7', 's8']}, stations_list)
ktv_pdt_mid1  = block_sec('mid1', 'ktv', 'pdt', 8.92, {'ktv': ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9'], 'pdt': ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8']}, stations_list)
ktv_pdt_mid2  = block_sec('mid2', 'ktv', 'pdt', 8.92, {'ktv': ['s1', 's2', 's4', 's5', 's6', 's7', 's8', 's9'], 'pdt': ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8']}, stations_list)

pdt_scmn_dn1  = block_sec('dn1', 'pdt', 'scmn', 7.9, {'pdt': ['s1', 's2', 's3', 's4', 's5', 's6', 's8'], 'scmn': ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9']}, stations_list)
pdt_scmn_up1  = block_sec('up1', 'pdt', 'scmn', 7.9, {'pdt': ['s1', 's2', 's4', 's5', 's6', 's7', 's8'], 'scmn': ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's10', 's11', 's12']}, stations_list)
pdt_scmn_mid1 = block_sec('mid1', 'pdt', 'scmn', 7.9, {'pdt': ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8'], 'scmn': ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9', 's10', 's11', 's12']}, stations_list)
pdt_scmn_mid2 = block_sec('mid2', 'pdt', 'scmn', 7.9, {'pdt': ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8'], 'scmn': ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9', 's10', 's11', 's12']}, stations_list)

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

