"""Part of the simulation engine -- see docs/restructure-notes.md and docs/simulation-engine.md. Mixed into Simulation (engine/run.py); every method here reads/writes shared per-run state via self.X (see SimulationState in engine/state.py)."""

import json
import time
import numpy as np
import pandas as pd
from pandas import Timestamp
from scipy import stats as _halt_dev_stats
from openpyxl.styles import Alignment, Font
import iidsim.network as _network
from iidsim import schedules
from iidsim.data import geography, halt_deviation, timing
from iidsim.reporting.chart import plot_railway_chart
from iidsim.reporting.extract import filter_df_by_date_window, get_formatted_data_from_df

class PriorityMixin:

    def autoblsec_check(self):
        if self.stns_event[0].name in self.autoblock_stations and self.stns_event[1].name in self.autoblock_stations:
            return True
        else:
            return False

    def check_if_all_goods(self, t_ind, next_event_tr_id):
        stn_lines = []
        for stn_line in self.stns_event[0].tracks:
            conn_key = self.blsec_t.name + '_' + str(stn_line)
            if conn_key in self.stns_event[0].connections:
                stn_lines.append(conn_key.split('_')[-1])
        for stn_line in stn_lines:
            try:
                tr_info = self.stns_event[0].tracks[stn_line]
            except Exception:
                continue
            if not isinstance(tr_info, (list, tuple)):
                continue
            occ_train_id = tr_info[5] if len(tr_info) > 5 else None
            if not occ_train_id:
                continue
            occ_train_obj = self.trains_by_id.get(occ_train_id)
            occ_type = getattr(occ_train_obj, 'tr_type', None) if occ_train_obj is not None else None
            if occ_type == 'g':
                continue
            else:
                return False
        print('Since all trains on station are goods and prev blsec has passenger we would have to depart this gooods train')
        return True

    def get_pass_train_stnline_endtimes(self, t, next_event_tr_id):
        stn_lines = []
        for stn_line in self.stns_event[0].tracks:
            conn_key = self.blsec_t.name + '_' + str(stn_line)
            if conn_key in self.stns_event[0].connections:
                stn_lines.append(conn_key.split('_')[-1])
        print('list of stn lines', stn_lines)
        print('goods train timetable is', self.sched_act[next_event_tr_id])
        current_train_dir = self.train_direction(self.tr_next_event, self.stns_event[0].name)
        print('current departing train direction is', current_train_dir)
        pass_train_stnline_endtimes = []
        for stn_line in stn_lines:
            try:
                tr_info = self.stns_event[0].tracks[stn_line]
            except Exception:
                continue
            if not isinstance(tr_info, (list, tuple)):
                continue
            print('tr info for station line ', stn_line, ' is ', tr_info)
            occ_train_id = tr_info[5] if len(tr_info) > 5 else None
            if occ_train_id is None:
                continue
            print('occ train id is', occ_train_id)
            occ_train_obj = self.trains_by_id.get(occ_train_id)
            occ_type = getattr(occ_train_obj, 'tr_type', None) if occ_train_obj is not None else None
            if occ_type == 'p':
                occ_train_dir = self.train_direction(occ_train_obj, self.stns_event[0].name)
                print('occ passenger train', occ_train_id, 'direction is', occ_train_dir)
                if occ_train_dir is None or occ_train_dir != current_train_dir:
                    print('skipping', occ_train_id, '-- destination station or opposite direction, no conflict with', self.blsec_t.name)
                    continue
                print('occ type is', occ_type)
                print('tr info is', tr_info)
                print('train id is', occ_train_id)
                end_time = tr_info[3] if len(tr_info) > 3 else None
                if isinstance(end_time, pd.Timestamp) and end_time >= t:
                    pass_train_stnline_endtimes.append(end_time)
        if len(pass_train_stnline_endtimes) > 0:
            max_endtime = max([i for i in pass_train_stnline_endtimes if isinstance(i, pd.Timestamp) and i > t])
            print('list of endtimes here is', pass_train_stnline_endtimes)
            print('\n station line ', self.stn_line_occ_name, 'at station ', self.stns_event[0].name, 'will be free starting at t = ', max_endtime + pd.Timedelta(minutes=1))
            print('given stn line is ', self.stn_line_occ_name)
            print('curent station is', self.stns_event[0].name, self.stns_event[1].name)
            return max_endtime
        else:
            return None

    def get_prev_blsec_obj(self, t_ind, next_event_tr_id):
        if t_ind - 5 < 0:
            print('previous block section is  None  (train at origin)')
            return None
        previous_stn = self.sched_act[next_event_tr_id][t_ind - 5]
        curr_stn = self.stns_event[0].name
        prev_base = self.conn_base(previous_stn, curr_stn)
        east_bound = self.station_longitudes[curr_stn] >= self.station_longitudes[previous_stn]
        wanted = 'dn' if east_bound else 'up'
        prev_blsec_obj = next((b for b in self.blocksections_list if b.name.startswith(prev_base + '_') and isinstance(b.dir_mvmt, str) and b.dir_mvmt.startswith(wanted)), None)
        print('previous block section is ', prev_blsec_obj.name if prev_blsec_obj else None)
        return prev_blsec_obj

    def get_prev_pass_train_arr_time(self, t_ind, next_event_tr_id):
        prev_blsec_obj = self.get_prev_blsec_obj(t_ind, next_event_tr_id)
        if prev_blsec_obj is None:
            return None
        if prev_blsec_obj.occ_ind == 1:
            train_on_prev_blsec = prev_blsec_obj.occ_train
            train_on_prev_blsec = train_on_prev_blsec.split('_')[0]
            print('train on previous block section is ', train_on_prev_blsec)
            prev_train = self.trains_by_id.get(train_on_prev_blsec)
            print('previous train object is ', prev_train)
            if prev_train:
                previous_train_type = prev_train.tr_type
            else:
                previous_train_type = None
            print('previous train type on previous block section is ', previous_train_type)
            if previous_train_type == 'p' and prev_blsec_obj.occ_ind == 1:
                previous_pass_train_arr_time = getattr(prev_blsec_obj, 'occ_end', None) or getattr(prev_blsec_obj, 'occ_end_time', None)
                previous_pass_train_id = getattr(prev_blsec_obj, 'occ_train', None)
                print('previous passenger train id is on previous block section is ', previous_pass_train_id)
                print('previous passenger train arrival time is ', previous_pass_train_arr_time)
                return previous_pass_train_arr_time
            else:
                return None
        else:
            print('Previous blsec is empty')
            return None

    def goods_delay_due_to_passenger(self, sched_act, t, t_ind, next_event_tr_id):
        max_endtime_among_stn_trains = self.get_pass_train_stnline_endtimes(t, next_event_tr_id)
        prev_pass_train_arr_time = self.get_prev_pass_train_arr_time(t_ind, next_event_tr_id)
        if not max_endtime_among_stn_trains and (not prev_pass_train_arr_time):
            return sched_act[next_event_tr_id][t_ind]
        elif max_endtime_among_stn_trains and prev_pass_train_arr_time:
            updt_dep_time = max(max_endtime_among_stn_trains, prev_pass_train_arr_time)
            return updt_dep_time
        elif max_endtime_among_stn_trains and (not prev_pass_train_arr_time):
            updt_dep_time = max_endtime_among_stn_trains
            return updt_dep_time
        else:
            updt_dep_time = prev_pass_train_arr_time
            return updt_dep_time

    def update_blsec_queue_priority(self, blsec, train_type, next_event_tr_id):
        """
        Ensures all passenger trains are at the front of the queue and all goods trains at the end.
        Updates occ_start/occ_end and schedules for goods trains if needed.
        """
        if not blsec.blsec_queue:
            return
        queue = [blsec.blsec_queue[i:i + 6] for i in range(0, len(blsec.blsec_queue), 6)]
        passenger_trains = [q for q in queue if q[2] == 'p']
        goods_trains = [q for q in queue if q[2] == 'g']
        queue = passenger_trains + goods_trains
        if passenger_trains and goods_trains and (train_type == 'p'):
            current_train_start_time = goods_trains[0][4]
            time_taken = passenger_trains[-1][5] - passenger_trains[-1][4]
            current_train_end_time = current_train_start_time + time_taken
            current_train_ind = passenger_trains[-1][3]
            self.sched_updt(current_train_start_time, current_train_ind, next_event_tr_id)
            stn_line = self.get_train_stnline_for_departure_delay(self.stns_event, passenger_trains[-1][1])
            self.stns_event[0].set_occupancy_updt(stn_line, passenger_trains[-1][0])
            passenger_trains[-1][4] = current_train_start_time
            passenger_trains[-1][5] = current_train_end_time
            prev_end = current_train_end_time + pd.Timedelta(minutes=1)
            for gq in goods_trains:
                duration = gq[5] - gq[4]
                gq[4] = max(prev_end, gq[4]) + pd.Timedelta(minutes=1)
                gq[5] = gq[4] + duration
                tr_id = gq[0]
                t_ind_queue = gq[3]
                self.sched_updt(gq[4], t_ind_queue, tr_id)
                stn_line_stn0 = self.get_train_stnline_for_departure_delay(self.stns_event, gq[1])
                stn_line_stn1 = self.get_train_stnline_for_arrival_delay(self.stns_event, gq[1])
                print('gq[1] value is ', gq[1])
                print('gq value is ', gq)
                print('inside goods train upt function; get_train_stnline stn0:', stn_line_stn0, 'stn1:', stn_line_stn1)
                if stn_line_stn0 is not None:
                    self.stns_event[0].set_occupancy_updt(stn_line_stn0, gq[5])
                elif stn_line_stn1 is not None:
                    self.stns_event[1].set_occupancy_updt(stn_line_stn1, gq[5])
                else:
                    print(f'[goods train update] train {gq[1]} not found at either station, skipping stn line update')
                prev_end = gq[5]
            blsec.blsec_queue = [item for sublist in queue for item in sublist]
        else:
            'do nothing'