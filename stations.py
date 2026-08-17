import pandas as pd


def create_station_class(station_name, longitude, station_config):
    class DynamicStation:
        def __init__(self):
            self.name = station_name
            self.longitude = longitude
            self.tracks = {}
            self.connections = {}
            for track_name, platform_num in station_config["tracks"].items():
                self.tracks[track_name] = [0, platform_num, 0, 0, pd.Timedelta(0), '']

        def station_connset(self, station_config):
            for conn_name, direction in station_config["connections"].items():
                self.connections[conn_name] = [0, direction, '']

        def set_occupancy_arr(self, stn_track_name, occ_start, occ_end, train_name):
            if stn_track_name in self.tracks:
                self.tracks[stn_track_name][0] = 1
                self.tracks[stn_track_name][2] = occ_start
                self.tracks[stn_track_name][3] = occ_end
                self.tracks[stn_track_name][5] = train_name
            else:
                print('\n Track is not found')

        def set_occupancy_dep(self, stn_track_name, t):
            if stn_track_name in self.tracks:
                self.tracks[stn_track_name][0] = 0
                self.tracks[stn_track_name][4] = t - self.tracks[stn_track_name][2] + self.tracks[stn_track_name][4]
                self.tracks[stn_track_name][2] = pd.Timestamp("2100-06-01 22:52:00")
                self.tracks[stn_track_name][3] = pd.Timestamp("2100-06-01 22:52:00")
                self.tracks[stn_track_name][5] = ''
            else:
                print('\n Track is not found')

        def set_occ_conn_in(self, blsec_in_stn_track_name, train_name, status):
            if blsec_in_stn_track_name in self.connections:
                self.connections[blsec_in_stn_track_name][0] = status
                self.connections[blsec_in_stn_track_name][2] = train_name
            else:
                print('\n Connection is not found')

        def set_occ_conn_out(self, blsec_out_stn_track_name, train_name, status):
            if blsec_out_stn_track_name in self.connections:
                self.connections[blsec_out_stn_track_name][0] = status
                self.connections[blsec_out_stn_track_name][2] = train_name
            else:
                print('\n Connection is not found')

        # if station line is being occupied for longer duration, update the occupancy end time
        def set_occupancy_updt(self, stn_line_name, occ_end):
            # self.tracks[stn_line_name][3] = occ_end
            if stn_line_name in self.tracks:
                self.tracks[stn_line_name][3] = occ_end
            else:
                print('\n Track is not found')

        def is_occupied(self, track_name):
            if self.tracks[track_name][0] == 1:
                return track_name + ' is occupied'
            return track_name + ' is not occupied'

    return DynamicStation()


def populate_connections(blocksections_list, station_dict, stations_list):
    """Fill each station's connections from the block sections that touch it.

    Run this once, after both the station objects and the block sections are
    constructed. Centralised here so every *_data.py file calls the same
    function instead of duplicating the loop body.
    """
    # 1) fill station_dict connections from each block section
    for k in blocksections_list:
        for stn_name in k.stn_conns:
            for conn_key in k.stn_conns[stn_name]:
                station_dict[stn_name]['connections'][conn_key] = k.dir_mvmt
    # 2) push them onto the station objects
    for s in stations_list:
        s.station_connset(station_dict[s.name])
