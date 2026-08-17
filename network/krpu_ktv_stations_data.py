import pandas as pd
from stations import create_station_class
from stations_longitude import station_longitudes

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

# ── Station object instantiation (longitude from stations_longitude.py) ──
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

