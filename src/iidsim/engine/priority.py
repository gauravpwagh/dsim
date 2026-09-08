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
        return True

    def get_pass_train_stnline_endtimes(self, t, next_event_tr_id):
        stn_lines = []
        for stn_line in self.stns_event[0].tracks:
            conn_key = self.blsec_t.name + '_' + str(stn_line)
            if conn_key in self.stns_event[0].connections:
                stn_lines.append(conn_key.split('_')[-1])
        current_train_dir = self.train_direction(self.tr_next_event, self.stns_event[0].name)
        pass_train_stnline_endtimes = []
        for stn_line in stn_lines:
            try:
                tr_info = self.stns_event[0].tracks[stn_line]
            except Exception:
                continue
            if not isinstance(tr_info, (list, tuple)):
                continue
            occ_train_id = tr_info[5] if len(tr_info) > 5 else None
            if occ_train_id is None:
                continue
            occ_train_obj = self.trains_by_id.get(occ_train_id)
            occ_type = getattr(occ_train_obj, 'tr_type', None) if occ_train_obj is not None else None
            if occ_type == 'p':
                occ_train_dir = self.train_direction(occ_train_obj, self.stns_event[0].name)
                if occ_train_dir is None or occ_train_dir != current_train_dir:
                    continue
                end_time = tr_info[3] if len(tr_info) > 3 else None
                if isinstance(end_time, pd.Timestamp) and end_time >= t:
                    pass_train_stnline_endtimes.append(end_time)
        if len(pass_train_stnline_endtimes) > 0:
            max_endtime = max([endtime for endtime in pass_train_stnline_endtimes if isinstance(endtime, pd.Timestamp) and endtime > t])
            return max_endtime
        else:
            return None

    def get_prev_blsec_obj(self, t_ind, next_event_tr_id):
        if t_ind - 5 < 0:
            return None
        previous_stn = self.sched_act[next_event_tr_id][t_ind - 5]
        curr_stn = self.stns_event[0].name
        prev_base = self.conn_base(previous_stn, curr_stn)
        wanted = self.direction_of_travel(previous_stn, curr_stn)
        prev_blsec_obj = next((b for b in self.blsec_by_pair.get(prev_base, []) if isinstance(b.dir_mvmt, str) and b.dir_mvmt.startswith(wanted)), None)
        return prev_blsec_obj

    def get_prev_pass_train_arr_time(self, t_ind, next_event_tr_id):
        prev_blsec_obj = self.get_prev_blsec_obj(t_ind, next_event_tr_id)
        if prev_blsec_obj is None:
            return None
        if prev_blsec_obj.occ_ind == 1:
            train_on_prev_blsec = prev_blsec_obj.occ_train
            train_on_prev_blsec = train_on_prev_blsec.split('_')[0]
            prev_train = self.trains_by_id.get(train_on_prev_blsec)
            if prev_train:
                previous_train_type = prev_train.tr_type
            else:
                previous_train_type = None
            if previous_train_type == 'p' and prev_blsec_obj.occ_ind == 1:
                previous_pass_train_arr_time = getattr(prev_blsec_obj, 'occ_end', None) or getattr(prev_blsec_obj, 'occ_end_time', None)
                return previous_pass_train_arr_time
            else:
                return None
        else:
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

    # update_blsec_queue_priority was here -- moved to BlockSection.update_queue_priority
    # (domain/block_section.py) as part of docs/event-manager-design.md stage 3b. See
    # that method's docstring for the translation notes; verified via a before/after
    # total_schedule diff (git history has the original if it's ever needed).