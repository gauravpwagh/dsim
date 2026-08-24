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
        stn_start = self.stations_by_name[stn1]
        stn_end = self.stations_by_name[stn2]
        if stn_start.longitude - stn_end.longitude > 0:
            train_dir = 'up'
        else:
            train_dir = 'dn'
        # conn_base() always returns the same west_east string regardless of argument
        # order (it re-sorts by longitude internally), so conn_base(stn2, stn1) here
        # would just recompute the identical string -- no need for a second lookup.
        blsec_base = self.conn_base(stn1, stn2)
        blsec_list = [
            blsec_candidate for blsec_candidate in self.blsec_by_pair.get(blsec_base, [])
            if blsec_candidate.dir_mvmt[0:2] == train_dir or blsec_candidate.dir_mvmt[0:3] == 'mid'
        ]
        if self.next_event_type == 'a' and len(self.stns_event) > 1:
            for blsec in blsec_list:
                if blsec.occ_ind == 1 and blsec.occ_train == self.next_event_tr_id:
                    return blsec
                check_auto = self.autoblsec_check()
                if check_auto:
                    if blsec.autoblsec_list and self.next_event_tr_id == blsec.autoblsec_list[0][0]:
                        return blsec
        stn_line_occ_name = ''
        for track_name in stn_start.tracks:
            if stn_start.tracks[track_name][0] == 1 and stn_start.tracks[track_name][5] == self.tr_next_event.train_id:
                stn_line_occ_name = track_name
                break
        if stn_line_occ_name:
            blsec_list = [b for b in blsec_list if b.name + '_' + stn_line_occ_name in stn_start.connections]
            if not blsec_list:
                raise ValueError(f'blsec_id({stn1!r}, {stn2!r}): station line {stn_line_occ_name!r} is not connected to any candidate block section')
        if self.next_event_type == 'd':
            if len(blsec_list) == 1:
                return blsec_list[0]
            for blsec in blsec_list:
                if self.next_event_tr_id in blsec.blsec_queue[0::6]:
                    if blsec.occ_ind == 0:
                        return blsec
                    sib = blsec.find_free_sibling(self.blsec_lookup, stn_start, stn_line_occ_name, train_dir=train_dir)
                    if sib is not None:
                        t_index = self.sched_act[self.next_event_tr_id].index(self.t)
                        dep_list = [self.next_event_tr_id, self.next_event_train, self.tr_next_event.tr_type, t_index, self.t, self.sched_act[self.next_event_tr_id][t_index + 2]]
                        blsec.queue_remove(dep_list)
                        return sib
                    return blsec
        end_times = []
        if len(blsec_list) > 1:
            for blsec in blsec_list:
                blsec_end_time = self.get_queue_end_time(blsec)
                end_times.append((blsec, blsec_end_time))
            free_time = pd.Timestamp('1900-01-01 00:00:00')
            if all((t == free_time for _, t in end_times)):
                preferred = [(b, t) for b, t in end_times if b.dir_mvmt.startswith(('up', 'dn'))]
                if preferred:
                    selected_blsec = preferred[0][0]
                else:
                    selected_blsec = end_times[0][0]
            else:
                selected_blsec = min(end_times, key=lambda x: x[1])[0]
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
            for blsec in self.blocksections_list:
                if blsec.name.startswith(curr_blsec):
                    count_curr_blsec += 1
            for track_name, vals in self.stns_event[1].tracks.items():
                train = vals[5]
                train_dir = None
                _t = self.trains_by_id.get(train)
                if _t is not None:
                    train_dir = self.train_direction(_t, self.stns_event[1].name)
                next_stn_occ[track_name] = [vals[0], vals[3], train_dir, vals[5]]
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
            if stn3 != '':
                next_blsec_name = self.conn_base(stn2, stn3)
                for blsec in self.blocksections_list:
                    if blsec.name.startswith(next_blsec_name):
                        count_next_blsec += 1
                        blsec_tr_dir = None
                        blsec_occ_train_name = blsec.occ_train.split('_')[0] if blsec.occ_train else None
                        _t = self.trains_by_id.get(blsec_occ_train_name)
                        if _t is not None:
                            blsec_tr_dir = self.train_direction(_t, blsec.stn_west.name)
                        next_blsec_list.append([blsec, blsec_tr_dir])
                        next_blsec_list_names.append([blsec.name, blsec_tr_dir])
            else:
                count_next_blsec = count_curr_blsec
        return [dn_dir_stn_count, up_dir_stn_count, next_stn_line_min_endtimes, count_next_blsec, count_curr_blsec, next_blsec_list]

    def conn_base(self, stn_a, stn_b, dir_mvmt=None):
        w, e = (stn_a, stn_b) if self.station_longitudes[stn_a] <= self.station_longitudes[stn_b] else (stn_b, stn_a)
        return f'{w}_{e}_{dir_mvmt}' if dir_mvmt else f'{w}_{e}'

    def conn_exists(self, stn, stn_a, stn_b, dir_mvmt, line):
        """Return the real connection key (a_b or swapped b_a) present at `stn`, else None.
           Handles equal-longitude pairs where west/east ordering is ambiguous."""
        for base in (self.conn_base(stn_a, stn_b, dir_mvmt), self.conn_base(stn_b, stn_a, dir_mvmt)):
            key = base + '_' + str(line)
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
        _arr = self.tr_next_event.tr_sched_act[stn_event.name][0]
        _dep = self.tr_next_event.tr_sched_act[stn_event.name][1]
        same_arr_dep = _arr == _dep
        if is_origin_stn:
            next_stn = self.sched[self.next_event_tr_id][t_ind + 2]
            curr_stn = self.sched[self.next_event_tr_id][t_ind - 1]
            out_blsec = self.outgoing_blsec_name(curr_stn, next_stn)
            for track_name in stn_event.tracks:
                if self.tr_next_event.tr_type == 'p' and (not same_arr_dep) and (stn_event.tracks[track_name][1] == 0):
                    continue
                if out_blsec is None:
                    continue
                next_conn = out_blsec + '_' + str(track_name)
                if next_conn in stn_event.connections and isinstance(stn_event.tracks[track_name][3], pd.Timestamp) and (min_endtime > stn_event.tracks[track_name][3]):
                    min_endtime = stn_event.tracks[track_name][3]
            return min_endtime
        curr_blsec_name = self.blsec_t.name
        if t_ind == len_sched - 2:
            for track_name in stn_event.tracks:
                if self.tr_next_event.tr_type == 'p' and (not same_arr_dep) and (stn_event.tracks[track_name][1] == 0):
                    continue
                conn_key = curr_blsec_name + '_' + str(track_name)
                if conn_key in stn_event.connections and min_endtime > stn_event.tracks[track_name][3]:
                    min_endtime = stn_event.tracks[track_name][3]
            return min_endtime
        next_stn = self.sched[self.next_event_tr_id][t_ind + 2]
        curr_stn = self.sched[self.next_event_tr_id][t_ind - 1]
        out_blsec = self.outgoing_blsec_name(curr_stn, next_stn)
        for track_name in stn_event.tracks:
            if self.tr_next_event.tr_type == 'p' and (not same_arr_dep) and (stn_event.tracks[track_name][1] == 0):
                continue
            if out_blsec is None:
                continue
            next_conn = out_blsec + '_' + str(track_name)
            conn_key = curr_blsec_name + '_' + str(track_name)
            if conn_key in stn_event.connections and next_conn in stn_event.connections and isinstance(stn_event.tracks[track_name][3], pd.Timestamp) and (min_endtime > stn_event.tracks[track_name][3]):
                min_endtime = stn_event.tracks[track_name][3]
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
            if stns_event[1].tracks[stn_line][5] == train_name:
                return stn_line

    def get_train_stnline_for_departure_delay(self, stns_event, train_name):
        for stn_line in stns_event[0].tracks:
            if stns_event[0].tracks[stn_line][5] == train_name:
                return stn_line

    def outgoing_blsec_name(self, stn_a, stn_b):
        base = self.conn_base(stn_a, stn_b)
        base_alt = self.conn_base(stn_b, stn_a)
        east_bound = self.station_longitudes[stn_b] >= self.station_longitudes[stn_a]
        wanted = 'dn' if east_bound else 'up'
        candidates = [b for b in self.blocksections_list if b.name.startswith(base + '_') or b.name.startswith(base_alt + '_')]
        for blsec in candidates:
            if blsec.dir_mvmt.startswith(wanted):
                return blsec.name
        for blsec in candidates:
            if blsec.dir_mvmt.startswith('mid'):
                return blsec.name
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