"""krpu_ktv board: stations + block sections. Merged from network/krpu_ktv_stations_data.py
and network/krpu_ktv_blocksections_data.py during the src/ package restructure."""
import pandas as pd

from iidsim.domain import create_station_class, populate_connections, Segment
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


_seg_krpu_suku = Segment.new('krpu', 'suku', 11.16, stations_list)
krpu_suku_mid1 = _seg_krpu_suku.add_line('mid1', {'krpu': ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8'], 'suku': ['s1', 's2', 's3', 's4']})

_seg_suku_pbv = Segment.new('suku', 'pbv', 7.59, stations_list)
suku_pbv_dn1 = _seg_suku_pbv.add_line('dn1', {'suku': ['s1', 's2', 's3', 's4'], 'pbv': ['s3', 's4']})
suku_pbv_up1 = _seg_suku_pbv.add_line('up1', {'suku': ['s1', 's2', 's3', 's4'], 'pbv': ['s1', 's2', 's3']})

# pbv_mkrd_mid1  = block_sec('mid1', 'pbv', 'mkrd', 12.57, {'pbv': ['s3', 's4'], 'mkrd': ['s3', 's4']}, stations_list) 
_seg_pbv_mkrd = Segment.new('pbv', 'mkrd', 12.57, stations_list)
pbv_mkrd_dn1 = _seg_pbv_mkrd.add_line('dn1', {'pbv': ['s3', 's4'], 'mkrd': ['s3', 's4']})
pbv_mkrd_up1 = _seg_pbv_mkrd.add_line('up1', {'pbv': ['s1', 's2', 's3'], 'mkrd': ['s1', 's2']})
# pbv_mkrd_mid2  = block_sec('mid2', 'pbv', 'mkrd', 12.57, {'pbv': ['s1', 's2', 's3'], 'mkrd': ['s1', 's2']}, stations_list)

# mkrd_bhja_mid1 = block_sec('mid1', 'mkrd', 'bhja', 11.39, {'mkrd': ['s3', 's4'], 'bhja': ['s3', 's4']}, stations_list)
_seg_mkrd_bhja = Segment.new('mkrd', 'bhja', 11.39, stations_list)
mkrd_bhja_dn1 = _seg_mkrd_bhja.add_line('dn1', {'mkrd': ['s3', 's4'], 'bhja': ['s3', 's4']})
mkrd_bhja_up1 = _seg_mkrd_bhja.add_line('up1', {'mkrd': ['s1', 's2'], 'bhja': ['s1', 's2', 's3']})
# mkrd_bhja_mid2 = block_sec('mid2', 'mkrd', 'bhja', 11.39, {'mkrd': ['s1', 's2'], 'bhja': ['s1', 's2', 's3']}, stations_list)


_seg_bhja_pfu = Segment.new('bhja', 'pfu', 10.03, stations_list)
bhja_pfu_dn1 = _seg_bhja_pfu.add_line('dn1', {'bhja': ['s1', 's2','s3', 's4'], 'pfu': ['s1', 's2', 's3', 's4']})
bhja_pfu_up1 = _seg_bhja_pfu.add_line('up1', {'bhja': ['s1', 's2','s3', 's4'], 'pfu': ['s1', 's2', 's3', 's4']})

_seg_pfu_dpc = Segment.new('pfu', 'dpc', 9.78, stations_list)
pfu_dpc_dn1 = _seg_pfu_dpc.add_line('dn1', {'pfu': ['s1', 's2', 's3', 's4'], 'dpc': ['s1', 's3', 's4']})
pfu_dpc_up1 = _seg_pfu_dpc.add_line('up1', {'pfu': ['s1', 's2', 's3','s4'], 'dpc': ['s1', 's2', 's3']})

_seg_dpc_gpj = Segment.new('dpc', 'gpj', 12.65, stations_list)
dpc_gpj_dn1 = _seg_dpc_gpj.add_line('dn1', {'dpc': ['s1', 's3', 's4'], 'gpj': ['s3', 's4']})
dpc_gpj_up1 = _seg_dpc_gpj.add_line('up1', {'dpc': ['s1', 's2'], 'gpj': ['s1', 's2', 's4']})

_seg_gpj_ark = Segment.new('gpj', 'ark', 9.9, stations_list)
gpj_ark_dn1 = _seg_gpj_ark.add_line('dn1', {'gpj': ['s3', 's4'], 'ark': ['s5', 's6']})
gpj_ark_up1 = _seg_gpj_ark.add_line('up1', {'gpj': ['s1', 's2', 's4'], 'ark': ['s1', 's2', 's3', 's4', 's6']})

_seg_ark_smlg = Segment.new('ark', 'smlg', 11.72, stations_list)
ark_smlg_dn1 = _seg_ark_smlg.add_line('dn1', {'ark': ['s5', 's6'], 'smlg': ['s1', 's2', 's3']})
ark_smlg_up1 = _seg_ark_smlg.add_line('up1', {'ark': ['s1', 's2', 's3', 's4', 's6'], 'smlg': ['s1', 's2', 's3']})

_seg_smlg_kvls = Segment.new('smlg', 'kvls', 9.0, stations_list)
smlg_kvls_mid1 = _seg_smlg_kvls.add_line('mid1', {'smlg': ['s1', 's2', 's3'], 'kvls': ['s1', 's2', 's3']})

_seg_kvls_bghu = Segment.new('kvls', 'bghu', 11.25, stations_list)
kvls_bghu_mid1 = _seg_kvls_bghu.add_line('mid1', {'kvls': ['s1', 's2', 's3'], 'bghu': ['s1', 's2', 's3']})

_seg_bghu_cmdp = Segment.new('bghu', 'cmdp', 9.01, stations_list)
bghu_cmdp_mid1 = _seg_bghu_cmdp.add_line('mid1', {'bghu': ['s1', 's2', 's3'], 'cmdp': ['s1', 's2', 's3']})

_seg_cmdp_txd = Segment.new('cmdp', 'txd', 11.89, stations_list)
cmdp_txd_mid1 = _seg_cmdp_txd.add_line('mid1', {'cmdp': ['s1', 's2', 's3'], 'txd': ['s1', 's2']})

_seg_txd_slpm = Segment.new('txd', 'slpm', 6.64, stations_list)
txd_slpm_mid1 = _seg_txd_slpm.add_line('mid1', {'txd': ['s1', 's2'], 'slpm': ['s1', 's2', 's3']})

_seg_slpm_bdvr = Segment.new('slpm', 'bdvr', 12.08, stations_list)
slpm_bdvr_mid1 = _seg_slpm_bdvr.add_line('mid1', {'slpm': ['s1', 's2', 's3'], 'bdvr': ['s1', 's2', 's3']})

_seg_bdvr_sup = Segment.new('bdvr', 'sup', 7.29, stations_list)
bdvr_sup_dn1 = _seg_bdvr_sup.add_line('dn1', {'bdvr': ['s1','s2', 's3'], 'sup': ['s2', 's3', 's5', 's6']})
bdvr_sup_up1 = _seg_bdvr_sup.add_line('up1', {'bdvr': ['s1', 's2', 's3'], 'sup': ['s2', 's3', 's4']})

_seg_sup_lvk = Segment.new('sup', 'lvk', 9.61, stations_list)
sup_lvk_dn1 = _seg_sup_lvk.add_line('dn1', {'sup': ['s2', 's3', 's5', 's6'], 'lvk': ['s3', 's4', 's5']})
sup_lvk_up1 = _seg_sup_lvk.add_line('up1', {'sup': ['s1', 's2', 's3', 's4'], 'lvk': ['s1', 's2', 's3']})

_seg_lvk_mvw = Segment.new('lvk', 'mvw', 7.42, stations_list)
lvk_mvw_dn1 = _seg_lvk_mvw.add_line('dn1', {'lvk': ['s3', 's4', 's5'], 'mvw': ['s1', 's2', 's4', 's5']})
lvk_mvw_up1 = _seg_lvk_mvw.add_line('up1', {'lvk': ['s1', 's2', 's3'], 'mvw': ['s1', 's2', 's3']})

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

