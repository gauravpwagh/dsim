"""Part of the simulation engine -- see docs/restructure-notes.md and docs/simulation-engine.md. Mixed into Simulation (engine/run.py); every method here reads/writes shared per-run state via self.X (see SimulationState in engine/state.py)."""

# import json
# import time
# import numpy as np
import pandas as pd
# from pandas import Timestamp
# from scipy import stats as _halt_dev_stats
# from openpyxl.styles import Alignment, Font
# import iidsim.network as _network
# from iidsim import schedules
# from iidsim.data import geography, halt_deviation, timing
# from iidsim.reporting.chart import plot_railway_chart
# from iidsim.reporting.extract import filter_df_by_date_window, get_formatted_data_from_df

class ResolveMixin:

    def blsec_id(self, stn1, stn2):
        for j in self.stations_list:
            if j.name == stn1:
                stn_start = j
                break
        for k in self.stations_list:
            if k.name == stn2:
                stn_end = k
                break
        if stn_start.longitude - stn_end.longitude > 0:
            train_dir = 'up'
        else:
            train_dir = 'dn'
        same_long = stn_start.longitude == stn_end.longitude
        blsec_base = self.conn_base(stn1, stn2)
        blsec_base_alt = self.conn_base(stn2, stn1)
        print('blsec base ', blsec_base, '| same_long', same_long)
        print('inside blocksection assign function')
        blsec_list = []
        for l in self.blocksections_list:
            if l.dir_mvmt[0:2] == train_dir or l.dir_mvmt[0:3] == 'mid':
                if l.name.startswith(blsec_base + '_') or l.name.startswith(blsec_base_alt + '_'):
                    blsec_list.append(l)
        print('blsec list is ', [b.name for b in blsec_list])
        if self.next_event_type == 'a' and len(self.stns_event) > 1:
            for blsec in blsec_list:
                print('blsec is ', blsec.name)
                if blsec.occ_ind == 1 and blsec.occ_train == self.next_event_tr_id:
                    print('arrival event and blsec is ', blsec.name)
                    return blsec
                check_auto = self.autoblsec_check()
                if check_auto:
                    print('it is autoblock section')
                    print('auto blsec list is ', blsec.autoblsec_list)
                    if blsec.autoblsec_list and self.next_event_tr_id == blsec.autoblsec_list[0][0]:
                        print('arrival event and autoblock case ', blsec.name)
                        return blsec
        print('block assign fun before checking the connections ', blsec_list)
        print('block assign fun before checking the connections ', [b.name for b in blsec_list])
        stn_line_occ_name = ''
        for j in stn_start.tracks:
            if stn_start.tracks[j][0] == 1 and stn_start.tracks[j][5] == self.tr_next_event.train_id:
                stn_line_occ_name = j
                break
        if stn_line_occ_name:
            blsec_list = [l for l in blsec_list if l.name + '_' + stn_line_occ_name in stn_start.connections]
            if not blsec_list:
                raise ValueError(f'blsec_id({stn1!r}, {stn2!r}): station line {stn_line_occ_name!r} is not connected to any candidate block section')
        print('block section assign function after checking the connections; block secction list is ', [(b.name, b.occ_train) for b in blsec_list])
        print('/n inside blsec_id function; blsec list is ', blsec_list)
        if self.next_event_type == 'd':
            if len(blsec_list) == 1:
                print('single candidate', blsec_list[0].name, '-> assigning directly')
                return blsec_list[0]
            print('\n length of the blsec_list is inside dept case ', len(blsec_list))
            for blsec in blsec_list:
                if self.next_event_tr_id in blsec.blsec_queue[0::6]:
                    if blsec.occ_ind == 0:
                        print('train', self.next_event_tr_id, 'is queued in free', blsec.name, '-> assigning it')
                        return blsec
                    sib = blsec.find_free_sibling(self.blsec_lookup, stn_start, stn_line_occ_name, train_dir=train_dir)
                    if sib is not None:
                        print('train', self.next_event_tr_id, 'was queued in occupied', blsec.name, '-> redirecting to free sibling', sib.name)
                        t_index = self.sched_act[self.next_event_tr_id].index(self.t)
                        dep_list = [self.next_event_tr_id, self.next_event_train, self.tr_next_event.tr_type, t_index, self.t, self.sched_act[self.next_event_tr_id][t_index + 2]]
                        blsec.queue_remove(dep_list)
                        return sib
                    print('train', self.next_event_tr_id, 'is queued in occupied', blsec.name, '-> assigning this block section directly')
                    return blsec
        end_times = []
        end_times_name = []
        if len(blsec_list) > 1:
            print('\n case when more than one block section')
            for blsec in blsec_list:
                blsec_end_time = self.get_queue_end_time(blsec)
                end_times.append((blsec, blsec_end_time))
                end_times_name.append((blsec.name, blsec_end_time))
                print(blsec.name, blsec_end_time)
            print('end times list is ', end_times_name)
            free_time = pd.Timestamp('1900-01-01 00:00:00')
            if all((t == free_time for _, t in end_times)):
                print('when all blocksections are free')
                preferred = [(b, t) for b, t in end_times if b.dir_mvmt.startswith(('up', 'dn'))]
                if preferred:
                    selected_blsec = preferred[0][0]
                else:
                    selected_blsec = end_times[0][0]
            else:
                selected_blsec = min(end_times, key=lambda x: x[1])[0]
                print('case when more than two blocksections; one is occupied and other is not ', selected_blsec.name)
        else:
            return blsec_list[0]
        return selected_blsec

    def check_next_blse_stn_occupancy(self, t_ind, len_sched):
        next_stn_occ = {}
        next_stn_line_min_endtimes = pd.Timestamp('2100-01-01 00:00:00')
        up_dir_stn_count, dn_dir_stn_count = (0, 0)
        count_next_blsec = 0
        count_curr_blsec = 0
        next_blsec_list = []
        next_blsec_list_names = []
        curr_blsec_list = []
        stn1 = self.stns_event[0].name
        stn2 = ''
        stn3 = ''
        if t_ind != len_sched - 1:
            stn2 = self.stns_event[1].name
            curr_blsec = self.conn_base(stn1, stn2)
            print('current blocksection name is ', curr_blsec)
            for b in self.blocksections_list:
                if b.name.startswith(curr_blsec):
                    count_curr_blsec += 1
            for i, vals in self.stns_event[1].tracks.items():
                train = vals[5]
                train_dir = None
                _t = self.trains_by_id.get(train)
                if _t is not None:
                    train_dir = self.train_direction(_t, self.stns_event[1].name)
                next_stn_occ[i] = [vals[0], vals[3], train_dir, vals[5]]
                print('type of vals[3] is ', type(vals[3]))
                if isinstance(vals[3], pd.Timestamp):
                    if vals[3] < next_stn_line_min_endtimes:
                        next_stn_line_min_endtimes = vals[3]
                if vals[0] == 1:
                    if train_dir == 0:
                        dn_dir_stn_count += 1
                    else:
                        up_dir_stn_count += 1
            if t_ind + 4 < len(self.sched_act[self.next_event_tr_id]):
                stn3_candidate = self.sched_act[self.next_event_tr_id][t_ind + 4]
                if isinstance(stn3_candidate, str):
                    stn3 = stn3_candidate
            if stn3 == '':
                stn3 = self.find_stn3(stn1, stn2)
                print('next to next station is found so, stn3 is ', stn3)
            if stn3 != '':
                next_blsec_name = self.conn_base(stn2, stn3)
                print('next to next blocksection name ', next_blsec_name)
                for b in self.blocksections_list:
                    if b.name.startswith(next_blsec_name):
                        count_next_blsec += 1
                        blsec_tr_dir = None
                        blsec_occ_train_name = b.occ_train.split('_')[0] if b.occ_train else None
                        _t = self.trains_by_id.get(blsec_occ_train_name)
                        if _t is not None:
                            blsec_tr_dir = self.train_direction(_t, b.stn_west.name)
                            print('train name is ', _t.train_id, ' and its direction is ', blsec_tr_dir)
                            print('blsec occ train name is ', blsec_occ_train_name)
                        next_blsec_list.append([b, blsec_tr_dir])
                        next_blsec_list_names.append([b.name, blsec_tr_dir])
            else:
                print('next to next station not found; stn2 is last in corridor')
                count_next_blsec = count_curr_blsec
        print(f'down dir stn line count is ', {dn_dir_stn_count}, 'up dir stn line count is ', {up_dir_stn_count})
        print('next blocksections list ', next_blsec_list_names)
        print('next station lines occ details ', next_stn_occ)
        return [dn_dir_stn_count, up_dir_stn_count, next_stn_line_min_endtimes, count_next_blsec, count_curr_blsec, next_blsec_list]

    def conn_base(self, a, b, dir_mvmt=None):
        w, e = (a, b) if self.station_longitudes[a] <= self.station_longitudes[b] else (b, a)
        print(f'conn base output is = {w}_{e}_{dir_mvmt}')
        return f'{w}_{e}_{dir_mvmt}' if dir_mvmt else f'{w}_{e}'

    def conn_exists(self, stn, a, b, dir_mvmt, line):
        """Return the real connection key (a_b or swapped b_a) present at `stn`, else None.
           Handles equal-longitude pairs where west/east ordering is ambiguous."""
        print('inside the conn_exists function')
        for base in (self.conn_base(a, b, dir_mvmt), self.conn_base(b, a, dir_mvmt)):
            print('base blec name coming form conn_base is ', base)
            key = base + '_' + str(line)
            print('connection key in conn_exits is ', key)
            if key in stn.connections:
                return key
        return None

    # find_free_sibling_blsec was here -- moved to BlockSection.find_free_sibling
    # (domain/block_section.py) as part of docs/event-manager-design.md stage 4. See
    # that method's docstring for the translation notes; verified via a before/after
    # total_schedule diff (git history has the original if it's ever needed).

    def find_stn3(self, stn1, stn2):
        """Return the station adjacent to stn2 along the train's direction of travel,
        derived from block-section. Returns '' if stn2 is at the end of the
        physical network (no other block section touches it)."""
        curr_blsec_base = self.conn_base(stn1, stn2)
        for b in self.blocksections_list:
            if b.name.startswith(curr_blsec_base + '_'):
                continue
            if b.stn_west.name == stn2:
                return b.stn_east.name
            if b.stn_east.name == stn2:
                return b.stn_west.name
        return ''

    def get_min_endtime(self, stn_event, t_ind, is_origin_stn):
        len_sched = len(self.sched[self.next_event_tr_id])
        min_endtime = pd.Timestamp('2100-01-05 22:50:00')
        print('inside the get_min_edntime function')
        _arr = self.tr_next_event.tr_sched_act[stn_event.name][0]
        _dep = self.tr_next_event.tr_sched_act[stn_event.name][1]
        same_arr_dep = _arr == _dep
        if is_origin_stn:
            next_stn = self.sched[self.next_event_tr_id][t_ind + 2]
            curr_stn = self.sched[self.next_event_tr_id][t_ind - 1]
            out_blsec = self.outgoing_blsec_name(curr_stn, next_stn)
            for j in stn_event.tracks:
                print(f'station line {j}', stn_event.tracks[j][3], stn_event.tracks[j][5])
                if self.tr_next_event.tr_type == 'p' and (not same_arr_dep) and (stn_event.tracks[j][1] == 0):
                    continue
                if out_blsec is None:
                    continue
                next_conn = out_blsec + '_' + str(j)
                print('origin station, next outgoing connection could be ', next_conn)
                if next_conn in stn_event.connections and isinstance(stn_event.tracks[j][3], pd.Timestamp) and (min_endtime > stn_event.tracks[j][3]):
                    min_endtime = stn_event.tracks[j][3]
                    print(f'min_endtime is {min_endtime}')
            print('\n station line becomes free at: ', min_endtime)
            return min_endtime
        curr_blsec_name = self.blsec_t.name
        print('\n current block section under consideration: ', curr_blsec_name)
        if t_ind == len_sched - 2:
            for j in stn_event.tracks:
                print(f'station line {j}', stn_event.tracks[j][3], stn_event.tracks[j][5])
                if self.tr_next_event.tr_type == 'p' and (not same_arr_dep) and (stn_event.tracks[j][1] == 0):
                    continue
                conn_key = curr_blsec_name + '_' + str(j)
                if conn_key in stn_event.connections and min_endtime > stn_event.tracks[j][3]:
                    min_endtime = stn_event.tracks[j][3]
            print('\n station line becomes free at: ', min_endtime)
            return min_endtime
        next_stn = self.sched[self.next_event_tr_id][t_ind + 2]
        curr_stn = self.sched[self.next_event_tr_id][t_ind - 1]
        out_blsec = self.outgoing_blsec_name(curr_stn, next_stn)
        print('outgoing could be ', out_blsec)
        for j in stn_event.tracks:
            print(f'station line {j}', stn_event.tracks[j][3], stn_event.tracks[j][5])
            if self.tr_next_event.tr_type == 'p' and (not same_arr_dep) and (stn_event.tracks[j][1] == 0):
                continue
            if out_blsec is None:
                continue
            next_conn = out_blsec + '_' + str(j)
            conn_key = curr_blsec_name + '_' + str(j)
            if conn_key in stn_event.connections and next_conn in stn_event.connections and isinstance(stn_event.tracks[j][3], pd.Timestamp) and (min_endtime > stn_event.tracks[j][3]):
                min_endtime = stn_event.tracks[j][3]
        print('\n station line becomes free at: ', min_endtime)
        return min_endtime

    def get_queue_end_time(self, blsec):
        if len(blsec.blsec_queue) > 0:
            end_times = [blsec.blsec_queue[i] for i in range(5, len(blsec.blsec_queue), 6) if isinstance(blsec.blsec_queue[i], pd.Timestamp)]
            if end_times:
                return max(end_times)
        if len(blsec.autoblsec_list) > 0:
            return blsec.autoblsec_list[-1][4]
        if blsec.occ_ind == 1:
            return blsec.occ_end
        return pd.Timestamp('1900-01-01 00:00:00')

    def get_train_stnline_for_arrival_delay(self, stns_event, train_name):
        for stn_line in stns_event[1].tracks:
            print(stn_line)
            if stns_event[1].tracks[stn_line][5] == train_name:
                return stn_line

    def get_train_stnline_for_departure_delay(self, stns_event, train_name):
        for stn_line in stns_event[0].tracks:
            print(stn_line)
            if stns_event[0].tracks[stn_line][5] == train_name:
                return stn_line

    def outgoing_blsec_name(self, a, b):
        base = self.conn_base(a, b)
        base_alt = self.conn_base(b, a)
        east_bound = self.station_longitudes[b] >= self.station_longitudes[a]
        wanted = 'dn' if east_bound else 'up'
        candidates = [x for x in self.blocksections_list if x.name.startswith(base + '_') or x.name.startswith(base_alt + '_')]
        for x in candidates:
            if x.dir_mvmt.startswith(wanted):
                return x.name
        for x in candidates:
            if x.dir_mvmt.startswith('mid'):
                return x.name
        return None

    # stn_line_assign was here -- moved to Station.assign_line (domain/station.py) as
    # part of docs/event-manager-design.md stage 2. See that method's docstring for the
    # translation notes; verified via a before/after total_schedule diff across 6
    # scenarios (git history has the original if it's ever needed for reference).

    def train_direction(self, t, current_stn):
        stns = list(t.tr_sched_act.keys())
        if current_stn not in stns:
            return None
        idx = stns.index(current_stn)
        if idx + 1 >= len(stns):
            return None
        nxt = stns[idx + 1]
        return 1 if self.station_longitudes[nxt] > self.station_longitudes[current_stn] else 0