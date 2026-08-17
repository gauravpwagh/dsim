"""krpu_ktv board: stations + block sections. Merged from network/krpu_ktv_stations_data.py
and network/krpu_ktv_blocksections_data.py during the src/ package restructure."""
import pandas as pd

from iidsim.domain import create_station_class, block_sec, populate_connections
from iidsim.data.geography import station_longitudes as _station_longitudes_fn

station_longitudes = _station_longitudes_fn()


# Converted from krpu_ktv_stations.py (KRPU-KTV board).
# Connections left EMPTY; filled by populate_connections() from block-section conns.

station_dict = {
    'krpu' : {"tracks": {"s1": 1, "s2": 2, "s3": 3, "s4": 4, "s5": 5, "s6": 0, "s7": 0, "s8": 0}, "connections": {}},
    'suku' : {"tracks": {"s1": 1, "s2": 0, "s3": 0, "s4": 2}, "connections": {}},
    'pbv'  : {"tracks": {"s1": 1, "s2": 0, "s3": 2, "s4": 3}, "connections": {}},
    'mkrd' : {"tracks": {"s1": 1, "s2": 0, "s3": 0, "s4": 2}, "connections": {}},
    'bhja' : {"tracks": {"s1": 1, "s2": 0, "s3": 0, "s4": 2}, "connections": {}},
    'pfu'  : {"tracks": {"s1": 1, "s2": 0, "s3": 0, "s4": 2}, "connections": {}},
    'dpc'  : {"tracks": {"s1": 1, "s2": 0, "s3": 0, "s4": 2}, "connections": {}},
    'gpj'  : {"tracks": {"s1": 1, "s2": 0, "s3": 0, "s4": 2}, "connections": {}},
    'ark'  : {"tracks": {"s1": 1, "s2": 0, "s3": 0, "s4": 0, "s5": 0, "s6": 2}, "connections": {}},
    'smlg' : {"tracks": {"s1": 1, "s2": 0, "s3": 2}, "connections": {}},
    'kvls' : {"tracks": {"s1": 1, "s2": 0, "s3": 0}, "connections": {}},
    'bghu' : {"tracks": {"s1": 0, "s2": 0, "s3": 1}, "connections": {}},
    'cmdp' : {"tracks": {"s1": 0, "s2": 0, "s3": 1}, "connections": {}},
    'txd'  : {"tracks": {"s1": 1, "s2": 0}, "connections": {}},
    'slpm' : {"tracks": {"s1": 0, "s2": 0, "s3": 1}, "connections": {}},
    'bdvr' : {"tracks": {"s1": 1, "s2": 0, "s3": 2}, "connections": {}},
    'sup'  : {"tracks": {"s1": 0, "s2": 1, "s3": 2, "s4": 0, "s5": 0, "s6": 3}, "connections": {}},
    'lvk'  : {"tracks": {"s1": 0, "s2": 1, "s3": 0, "s4": 0, "s5": 2}, "connections": {}},
    'mvw'  : {"tracks": {"s1": 1, "s2": 2, "s3": 0, "s4": 0, "s5": 3}, "connections": {}},
}

# -- Station object instantiation (longitude from stations_longitude.py) --
krpu = create_station_class('krpu', station_longitudes['krpu'], station_dict['krpu'])
suku = create_station_class('suku', station_longitudes['suku'], station_dict['suku'])
pbv  = create_station_class('pbv', station_longitudes['pbv'], station_dict['pbv'])
mkrd = create_station_class('mkrd', station_longitudes['mkrd'], station_dict['mkrd'])
bhja = create_station_class('bhja', station_longitudes['bhja'], station_dict['bhja'])
pfu  = create_station_class('pfu', station_longitudes['pfu'], station_dict['pfu'])
dpc  = create_station_class('dpc', station_longitudes['dpc'], station_dict['dpc'])
gpj  = create_station_class('gpj', station_longitudes['gpj'], station_dict['gpj'])
ark  = create_station_class('ark', station_longitudes['ark'], station_dict['ark'])
smlg = create_station_class('smlg', station_longitudes['smlg'], station_dict['smlg'])
kvls = create_station_class('kvls', station_longitudes['kvls'], station_dict['kvls'])
bghu = create_station_class('bghu', station_longitudes['bghu'], station_dict['bghu'])
cmdp = create_station_class('cmdp', station_longitudes['cmdp'], station_dict['cmdp'])
txd  = create_station_class('txd', station_longitudes['txd'], station_dict['txd'])
slpm = create_station_class('slpm', station_longitudes['slpm'], station_dict['slpm'])
bdvr = create_station_class('bdvr', station_longitudes['bdvr'], station_dict['bdvr'])
sup  = create_station_class('sup', station_longitudes['sup'], station_dict['sup'])
lvk  = create_station_class('lvk', station_longitudes['lvk'], station_dict['lvk'])
mvw  = create_station_class('mvw', station_longitudes['mvw'], station_dict['mvw'])

