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

class EventsMixin:

    def build_event_list(self):
        event_list = []
        for instance_id in self.sched_act:
            pending_times = [v for v in self.sched_act[instance_id] if isinstance(v, str) == False and v < pd.Timestamp('2100-06-01 22:50:00')]
            if len(pending_times) > 0:
                next_time = min(pending_times)
                next_time_idx = self.sched_act[instance_id].index(next_time)
                if isinstance(self.sched_act[instance_id][next_time_idx - 1], str):
                    event_type = 'a'
                elif isinstance(self.sched_act[instance_id][next_time_idx - 1], str) == False:
                    event_type = 'd'
                underscore_idx = instance_id.index('_')
                train_id = instance_id[0:underscore_idx]
                event_list.append(train_id)
                event_list.append(next_time)
                event_list.append(event_type)
                event_list.append(instance_id)
            else:
                'do nothing'
        return event_list

    def compute_start_dt(self, trains, buffer_minutes):
        candidates = [self.get_earliest_time(tr.tr_schedule) for tr in trains]
        candidates = [c for c in candidates if c is not None]
        if not candidates:
            raise ValueError('no valid timestamps found in planned schedules to derive start_dt')
        return min(candidates) + pd.Timedelta(minutes=buffer_minutes)

    def get_earliest_time(self, schedule_dict):
        times = []
        for stn, times_pair in schedule_dict.items():
            for t in times_pair:
                if isinstance(t, pd.Timestamp) and t < self.big_time_value:
                    times.append(t)
        return min(times) if times else None

    def get_station_event(self, t, next_event_tr_id, next_event_type, stations_list):
        len_sched = len(self.sched_act[next_event_tr_id])
        a = self.sched_act[next_event_tr_id].index(t)
        next_event_stn_up1 = ''
        next_event_stn_mid1 = ''
        if next_event_type == 'a':
            next_event_stn_up1 = self.sched_act[next_event_tr_id][a - 1]
            if a > 1:
                next_event_stn_mid1 = self.sched_act[next_event_tr_id][a - 4]
            else:
                'do nothing'
        else:
            next_event_stn_up1 = self.sched_act[next_event_tr_id][a - 2]
            if a < len_sched - 1:
                next_event_stn_mid1 = self.sched_act[next_event_tr_id][a + 1]
            else:
                'do nothing'
        stns = []
        stn_names = []
        for station in stations_list:
            if station.name == next_event_stn_up1:
                stns.append(station)
                stn_names.append(station.name)
        for station in stations_list:
            if next_event_stn_mid1 != '':
                if station.name == next_event_stn_mid1:
                    stns.append(station)
                    stn_names.append(station.name)
        return stns

    def sched_updt(self, t_updt_start, t_ind, next_event_tr_id):
        num_updt = self.sched_act[next_event_tr_id][t_ind:]
        updt_inc = t_updt_start - self.sched_act[next_event_tr_id][t_ind]
        for offset in range(len(num_updt)):
            if isinstance(self.sched_act[next_event_tr_id][t_ind + offset], str):
                'do nothing'
            else:
                self.sched_act[next_event_tr_id][t_ind + offset] = self.sched_act[next_event_tr_id][t_ind + offset] + updt_inc

    def term_crit_calc(self):
        latest_pending_times = []
        for instance_id in self.sched_act:
            pending_times = [v for v in self.sched_act[instance_id] if isinstance(v, str) == False and v < pd.Timestamp('2100-06-01 22:50:00')]
            if len(pending_times) > 0:
                latest_pending_times.append(max(pending_times))
            else:
                latest_pending_times.append(pd.Timestamp('1900-01-01 00:00:00'))
        t_max = max(latest_pending_times)
        return t_max

    def tr_sched_updt(self, t, next_event_type):
        if next_event_type == 'a':
            self.tr_next_event.tr_sched_act[self.stns_event[0].name][0] = t
        else:
            self.tr_next_event.tr_sched_act[self.stns_event[0].name][1] = t