import pandas as pd
from stations import create_station_class
from stations_longitude import station_longitudes

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

# ── Station object instantiation (longitude from stations_longitude.py) ──
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

