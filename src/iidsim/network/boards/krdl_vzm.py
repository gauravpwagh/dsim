"""krdl_vzm board: stations + block sections. Merged from network/krdl_vzm_stations_data.py
and network/krdl_vzm_blocksections_data.py during the src/ package restructure."""
import pandas as pd

from iidsim.domain import create_station_class, populate_connections, Segment
from iidsim.data.geography import station_longitudes as _station_longitudes_fn

station_longitudes = _station_longitudes_fn()


# Converted from krdl_vzm_stations.py (KRDL-VZM board, 55 stations).
# Connections left EMPTY; filled by populate_connections() from block-section conns.

station_dict = {
    'krdl' : {"tracks": {"s1": 1, "s2": 0, "s3": 2, "s4": 0, "s5": 0, "s6": 0, "s7": 0, "s8": 0, "s9": 0, "s10": 0, "s11": 0, "s12": 0, "s13": 0, "s14": 0, "s15": 0}, "connections": {}},
    'bchl' : {"tracks": {"s1": 1, "s2": 0, "s3": 0, "s4": 0}, "connections": {}},
    'bhns' : {"tracks": {"s1": 1, "s2": 0, "s3": 0}, "connections": {}},
    'kmlr' : {"tracks": {"s1": 1, "s2": 0, "s3": 0}, "connections": {}},
    'dwz'  : {"tracks": {"s1": 1, "s2": 0, "s3": 0, "s4": 2, "s5": 0}, "connections": {}},
    'giz'  : {"tracks": {"s1": 1, "s2": 0, "s3": 0, "s4": 2}, "connections": {}},
    'dbf'  : {"tracks": {"s1": 1, "s2": 0, "s3": 0, "s4": 2}, "connections": {}},
    'kwgn' : {"tracks": {"s1": 1, "s2": 0, "s3": 0, "s4": 2}, "connections": {}},
    'kklu' : {"tracks": {"s1": 1, "s2": 0, "s3": 0, "s4": 2}, "connections": {}},
    'kmsd' : {"tracks": {"s1": 1, "s2": 0, "s3": 0, "s4": 2}, "connections": {}},
    'szy'  : {"tracks": {"s1": 1, "s2": 0, "s3": 2, "s4": 3}, "connections": {}},
    'dmk'  : {"tracks": {"s1": 1, "s2": 0, "s3": 0, "s4": 2}, "connections": {}},
    'bdxx' : {"tracks": {"s1": 1, "s2": 2, "s3": 0, "s4": 0, "s5": 3}, "connections": {}},
    'tpq'  : {"tracks": {"s1": 1, "s2": 0, "s3": 0, "s4": 2}, "connections": {}},
    'kmez' : {"tracks": {"s1": 1, "s2": 0, "s3": 0, "s4": 2}, "connections": {}},
    'jdb'  : {"tracks": {"s1": 1, "s2": 0, "s3": 0, "s4": 2, "s5": 3, "s6": 4}, "connections": {}},
    'nkx'  : {"tracks": {"s1": 1, "s2": 0, "s3": 0, "s4": 2}, "connections": {}},
    'agz'  : {"tracks": {"s1": 1, "s2": 0, "s3": 0, "s4": 2}, "connections": {}},
    'agb'  : {"tracks": {"s1": 1, "s2": 0, "s3": 0, "s4": 2}, "connections": {}},
    'kprr' : {"tracks": {"s1": 1, "s2": 0, "s3": 0, "s4": 2}, "connections": {}},
    'cjs'  : {"tracks": {"s1": 1, "s2": 0, "s3": 0, "s4": 2}, "connections": {}},
    'kdpa' : {"tracks": {"s1": 1, "s2": 0, "s3": 0, "s4": 2}, "connections": {}},
    'dir'  : {"tracks": {"s1": 1, "s2": 0, "s3": 0, "s4": 2}, "connections": {}},
    'jyp'  : {"tracks": {"s1": 1, "s2": 0, "s3": 0, "s4": 2, "s5": 3}, "connections": {}},
    'cts'  : {"tracks": {"s1": 0, "s2": 0, "s3": 1, "s4": 2}, "connections": {}},
    'mvg'  : {"tracks": {"s1": 0, "s2": 0, "s3": 1}, "connections": {}},
    'jrt'  : {"tracks": {"s1": 0, "s2": 0, "s3": 1}, "connections": {}},
    'mvf'  : {"tracks": {"s1": 1, "s2": 0, "s3": 0, "s4": 2}, "connections": {}},
    'krpu' : {"tracks": {"s1": 1, "s2": 2, "s3": 3, "s4": 4, "s5": 5, "s6": 0, "s7": 0, "s8": 0}, "connections": {}},
    'dmrt' : {"tracks": {"s1": 1, "s2": 0, "s3": 0, "s4": 2, "s5": 3}, "connections": {}},
    'dmnj' : {"tracks": {"s1": 1, "s2": 0, "s3": 0, "s4": 2, "s5": 0, "s6": 0, "s7": 0, "s8": 0, "s9": 0, "s10": 0}, "connections": {}},
    'bgua' : {"tracks": {"s1": 1, "s2": 2, "s3": 0, "s4": 3}, "connections": {}},
    'kkgm' : {"tracks": {"s1": 0, "s2": 0, "s3": 0, "s4": 1}, "connections": {}},
    'lkmr' : {"tracks": {"s1": 1, "s2": 0, "s3": 0, "s4": 2}, "connections": {}},
    'sgrm' : {"tracks": {"s1": 1, "s2": 0, "s3": 2, "s4": 3}, "connections": {}},
    'tkri' : {"tracks": {"s1": 1, "s2": 2, "s3": 3, "s4": 0, "s5": 0, "s6": 4}, "connections": {}},
    'rul'  : {"tracks": {"s1": 0, "s2": 0, "s3": 1}, "connections": {}},
    'llgm' : {"tracks": {"s1": 0, "s2": 0, "s3": 1}, "connections": {}},
    'blmk' : {"tracks": {"s1": 1, "s2": 0, "s3": 2}, "connections": {}},
    'skpi' : {"tracks": {"s1": 1, "s2": 0, "s3": 0}, "connections": {}},
    'ktga' : {"tracks": {"s1": 1, "s2": 0, "s3": 0, "s4": 0}, "connections": {}},
    'sprd' : {"tracks": {"s1": 1, "s2": 2, "s3": 0, "s4": 0, "s5": 3}, "connections": {}},
    'rgda' : {"tracks": {"s1": 0, "s2": 0, "s3": 0, "s4": 0, "s5": 1, "s6": 2, "s7": 3, "s8": 4, "s9": 5}, "connections": {}},
    'ldx'  : {"tracks": {"s1": 1, "s2": 0, "s3": 0, "s4": 2}, "connections": {}},
    'jmpt' : {"tracks": {"s1": 1, "s2": 0, "s3": 0, "s4": 2, "s5": 3, "s6": 4}, "connections": {}},
    'knrt' : {"tracks": {"s1": 1, "s2": 0, "s3": 0, "s4": 2, "s5": 3, "s6": 4}, "connections": {}},
    'gmda' : {"tracks": {"s1": 1, "s2": 0, "s3": 0, "s4": 2, "s5": 3, "s6": 4}, "connections": {}},
    'pvp'  : {"tracks": {"s1": 1, "s2": 2, "s3": 0, "s4": 3, "s5": 4, "s6": 5}, "connections": {}},
    'snm'  : {"tracks": {"s1": 1, "s2": 0, "s3": 0, "s4": 2, "s5": 0}, "connections": {}},
    'vbl'  : {"tracks": {"s1": 1, "s2": 0, "s3": 0, "s4": 2, "s5": 0}, "connections": {}},
    'dnv'  : {"tracks": {"s1": 1, "s2": 2, "s3": 0, "s4": 3, "s5": 0}, "connections": {}},
    'kmx'  : {"tracks": {"s1": 0, "s2": 1, "s3": 2, "s4": 0, "s5": 3, "s6": 4, "s7": 5}, "connections": {}},
    'gpi'  : {"tracks": {"s1": 1, "s2": 0, "s3": 0, "s4": 2}, "connections": {}},
    'grbl' : {"tracks": {"s1": 0, "s2": 1, "s3": 2, "s4": 0, "s5": 3}, "connections": {}},
    'gtlm' : {"tracks": {"s1": 1, "s2": 2, "s3": 0, "s4": 3}, "connections": {}},
}