stations_list = [krpu, suku, pbv, mkrd, bhja, pfu, dpc, gpj, ark, smlg, kvls, bghu, cmdp, txd, slpm, bdvr, sup, lvk, mvw]



# Converted from krpu_ktv_blocksections.py (old int dir 0/1/2 -> dn1/up1/mid1).
# Dropped: krpu_mvf, krpu_dmrt (branch stubs), mvw_ktv (inter-board link; ktv not in this board).


krpu_suku_mid1= block_sec('mid1', 'krpu', 'suku', 11.16, {'krpu': ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8'], 'suku': ['s1', 's2', 's3', 's4']}, stations_list)

suku_pbv_dn1  = block_sec('dn1', 'suku', 'pbv', 7.59, {'suku': ['s1', 's2', 's3', 's4'], 'pbv': ['s3', 's4']}, stations_list)
suku_pbv_up1  = block_sec('up1', 'suku', 'pbv', 7.59, {'suku': ['s1', 's2', 's3', 's4'], 'pbv': ['s1', 's2', 's3']}, stations_list)

# pbv_mkrd_mid1  = block_sec('mid1', 'pbv', 'mkrd', 12.57, {'pbv': ['s3', 's4'], 'mkrd': ['s3', 's4']}, stations_list) 
pbv_mkrd_dn1  = block_sec('dn1', 'pbv', 'mkrd', 12.57, {'pbv': ['s3', 's4'], 'mkrd': ['s3', 's4']}, stations_list)
pbv_mkrd_up1  = block_sec('up1', 'pbv', 'mkrd', 12.57, {'pbv': ['s1', 's2', 's3'], 'mkrd': ['s1', 's2']}, stations_list)
# pbv_mkrd_mid2  = block_sec('mid2', 'pbv', 'mkrd', 12.57, {'pbv': ['s1', 's2', 's3'], 'mkrd': ['s1', 's2']}, stations_list)

# mkrd_bhja_mid1 = block_sec('mid1', 'mkrd', 'bhja', 11.39, {'mkrd': ['s3', 's4'], 'bhja': ['s3', 's4']}, stations_list)
mkrd_bhja_dn1 = block_sec('dn1', 'mkrd', 'bhja', 11.39, {'mkrd': ['s3', 's4'], 'bhja': ['s3', 's4']}, stations_list)
mkrd_bhja_up1 = block_sec('up1', 'mkrd', 'bhja', 11.39, {'mkrd': ['s1', 's2'], 'bhja': ['s1', 's2', 's3']}, stations_list)
# mkrd_bhja_mid2 = block_sec('mid2', 'mkrd', 'bhja', 11.39, {'mkrd': ['s1', 's2'], 'bhja': ['s1', 's2', 's3']}, stations_list)


bhja_pfu_dn1  = block_sec('dn1', 'bhja', 'pfu', 10.03, {'bhja': ['s1', 's2','s3', 's4'], 'pfu': ['s1', 's2', 's3', 's4']}, stations_list) 
bhja_pfu_up1  = block_sec('up1', 'bhja', 'pfu', 10.03, {'bhja': ['s1', 's2','s3', 's4'], 'pfu': ['s1', 's2', 's3', 's4']}, stations_list)

pfu_dpc_dn1   = block_sec('dn1', 'pfu', 'dpc', 9.78, {'pfu': ['s1', 's2', 's3', 's4'], 'dpc': ['s1', 's3', 's4']}, stations_list)
pfu_dpc_up1   = block_sec('up1', 'pfu', 'dpc', 9.78, {'pfu': ['s1', 's2', 's3','s4'], 'dpc': ['s1', 's2', 's3']}, stations_list)

dpc_gpj_dn1   = block_sec('dn1', 'dpc', 'gpj', 12.65, {'dpc': ['s1', 's3', 's4'], 'gpj': ['s3', 's4']}, stations_list)
dpc_gpj_up1   = block_sec('up1', 'dpc', 'gpj', 12.65, {'dpc': ['s1', 's2'], 'gpj': ['s1', 's2', 's4']}, stations_list)

gpj_ark_dn1   = block_sec('dn1', 'gpj', 'ark', 9.9, {'gpj': ['s3', 's4'], 'ark': ['s5', 's6']}, stations_list)
gpj_ark_up1   = block_sec('up1', 'gpj', 'ark', 9.9, {'gpj': ['s1', 's2', 's4'], 'ark': ['s1', 's2', 's3', 's4', 's6']}, stations_list)

ark_smlg_dn1  = block_sec('dn1', 'ark', 'smlg', 11.72, {'ark': ['s5', 's6'], 'smlg': ['s1', 's2', 's3']}, stations_list)
ark_smlg_up1  = block_sec('up1', 'ark', 'smlg', 11.72, {'ark': ['s1', 's2', 's3', 's4', 's6'], 'smlg': ['s1', 's2', 's3']}, stations_list)

smlg_kvls_mid1= block_sec('mid1', 'smlg', 'kvls', 9.0, {'smlg': ['s1', 's2', 's3'], 'kvls': ['s1', 's2', 's3']}, stations_list)

kvls_bghu_mid1= block_sec('mid1', 'kvls', 'bghu', 11.25, {'kvls': ['s1', 's2', 's3'], 'bghu': ['s1', 's2', 's3']}, stations_list)

bghu_cmdp_mid1= block_sec('mid1', 'bghu', 'cmdp', 9.01, {'bghu': ['s1', 's2', 's3'], 'cmdp': ['s1', 's2', 's3']}, stations_list)

cmdp_txd_mid1 = block_sec('mid1', 'cmdp', 'txd', 11.89, {'cmdp': ['s1', 's2', 's3'], 'txd': ['s1', 's2']}, stations_list)

txd_slpm_mid1 = block_sec('mid1', 'txd', 'slpm', 6.64, {'txd': ['s1', 's2'], 'slpm': ['s1', 's2', 's3']}, stations_list)

slpm_bdvr_mid1= block_sec('mid1', 'slpm', 'bdvr', 12.08, {'slpm': ['s1', 's2', 's3'], 'bdvr': ['s1', 's2', 's3']}, stations_list)

bdvr_sup_dn1  = block_sec('dn1', 'bdvr', 'sup', 7.29, {'bdvr': ['s1','s2', 's3'], 'sup': ['s2', 's3', 's5', 's6']}, stations_list)
bdvr_sup_up1  = block_sec('up1', 'bdvr', 'sup', 7.29, {'bdvr': ['s1', 's2', 's3'], 'sup': ['s2', 's3', 's4']}, stations_list)

sup_lvk_dn1   = block_sec('dn1', 'sup', 'lvk', 9.61, {'sup': ['s2', 's3', 's5', 's6'], 'lvk': ['s3', 's4', 's5']}, stations_list)
sup_lvk_up1   = block_sec('up1', 'sup', 'lvk', 9.61, {'sup': ['s1', 's2', 's3', 's4'], 'lvk': ['s1', 's2', 's3']}, stations_list)

lvk_mvw_dn1   = block_sec('dn1', 'lvk', 'mvw', 7.42, {'lvk': ['s3', 's4', 's5'], 'mvw': ['s1', 's2', 's4', 's5']}, stations_list)
lvk_mvw_up1   = block_sec('up1', 'lvk', 'mvw', 7.42, {'lvk': ['s1', 's2', 's3'], 'mvw': ['s1', 's2', 's3']}, stations_list)

blocksections_list = [
    krpu_suku_mid1,
    suku_pbv_dn1, suku_pbv_up1,
   pbv_mkrd_dn1, pbv_mkrd_up1,
    mkrd_bhja_dn1, mkrd_bhja_up1,
    bhja_pfu_dn1, bhja_pfu_up1,
    pfu_dpc_dn1, pfu_dpc_up1,
    dpc_gpj_dn1, dpc_gpj_up1,
    gpj_ark_dn1, gpj_ark_up1,
    ark_smlg_dn1, ark_smlg_up1,
    smlg_kvls_mid1,
    kvls_bghu_mid1,
    bghu_cmdp_mid1,
    cmdp_txd_mid1,
    txd_slpm_mid1,
    slpm_bdvr_mid1,
    bdvr_sup_dn1, bdvr_sup_up1,
    sup_lvk_dn1, sup_lvk_up1,
    lvk_mvw_dn1, lvk_mvw_up1,
   
]

# populate_connections(blocksections_list, station_dict, stations_list)

