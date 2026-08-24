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

        def assign_line(self, train, t_ind, next_event_tr_id, len_sched, sched_act, blsec_t, prev_station, blsec_id_fn, conn_exists_fn):
            """Which of this station's tracks (if any) a just-arrived train should occupy,
            and the connection key(s) linking it to the block section on either side.

            Stage 2 of docs/event-manager-design.md -- absorbs
            iidsim.engine.resolve.ResolveMixin.stn_line_assign, translated line-for-line
            (not redesigned) to minimize the risk of a subtle behavior change: every
            `self.X` read in the original became an explicit parameter here (`self` in
            the original was always `self.stns_event[0]`, i.e. this station). blsec_id_fn
            / conn_exists_fn are the Simulation's own blsec_id/conn_exists bound methods,
            passed in rather than duplicated here since they need the network-wide
            block-section lookup this class deliberately doesn't own.

            Returns [occ_flag, line_name, conn1, conn2] -- same shape as before.
            """
            stn_line_occ_flag = 0
            stn_line_occ_name = ''
            next_event_conn1 = ''
            next_event_conn2 = ''
            stn1 = ''
            stn2 = self.name
            stn3 = ''
            if t_ind > 1:
                if t_ind != len_sched - 2:
                    stn1 = prev_station.name
                    stn3 = sched_act[next_event_tr_id][t_ind + 2]
                    out_blsec_dir = blsec_id_fn(stn2, stn3).dir_mvmt
                else:
                    stn1 = sched_act[next_event_tr_id][t_ind - 4]
                arrived_dir = blsec_t.dir_mvmt
            else:
                stn3 = sched_act[next_event_tr_id][t_ind + 2]
                out_blsec_dir = blsec_id_fn(stn2, stn3).dir_mvmt
            tracks = self.tracks
            if train.tr_type == 'g':
                track_order = sorted(tracks.keys(), key=lambda track_name: tracks[track_name][1] != 0)
            else:
                track_order = list(tracks.keys())
            arrival_time = train.tr_sched_act[self.name][0]
            departure_time = train.tr_sched_act[self.name][1]
            same_arr_dep = arrival_time == departure_time
            halting_passenger = train.tr_type == 'p' and (not same_arr_dep)
            total_passes = 2 if halting_passenger else 1
            for pass_no in range(total_passes):
                for track_name in track_order:
                    if self.tracks[track_name][0] != 0:
                        continue
                    if pass_no == 0 and halting_passenger and (self.tracks[track_name][1] == 0):
                        continue
                    if t_ind > 1:
                        incoming_conn = blsec_t.name + '_' + str(track_name)
                        if incoming_conn not in self.connections:
                            incoming_conn = None
                        if t_ind != len_sched - 2:
                            outgoing_conn = conn_exists_fn(self, stn2, stn3, out_blsec_dir, track_name)
                            if incoming_conn and outgoing_conn:
                                next_event_conn1, next_event_conn2 = (incoming_conn, outgoing_conn)
                            else:
                                next_event_conn1 = next_event_conn2 = ''
                        else:
                            next_event_conn1 = incoming_conn if incoming_conn else ''
                            next_event_conn2 = ''
                    else:
                        incoming_conn = conn_exists_fn(self, stn2, stn3, out_blsec_dir, track_name)
                        next_event_conn1 = incoming_conn if incoming_conn else ''
                        next_event_conn2 = ''
                    if next_event_conn1 != '':
                        stn_line_occ_flag = 1
                        stn_line_occ_name = track_name
                        return [stn_line_occ_flag, stn_line_occ_name, next_event_conn1, next_event_conn2]
            return [stn_line_occ_flag, stn_line_occ_name, next_event_conn1, next_event_conn2]

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