# -- Station object instantiation (longitude from stations_longitude.py) --
krdl = create_station_class('krdl', station_longitudes['krdl'], station_dict['krdl'])
bchl = create_station_class('bchl', station_longitudes['bchl'], station_dict['bchl'])
bhns = create_station_class('bhns', station_longitudes['bhns'], station_dict['bhns'])
kmlr = create_station_class('kmlr', station_longitudes['kmlr'], station_dict['kmlr'])
dwz  = create_station_class('dwz', station_longitudes['dwz'], station_dict['dwz'])
giz  = create_station_class('giz', station_longitudes['giz'], station_dict['giz'])
dbf  = create_station_class('dbf', station_longitudes['dbf'], station_dict['dbf'])
kwgn = create_station_class('kwgn', station_longitudes['kwgn'], station_dict['kwgn'])
kklu = create_station_class('kklu', station_longitudes['kklu'], station_dict['kklu'])
kmsd = create_station_class('kmsd', station_longitudes['kmsd'], station_dict['kmsd'])
szy  = create_station_class('szy', station_longitudes['szy'], station_dict['szy'])
dmk  = create_station_class('dmk', station_longitudes['dmk'], station_dict['dmk'])
bdxx = create_station_class('bdxx', station_longitudes['bdxx'], station_dict['bdxx'])
tpq  = create_station_class('tpq', station_longitudes['tpq'], station_dict['tpq'])
kmez = create_station_class('kmez', station_longitudes['kmez'], station_dict['kmez'])
jdb  = create_station_class('jdb', station_longitudes['jdb'], station_dict['jdb'])
nkx  = create_station_class('nkx', station_longitudes['nkx'], station_dict['nkx'])
agz  = create_station_class('agz', station_longitudes['agz'], station_dict['agz'])
agb  = create_station_class('agb', station_longitudes['agb'], station_dict['agb'])
kprr = create_station_class('kprr', station_longitudes['kprr'], station_dict['kprr'])
cjs  = create_station_class('cjs', station_longitudes['cjs'], station_dict['cjs'])
kdpa = create_station_class('kdpa', station_longitudes['kdpa'], station_dict['kdpa'])
dir  = create_station_class('dir', station_longitudes['dir'], station_dict['dir'])
jyp  = create_station_class('jyp', station_longitudes['jyp'], station_dict['jyp'])
cts  = create_station_class('cts', station_longitudes['cts'], station_dict['cts'])
mvg  = create_station_class('mvg', station_longitudes['mvg'], station_dict['mvg'])
jrt  = create_station_class('jrt', station_longitudes['jrt'], station_dict['jrt'])
mvf  = create_station_class('mvf', station_longitudes['mvf'], station_dict['mvf'])
krpu = create_station_class('krpu', station_longitudes['krpu'], station_dict['krpu'])
dmrt = create_station_class('dmrt', station_longitudes['dmrt'], station_dict['dmrt'])
dmnj = create_station_class('dmnj', station_longitudes['dmnj'], station_dict['dmnj'])
bgua = create_station_class('bgua', station_longitudes['bgua'], station_dict['bgua'])
kkgm = create_station_class('kkgm', station_longitudes['kkgm'], station_dict['kkgm'])
lkmr = create_station_class('lkmr', station_longitudes['lkmr'], station_dict['lkmr'])
sgrm = create_station_class('sgrm', station_longitudes['sgrm'], station_dict['sgrm'])
tkri = create_station_class('tkri', station_longitudes['tkri'], station_dict['tkri'])
rul  = create_station_class('rul', station_longitudes['rul'], station_dict['rul'])
llgm = create_station_class('llgm', station_longitudes['llgm'], station_dict['llgm'])
blmk = create_station_class('blmk', station_longitudes['blmk'], station_dict['blmk'])
skpi = create_station_class('skpi', station_longitudes['skpi'], station_dict['skpi'])
ktga = create_station_class('ktga', station_longitudes['ktga'], station_dict['ktga'])
sprd = create_station_class('sprd', station_longitudes['sprd'], station_dict['sprd'])
rgda = create_station_class('rgda', station_longitudes['rgda'], station_dict['rgda'])
ldx  = create_station_class('ldx', station_longitudes['ldx'], station_dict['ldx'])
jmpt = create_station_class('jmpt', station_longitudes['jmpt'], station_dict['jmpt'])
knrt = create_station_class('knrt', station_longitudes['knrt'], station_dict['knrt'])
gmda = create_station_class('gmda', station_longitudes['gmda'], station_dict['gmda'])
pvp  = create_station_class('pvp', station_longitudes['pvp'], station_dict['pvp'])
snm  = create_station_class('snm', station_longitudes['snm'], station_dict['snm'])
vbl  = create_station_class('vbl', station_longitudes['vbl'], station_dict['vbl'])
dnv  = create_station_class('dnv', station_longitudes['dnv'], station_dict['dnv'])
kmx  = create_station_class('kmx', station_longitudes['kmx'], station_dict['kmx'])
gpi  = create_station_class('gpi', station_longitudes['gpi'], station_dict['gpi'])
grbl = create_station_class('grbl', station_longitudes['grbl'], station_dict['grbl'])
gtlm = create_station_class('gtlm', station_longitudes['gtlm'], station_dict['gtlm'])

