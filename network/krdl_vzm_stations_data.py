import pandas as pd
from stations import create_station_class
from stations_longitude import station_longitudes

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

# ── Station object instantiation (longitude from stations_longitude.py) ──
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