stations_list = [
    krdl, bchl, bhns, kmlr, dwz, giz, dbf, kwgn, kklu, kmsd,
    szy, dmk, bdxx, tpq, kmez, jdb, nkx, agz, agb, kprr,
    cjs, kdpa, dir, jyp, cts, mvg, jrt, mvf, krpu, dmrt,
    dmnj, bgua, kkgm, lkmr, sgrm, tkri, rul, llgm, blmk, skpi,
    ktga, sprd, rgda, ldx, jmpt, knrt, gmda, pvp, snm, vbl,
    dnv, kmx, gpi, grbl, gtlm,
]



# Converted from krdl_vzm_blocksections.py (old int dir 0/1/2 -> dn1/up1/mid1).
# Dropped: gtlm_vzm (link to VZM board), krpu_suku (link to KRPU board), vbl_salr (branch stub).


segments_by_pair = {}
_seg_krdl_bchl = Segment.new('krdl', 'bchl', 9.14, stations_list)
segments_by_pair[_seg_krdl_bchl.name] = _seg_krdl_bchl
krdl_bchl_dn1 = _seg_krdl_bchl.add_line('dn1', {'krdl': ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9', 's10', 's11', 's12', 's13', 's14', 's15'], 'bchl': ['s1', 's2','s3', 's4']})
krdl_bchl_up1 = _seg_krdl_bchl.add_line('up1', {'krdl': ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9', 's10', 's11', 's12', 's13', 's14', 's15'], 'bchl': ['s1', 's2','s3', 's4']})

_seg_bchl_bhns = Segment.new('bchl', 'bhns', 9.55, stations_list)
segments_by_pair[_seg_bchl_bhns.name] = _seg_bchl_bhns
bchl_bhns_mid1 = _seg_bchl_bhns.add_line('mid1', {'bchl': ['s1', 's2', 's3', 's4'], 'bhns': ['s1', 's2', 's3']})

_seg_bhns_kmlr = Segment.new('bhns', 'kmlr', 12.43, stations_list)
segments_by_pair[_seg_bhns_kmlr.name] = _seg_bhns_kmlr
bhns_kmlr_mid1 = _seg_bhns_kmlr.add_line('mid1', {'bhns': ['s1', 's2', 's3'], 'kmlr': ['s1', 's2', 's3']})

_seg_kmlr_dwz = Segment.new('kmlr', 'dwz', 12.35, stations_list)
segments_by_pair[_seg_kmlr_dwz.name] = _seg_kmlr_dwz
kmlr_dwz_dn1 = _seg_kmlr_dwz.add_line('dn1', {'kmlr': ['s1', 's2', 's3'], 'dwz': ['s3', 's4', 's5']})
kmlr_dwz_up1 = _seg_kmlr_dwz.add_line('up1', {'kmlr': ['s1', 's2', 's3'], 'dwz': ['s1', 's2', 's4', 's5']})

_seg_dwz_giz = Segment.new('dwz', 'giz', 7.32, stations_list)
segments_by_pair[_seg_dwz_giz.name] = _seg_dwz_giz
dwz_giz_dn1 = _seg_dwz_giz.add_line('dn1', {'dwz': ['s3', 's4', 's5'], 'giz': ['s1', 's3', 's4']})
dwz_giz_up1 = _seg_dwz_giz.add_line('up1', {'dwz': ['s1', 's2', 's4', 's5'], 'giz': ['s1', 's2']})

_seg_giz_dbf = Segment.new('giz', 'dbf', 10.99, stations_list)
segments_by_pair[_seg_giz_dbf.name] = _seg_giz_dbf
giz_dbf_dn1 = _seg_giz_dbf.add_line('dn1', {'giz': ['s1', 's3', 's4'], 'dbf': ['s1', 's3', 's4']})
giz_dbf_up1 = _seg_giz_dbf.add_line('up1', {'giz': ['s1', 's2'], 'dbf': ['s1', 's2']})

_seg_dbf_kwgn = Segment.new('dbf', 'kwgn', 8.99, stations_list)
segments_by_pair[_seg_dbf_kwgn.name] = _seg_dbf_kwgn
dbf_kwgn_dn1 = _seg_dbf_kwgn.add_line('dn1', {'dbf': ['s1', 's3', 's4'], 'kwgn': ['s1', 's3', 's4']})
dbf_kwgn_up1 = _seg_dbf_kwgn.add_line('up1', {'dbf': ['s1', 's2'], 'kwgn': ['s1', 's2']})

_seg_kwgn_kklu = Segment.new('kwgn', 'kklu', 12.13, stations_list)
segments_by_pair[_seg_kwgn_kklu.name] = _seg_kwgn_kklu
kwgn_kklu_dn1 = _seg_kwgn_kklu.add_line('dn1', {'kwgn': ['s1', 's3', 's4'], 'kklu': ['s3', 's4']})
kwgn_kklu_up1 = _seg_kwgn_kklu.add_line('up1', {'kwgn': ['s1', 's2'], 'kklu': ['s1', 's2']})

_seg_kklu_kmsd = Segment.new('kklu', 'kmsd', 12.04, stations_list)
segments_by_pair[_seg_kklu_kmsd.name] = _seg_kklu_kmsd
kklu_kmsd_dn1 = _seg_kklu_kmsd.add_line('dn1', {'kklu': ['s3', 's4'], 'kmsd': ['s1', 's3', 's4']})
kklu_kmsd_up1 = _seg_kklu_kmsd.add_line('up1', {'kklu': ['s1', 's2'], 'kmsd': ['s1', 's2']})

_seg_kmsd_szy = Segment.new('kmsd', 'szy', 9.39, stations_list)
segments_by_pair[_seg_kmsd_szy.name] = _seg_kmsd_szy
kmsd_szy_dn1 = _seg_kmsd_szy.add_line('dn1', {'kmsd': ['s1', 's3', 's4'], 'szy': ['s3', 's4']})
kmsd_szy_up1 = _seg_kmsd_szy.add_line('up1', {'kmsd': ['s1', 's2'], 'szy': ['s1', 's2', 's3']})

_seg_szy_dmk = Segment.new('szy', 'dmk', 11.27, stations_list)
segments_by_pair[_seg_szy_dmk.name] = _seg_szy_dmk
szy_dmk_dn1 = _seg_szy_dmk.add_line('dn1', {'szy': ['s3', 's4'], 'dmk': ['s3', 's4']})
szy_dmk_up1 = _seg_szy_dmk.add_line('up1', {'szy': ['s1', 's2', 's3'], 'dmk': ['s1', 's2']})

_seg_dmk_bdxx = Segment.new('dmk', 'bdxx', 11.4, stations_list)
segments_by_pair[_seg_dmk_bdxx.name] = _seg_dmk_bdxx
dmk_bdxx_dn1 = _seg_dmk_bdxx.add_line('dn1', {'dmk': ['s3', 's4'], 'bdxx': ['s1', 's2', 's4', 's5']})
dmk_bdxx_up1 = _seg_dmk_bdxx.add_line('up1', {'dmk': ['s1', 's2'], 'bdxx': ['s1', 's2', 's3']})

_seg_bdxx_tpq = Segment.new('bdxx', 'tpq', 5.61, stations_list)
segments_by_pair[_seg_bdxx_tpq.name] = _seg_bdxx_tpq
bdxx_tpq_dn1 = _seg_bdxx_tpq.add_line('dn1', {'bdxx': ['s1', 's2', 's4', 's5'], 'tpq': ['s3', 's4']})
bdxx_tpq_up1 = _seg_bdxx_tpq.add_line('up1', {'bdxx': ['s1', 's2', 's3'], 'tpq': ['s1', 's2', 's4']})

_seg_tpq_kmez = Segment.new('tpq', 'kmez', 8.3, stations_list)
segments_by_pair[_seg_tpq_kmez.name] = _seg_tpq_kmez
tpq_kmez_dn1 = _seg_tpq_kmez.add_line('dn1', {'tpq': ['s3', 's4'], 'kmez': ['s3', 's4']})
tpq_kmez_up1 = _seg_tpq_kmez.add_line('up1', {'tpq': ['s1', 's2', 's4'], 'kmez': ['s1', 's2', 's4']})

_seg_kmez_jdb = Segment.new('kmez', 'jdb', 8.91, stations_list)
segments_by_pair[_seg_kmez_jdb.name] = _seg_kmez_jdb
kmez_jdb_dn1 = _seg_kmez_jdb.add_line('dn1', {'kmez': ['s3', 's4'], 'jdb': ['s1', 's2', 's3', 's4', 's5', 's6']})
kmez_jdb_up1 = _seg_kmez_jdb.add_line('up1', {'kmez': ['s1', 's2', 's4'], 'jdb': ['s1', 's2', 's3', 's4', 's5', 's6']})

_seg_jdb_nkx = Segment.new('jdb', 'nkx', 6.45, stations_list)
segments_by_pair[_seg_jdb_nkx.name] = _seg_jdb_nkx
jdb_nkx_dn1 = _seg_jdb_nkx.add_line('dn1', {'jdb': ['s1', 's2', 's3', 's4', 's5', 's6'], 'nkx': ['s3', 's4']})
jdb_nkx_up1 = _seg_jdb_nkx.add_line('up1', {'jdb': ['s1', 's2', 's3', 's4', 's5', 's6'], 'nkx': ['s1', 's2', 's4']})

_seg_nkx_agz = Segment.new('nkx', 'agz', 7.9, stations_list)
segments_by_pair[_seg_nkx_agz.name] = _seg_nkx_agz
nkx_agz_dn1 = _seg_nkx_agz.add_line('dn1', {'nkx': ['s3', 's4'], 'agz': ['s1', 's3', 's4']})
nkx_agz_up1 = _seg_nkx_agz.add_line('up1', {'nkx': ['s1', 's2', 's4'], 'agz': ['s1', 's2']})

_seg_agz_agb = Segment.new('agz', 'agb', 10.03, stations_list)
segments_by_pair[_seg_agz_agb.name] = _seg_agz_agb
agz_agb_dn1 = _seg_agz_agb.add_line('dn1', {'agz': ['s1', 's3', 's4'], 'agb': ['s1', 's3', 's4']})
agz_agb_up1 = _seg_agz_agb.add_line('up1', {'agz': ['s1', 's2'], 'agb': ['s1', 's2']})

_seg_agb_kprr = Segment.new('agb', 'kprr', 7.6, stations_list)
segments_by_pair[_seg_agb_kprr.name] = _seg_agb_kprr
agb_kprr_dn1 = _seg_agb_kprr.add_line('dn1', {'agb': ['s1', 's3', 's4'], 'kprr': ['s3', 's4']})
agb_kprr_up1 = _seg_agb_kprr.add_line('up1', {'agb': ['s1', 's2'], 'kprr': ['s1', 's2', 's4']})

_seg_kprr_cjs = Segment.new('kprr', 'cjs', 11.71, stations_list)
segments_by_pair[_seg_kprr_cjs.name] = _seg_kprr_cjs
kprr_cjs_dn1 = _seg_kprr_cjs.add_line('dn1', {'kprr': ['s3', 's4'], 'cjs': ['s3', 's4']})
kprr_cjs_up1 = _seg_kprr_cjs.add_line('up1', {'kprr': ['s1', 's2', 's4'], 'cjs': ['s1', 's2', 's4']})

_seg_cjs_kdpa = Segment.new('cjs', 'kdpa', 6.99, stations_list)
segments_by_pair[_seg_cjs_kdpa.name] = _seg_cjs_kdpa
cjs_kdpa_dn1 = _seg_cjs_kdpa.add_line('dn1', {'cjs': ['s3', 's4'], 'kdpa': ['s1', 's3', 's4']})
cjs_kdpa_up1 = _seg_cjs_kdpa.add_line('up1', {'cjs': ['s1', 's2', 's4'], 'kdpa': ['s1', 's2']})

_seg_kdpa_dir = Segment.new('kdpa', 'dir', 6.64, stations_list)
segments_by_pair[_seg_kdpa_dir.name] = _seg_kdpa_dir
kdpa_dir_dn1 = _seg_kdpa_dir.add_line('dn1', {'kdpa': ['s1', 's3', 's4'], 'dir': ['s3', 's4']})
kdpa_dir_up1 = _seg_kdpa_dir.add_line('up1', {'kdpa': ['s1', 's2'], 'dir': ['s1', 's2', 's4']})

_seg_dir_jyp = Segment.new('dir', 'jyp', 7.07, stations_list)
segments_by_pair[_seg_dir_jyp.name] = _seg_dir_jyp
dir_jyp_dn1 = _seg_dir_jyp.add_line('dn1', {'dir': ['s3', 's4'], 'jyp': ['s1', 's3', 's4', 's5']})
dir_jyp_up1 = _seg_dir_jyp.add_line('up1', {'dir': ['s1', 's2', 's4'], 'jyp': ['s1', 's2', 's4', 's5']})

_seg_jyp_cts = Segment.new('jyp', 'cts', 7.09, stations_list)
segments_by_pair[_seg_jyp_cts.name] = _seg_jyp_cts
jyp_cts_dn1 = _seg_jyp_cts.add_line('dn1', {'jyp': ['s1', 's3', 's4', 's5'], 'cts': ['s3', 's4']})
jyp_cts_up1 = _seg_jyp_cts.add_line('up1', {'jyp': ['s1', 's2', 's4', 's5'], 'cts': ['s1', 's2', 's3']})

_seg_cts_mvg = Segment.new('cts', 'mvg', 6.95, stations_list)
segments_by_pair[_seg_cts_mvg.name] = _seg_cts_mvg
cts_mvg_dn1 = _seg_cts_mvg.add_line('dn1', {'cts': ['s3', 's4'], 'mvg': ['s1', 's2', 's3']})
cts_mvg_up1 = _seg_cts_mvg.add_line('up1', {'cts': ['s1', 's2', 's3'], 'mvg': ['s1', 's2', 's3']})

_seg_mvg_jrt = Segment.new('mvg', 'jrt', 11.4, stations_list)
segments_by_pair[_seg_mvg_jrt.name] = _seg_mvg_jrt
mvg_jrt_mid1 = _seg_mvg_jrt.add_line('mid1', {'mvg': ['s1', 's2', 's3'], 'jrt': ['s1', 's2', 's3']})

_seg_jrt_mvf = Segment.new('jrt', 'mvf', 9.21, stations_list)
segments_by_pair[_seg_jrt_mvf.name] = _seg_jrt_mvf
jrt_mvf_mid1 = _seg_jrt_mvf.add_line('mid1', {'jrt': ['s1', 's2', 's3'], 'mvf': ['s1', 's2', 's3', 's4']})

_seg_mvf_krpu = Segment.new('mvf', 'krpu', 6.83, stations_list)
segments_by_pair[_seg_mvf_krpu.name] = _seg_mvf_krpu
mvf_krpu_dn1 = _seg_mvf_krpu.add_line('dn1', {'mvf': ['s1', 's2', 's3', 's4'], 'krpu': ['s1', 's3', 's4', 's5', 's6', 's7', 's8']})
mvf_krpu_up1 = _seg_mvf_krpu.add_line('up1', {'mvf': ['s1', 's2', 's3', 's4'], 'krpu': ['s1', 's2', 's4', 's5', 's6', 's7', 's8']})

_seg_krpu_dmrt = Segment.new('krpu', 'dmrt', 10.78, stations_list)
segments_by_pair[_seg_krpu_dmrt.name] = _seg_krpu_dmrt
krpu_dmrt_dn1 = _seg_krpu_dmrt.add_line('dn1', {'krpu': ['s1', 's3', 's4', 's5', 's6', 's7', 's8'], 'dmrt': ['s1', 's3', 's2', 's5']})
krpu_dmrt_up1 = _seg_krpu_dmrt.add_line('up1', {'krpu': ['s1', 's3', 's4', 's5', 's6', 's7', 's8'], 'dmrt': ['s1','s3', 's4', 's5']})

_seg_dmrt_dmnj = Segment.new('dmrt', 'dmnj', 8.12, stations_list)
segments_by_pair[_seg_dmrt_dmnj.name] = _seg_dmrt_dmnj
dmrt_dmnj_dn1 = _seg_dmrt_dmnj.add_line('dn1', {'dmrt': ['s1', 's2','s4', 's5'], 'dmnj': ['s1', 's2', 's4', 's5', 's6', 's7', 's8', 's9', 's10']})
dmrt_dmnj_up1 = _seg_dmrt_dmnj.add_line('up1', {'dmrt': ['s1', 's3', 's4', 's5'], 'dmnj': ['s3', 's4', 's5', 's6', 's7', 's8', 's9', 's10']})
 
_seg_dmnj_bgua = Segment.new('dmnj', 'bgua', 14.55, stations_list)
segments_by_pair[_seg_dmnj_bgua.name] = _seg_dmnj_bgua
dmnj_bgua_dn1 = _seg_dmnj_bgua.add_line('dn1', {'dmnj': ['s1', 's2', 's4', 's5', 's6', 's7', 's8', 's9', 's10'], 'bgua': ['s1', 's2']})
dmnj_bgua_up1 = _seg_dmnj_bgua.add_line('up1', {'dmnj': ['s3', 's4', 's5', 's6', 's7', 's8', 's9', 's10'], 'bgua': ['s2', 's3', 's4']})

_seg_bgua_kkgm = Segment.new('bgua', 'kkgm', 12.44, stations_list)
segments_by_pair[_seg_bgua_kkgm.name] = _seg_bgua_kkgm
bgua_kkgm_mid1 = _seg_bgua_kkgm.add_line('mid1', {'bgua': ['s1', 's2', 's3', 's4'], 'kkgm': ['s1', 's2', 's3', 's4']})

_seg_kkgm_lkmr = Segment.new('kkgm', 'lkmr', 15.28, stations_list)
segments_by_pair[_seg_kkgm_lkmr.name] = _seg_kkgm_lkmr
kkgm_lkmr_mid1 = _seg_kkgm_lkmr.add_line('mid1', {'kkgm': ['s1', 's2', 's3', 's4'], 'lkmr': ['s1', 's2', 's3', 's4']})

_seg_lkmr_sgrm = Segment.new('lkmr', 'sgrm', 12.83, stations_list)
segments_by_pair[_seg_lkmr_sgrm.name] = _seg_lkmr_sgrm
lkmr_sgrm_dn1 = _seg_lkmr_sgrm.add_line('dn1', {'lkmr': ['s1', 's2'], 'sgrm': ['s1', 's2']})
lkmr_sgrm_up1 = _seg_lkmr_sgrm.add_line('up1', {'lkmr': ['s1', 's3', 's4'], 'sgrm': ['s1', 's3', 's4']})

_seg_sgrm_tkri = Segment.new('sgrm', 'tkri', 9.07, stations_list)
segments_by_pair[_seg_sgrm_tkri.name] = _seg_sgrm_tkri
sgrm_tkri_dn1 = _seg_sgrm_tkri.add_line('dn1', {'sgrm': ['s1', 's2'], 'tkri': ['s1', 's2', 's3', 's4','s5', 's6']})
sgrm_tkri_up1 = _seg_sgrm_tkri.add_line('up1', {'sgrm': ['s1', 's3', 's4'], 'tkri': ['s1', 's2', 's3','s4', 's5', 's6']})

_seg_tkri_rul = Segment.new('tkri', 'rul', 12.43, stations_list)
segments_by_pair[_seg_tkri_rul.name] = _seg_tkri_rul
tkri_rul_mid1 = _seg_tkri_rul.add_line('mid1', {'tkri': ['s1', 's2', 's3', 's4', 's5', 's6'], 'rul': ['s1', 's2', 's3']})

_seg_rul_llgm = Segment.new('rul', 'llgm', 16.5, stations_list)
segments_by_pair[_seg_rul_llgm.name] = _seg_rul_llgm
rul_llgm_mid1 = _seg_rul_llgm.add_line('mid1', {'rul': ['s1', 's2', 's3'], 'llgm': ['s1', 's2', 's3']})

_seg_llgm_blmk = Segment.new('llgm', 'blmk', 16.93, stations_list)
segments_by_pair[_seg_llgm_blmk.name] = _seg_llgm_blmk
llgm_blmk_mid1 = _seg_llgm_blmk.add_line('mid1', {'llgm': ['s1', 's2', 's3'], 'blmk': ['s1', 's2', 's3']})

_seg_blmk_skpi = Segment.new('blmk', 'skpi', 10.4, stations_list)
segments_by_pair[_seg_blmk_skpi.name] = _seg_blmk_skpi
blmk_skpi_mid1 = _seg_blmk_skpi.add_line('mid1', {'blmk': ['s1', 's2', 's3'], 'skpi': ['s1', 's2', 's3']})

_seg_skpi_ktga = Segment.new('skpi', 'ktga', 14.77, stations_list)
segments_by_pair[_seg_skpi_ktga.name] = _seg_skpi_ktga
skpi_ktga_mid1 = _seg_skpi_ktga.add_line('mid1', {'skpi': ['s1', 's2', 's3'], 'ktga': ['s1', 's2', 's3', 's4']})

_seg_ktga_sprd = Segment.new('ktga', 'sprd', 9.63, stations_list)
segments_by_pair[_seg_ktga_sprd.name] = _seg_ktga_sprd
ktga_sprd_mid1 = _seg_ktga_sprd.add_line('mid1', {'ktga': ['s1', 's2', 's3', 's4'], 'sprd': ['s1', 's2', 's3', 's4', 's5']})

_seg_sprd_rgda = Segment.new('sprd', 'rgda', 9.23, stations_list)
segments_by_pair[_seg_sprd_rgda.name] = _seg_sprd_rgda
sprd_rgda_dn1 = _seg_sprd_rgda.add_line('dn1', {'sprd': ['s1', 's2', 's3','s4', 's5'], 'rgda': ['s1', 's2', 's3', 's4', 's5', 's7', 's8', 's9']})
sprd_rgda_up1 = _seg_sprd_rgda.add_line('up1', {'sprd': ['s1', 's2', 's3','s4', 's5'], 'rgda': ['s1', 's2', 's3', 's4', 's6', 's7', 's8', 's9']})
sprd_rgda_mid1 = _seg_sprd_rgda.add_line('mid1', {'sprd': ['s1', 's2', 's3', 's4', 's5'], 'rgda': ['s1', 's2', 's3', 's4', 's9']})

_seg_rgda_ldx = Segment.new('rgda', 'ldx', 7.82, stations_list)
segments_by_pair[_seg_rgda_ldx.name] = _seg_rgda_ldx
rgda_ldx_dn1 = _seg_rgda_ldx.add_line('dn1', {'rgda': ['s1', 's2', 's3', 's4', 's5', 's7', 's8', 's9'], 'ldx': ['s1', 's2']})
rgda_ldx_up1 = _seg_rgda_ldx.add_line('up1', {'rgda': ['s1', 's2', 's3', 's4', 's6', 's7', 's8', 's9'], 'ldx': ['s1', 's3', 's4']})

_seg_ldx_jmpt = Segment.new('ldx', 'jmpt', 7.18, stations_list)
segments_by_pair[_seg_ldx_jmpt.name] = _seg_ldx_jmpt
ldx_jmpt_dn1 = _seg_ldx_jmpt.add_line('dn1', {'ldx': ['s1', 's2'], 'jmpt': ['s1', 's2', 's4', 's5', 's6']})
ldx_jmpt_up1 = _seg_ldx_jmpt.add_line('up1', {'ldx': ['s1', 's3', 's4'], 'jmpt': ['s3', 's4', 's5', 's6']})

_seg_jmpt_knrt = Segment.new('jmpt', 'knrt', 9.14, stations_list)
segments_by_pair[_seg_jmpt_knrt.name] = _seg_jmpt_knrt
jmpt_knrt_dn1 = _seg_jmpt_knrt.add_line('dn1', {'jmpt': ['s1', 's2', 's4'], 'knrt': ['s1', 's2', 's4']})
jmpt_knrt_up1 = _seg_jmpt_knrt.add_line('up1', {'jmpt': ['s3', 's4'], 'knrt': ['s1', 's3', 's4']})
jmpt_knrt_mid1 = _seg_jmpt_knrt.add_line('mid1', {'jmpt': [ 's4','s5', 's6'], 'knrt': ['s2','s3', 's4','s5', 's6']})

_seg_knrt_gmda = Segment.new('knrt', 'gmda', 8.87, stations_list)
segments_by_pair[_seg_knrt_gmda.name] = _seg_knrt_gmda
knrt_gmda_dn1 = _seg_knrt_gmda.add_line('dn1', {'knrt': ['s1', 's2', 's4'], 'gmda': ['s1', 's2']})
knrt_gmda_up1 = _seg_knrt_gmda.add_line('up1', {'knrt': [ 's1', 's3', 's4'], 'gmda': ['s1','s2', 's3', 's4']})
knrt_gmda_mid1 = _seg_knrt_gmda.add_line('mid1', {'knrt': ['s2','s3', 's4','s5', 's6'], 'gmda': ['s1','s2','s5', 's6']})
# knrt_gmda_mid1 = block_sec('mid1', 'knrt', 'gmda', 8.87, {'knrt': ['s2','s3', 's4','s5', 's6'], 'gmda': ['s1', 's2','s3','s4','s5', 's6']}, stations_list)

_seg_gmda_pvp = Segment.new('gmda', 'pvp', 13.59, stations_list)
segments_by_pair[_seg_gmda_pvp.name] = _seg_gmda_pvp
gmda_pvp_dn1 = _seg_gmda_pvp.add_line('dn1', {'gmda': ['s1', 's2'], 'pvp': ['s1', 's2', 's4', 's5', 's6']})
gmda_pvp_up1 = _seg_gmda_pvp.add_line('up1', {'gmda': ['s1', 's2','s3', 's4'], 'pvp': ['s1', 's3', 's4', 's5', 's6']})
gmda_pvp_mid1 = _seg_gmda_pvp.add_line('mid1', {'gmda': ['s1', 's2','s3','s4','s5', 's6'], 'pvp': ['s5', 's6']})

_seg_pvp_snm = Segment.new('pvp', 'snm', 12.8, stations_list)
segments_by_pair[_seg_pvp_snm.name] = _seg_pvp_snm
pvp_snm_dn1 = _seg_pvp_snm.add_line('dn1', {'pvp': ['s1', 's2', 's4', 's5', 's6'], 'snm': ['s1', 's2', 's4', 's5']})
pvp_snm_up1 = _seg_pvp_snm.add_line('up1', {'pvp': ['s1', 's3', 's4', 's5', 's6'], 'snm': ['s3', 's4', 's5']})

_seg_snm_vbl = Segment.new('snm', 'vbl', 11.28, stations_list)
segments_by_pair[_seg_snm_vbl.name] = _seg_snm_vbl
snm_vbl_dn1 = _seg_snm_vbl.add_line('dn1', {'snm': ['s1', 's2', 's4', 's5'], 'vbl': ['s1', 's2', 's4', 's5']})
snm_vbl_up1 = _seg_snm_vbl.add_line('up1', {'snm': ['s3', 's4', 's5'], 'vbl': ['s1', 's3', 's4', 's5']})
 
_seg_vbl_dnv = Segment.new('vbl', 'dnv', 11.96, stations_list)
segments_by_pair[_seg_vbl_dnv.name] = _seg_vbl_dnv
vbl_dnv_dn1 = _seg_vbl_dnv.add_line('dn1', {'vbl': ['s1', 's2', 's4', 's5'], 'dnv': ['s1', 's2']})
vbl_dnv_up1 = _seg_vbl_dnv.add_line('up1', {'vbl': ['s1', 's3', 's4', 's5'], 'dnv': ['s1', 's3', 's4', 's5']})
vbl_dnv_mid1 = _seg_vbl_dnv.add_line('mid1', {'vbl': ['s1', 's3', 's4', 's5'], 'dnv': ['s1', 's2', 's3', 's4', 's5']})
# added extra 's2' at the dnv station


_seg_dnv_kmx = Segment.new('dnv', 'kmx', 9.81, stations_list)
segments_by_pair[_seg_dnv_kmx.name] = _seg_dnv_kmx
dnv_kmx_dn1 = _seg_dnv_kmx.add_line('dn1', {'dnv': ['s1', 's2'], 'kmx': ['s1', 's2', 's3']})
dnv_kmx_up1 = _seg_dnv_kmx.add_line('up1', {'dnv': ['s1', 's2', 's3', 's4', 's5'], 'kmx': ['s1', 's2', 's4', 's5']})

_seg_kmx_gpi = Segment.new('kmx', 'gpi', 9.56, stations_list)
segments_by_pair[_seg_kmx_gpi.name] = _seg_kmx_gpi
kmx_gpi_dn1 = _seg_kmx_gpi.add_line('dn1', {'kmx': ['s1', 's2', 's3'], 'gpi': ['s1', 's2', 's4']})
kmx_gpi_up1 = _seg_kmx_gpi.add_line('up1', {'kmx': ['s1', 's2', 's4', 's5'], 'gpi': ['s3', 's4']})

_seg_gpi_grbl = Segment.new('gpi', 'grbl', 10.52, stations_list)
segments_by_pair[_seg_gpi_grbl.name] = _seg_gpi_grbl
gpi_grbl_dn1 = _seg_gpi_grbl.add_line('dn1', {'gpi': ['s1', 's2', 's4'], 'grbl': ['s1', 's2', 's3']})
gpi_grbl_up1 = _seg_gpi_grbl.add_line('up1', {'gpi': ['s3', 's4'], 'grbl': ['s1', 's2', 's4', 's5']})

_seg_grbl_gtlm = Segment.new('grbl', 'gtlm', 5.84, stations_list)
segments_by_pair[_seg_grbl_gtlm.name] = _seg_grbl_gtlm
grbl_gtlm_dn1 = _seg_grbl_gtlm.add_line('dn1', {'grbl': ['s1', 's2', 's3'], 'gtlm': ['s1', 's2', 's4']})
grbl_gtlm_up1 = _seg_grbl_gtlm.add_line('up1', {'grbl': ['s1', 's2', 's4', 's5'], 'gtlm': ['s3', 's4']})


blocksections_list = [
    krdl_bchl_dn1, krdl_bchl_up1,
    bchl_bhns_mid1,
    bhns_kmlr_mid1,
    kmlr_dwz_dn1, kmlr_dwz_up1,
    dwz_giz_dn1, dwz_giz_up1,
    giz_dbf_dn1, giz_dbf_up1,
    dbf_kwgn_dn1, dbf_kwgn_up1,
    kwgn_kklu_dn1, kwgn_kklu_up1,
    kklu_kmsd_dn1, kklu_kmsd_up1,
    kmsd_szy_dn1, kmsd_szy_up1,
    szy_dmk_dn1, szy_dmk_up1,
    dmk_bdxx_dn1, dmk_bdxx_up1,
    bdxx_tpq_dn1, bdxx_tpq_up1,
    tpq_kmez_dn1, tpq_kmez_up1,
    kmez_jdb_dn1, kmez_jdb_up1,
    jdb_nkx_dn1, jdb_nkx_up1,
    nkx_agz_dn1, nkx_agz_up1,
    agz_agb_dn1, agz_agb_up1,
    agb_kprr_dn1, agb_kprr_up1,
    kprr_cjs_dn1, kprr_cjs_up1,
    cjs_kdpa_dn1, cjs_kdpa_up1,
    kdpa_dir_dn1, kdpa_dir_up1,
    dir_jyp_dn1, dir_jyp_up1,
    jyp_cts_dn1, jyp_cts_up1,
    cts_mvg_dn1, cts_mvg_up1,
    mvg_jrt_mid1,
    jrt_mvf_mid1,
    mvf_krpu_dn1, mvf_krpu_up1,
    krpu_dmrt_dn1, krpu_dmrt_up1,
    dmrt_dmnj_dn1, dmrt_dmnj_up1,
    dmnj_bgua_dn1, dmnj_bgua_up1,
    bgua_kkgm_mid1,
    kkgm_lkmr_mid1,
    lkmr_sgrm_dn1, lkmr_sgrm_up1,
    sgrm_tkri_dn1, sgrm_tkri_up1,
    tkri_rul_mid1,
    rul_llgm_mid1,
    llgm_blmk_mid1,
    blmk_skpi_mid1,
    skpi_ktga_mid1,
    ktga_sprd_mid1,
    sprd_rgda_dn1, sprd_rgda_up1,
      sprd_rgda_mid1,
    rgda_ldx_dn1, rgda_ldx_up1,
    ldx_jmpt_dn1, ldx_jmpt_up1,
    jmpt_knrt_dn1, jmpt_knrt_up1, 
    jmpt_knrt_mid1,
    knrt_gmda_dn1, knrt_gmda_up1,
      knrt_gmda_mid1,
    gmda_pvp_dn1, gmda_pvp_up1,
      gmda_pvp_mid1,
    pvp_snm_dn1, pvp_snm_up1,
    snm_vbl_dn1, snm_vbl_up1,
    vbl_dnv_dn1, vbl_dnv_up1,
    dnv_kmx_dn1, dnv_kmx_up1,
    kmx_gpi_dn1, kmx_gpi_up1,
    gpi_grbl_dn1, gpi_grbl_up1,
    grbl_gtlm_dn1, grbl_gtlm_up1,
]

# populate_connections(blocksections_list, station_dict, stations_list)

