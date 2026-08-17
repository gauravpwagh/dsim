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

class EventsMixin:

    def build_event_list(self):
        event_list = []
        for j in self.sched_act:
            b = [k for k in self.sched_act[j] if isinstance(k, str) == False and k < pd.Timestamp('2100-06-01 22:50:00')]
            if len(b) > 0:
                a = min(b)
                a_ind = self.sched_act[j].index(a)
                if isinstance(self.sched_act[j][a_ind - 1], str):
                    a_type = 'a'
                elif isinstance(self.sched_act[j][a_ind - 1], str) == False:
                    a_type = 'd'
                tr_num_ind = j.index('_')
                tr_name = j[0:tr_num_ind]
                event_list.append(tr_name)
                event_list.append(a)
                event_list.append(a_type)
                event_list.append(j)
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
        for j in stations_list:
            if j.name == next_event_stn_up1:
                stns.append(j)
                stn_names.append(j.name)
        for i in stations_list:
            if next_event_stn_mid1 != '':
                if i.name == next_event_stn_mid1:
                    stns.append(i)
                    stn_names.append(i.name)
        print('\n stations_list involved at time ', t, 'are ', stn_names)
        return stns

    def sched_updt(self, t_updt_start, t_ind, next_event_tr_id):
        num_updt = self.sched_act[next_event_tr_id][t_ind:]
        updt_inc = t_updt_start - self.sched_act[next_event_tr_id][t_ind]
        for j in range(len(num_updt)):
            if isinstance(self.sched_act[next_event_tr_id][t_ind + j], str):
                'do nothing'
            else:
                self.sched_act[next_event_tr_id][t_ind + j] = self.sched_act[next_event_tr_id][t_ind + j] + updt_inc

    def term_crit_calc(self):
        b = []
        for j in self.sched_act:
            c = [k for k in self.sched_act[j] if isinstance(k, str) == False and k < pd.Timestamp('2100-06-01 22:50:00')]
            if len(c) > 0:
                b.append(max(c))
            else:
                b.append(pd.Timestamp('1900-01-01 00:00:00'))
        t_max = max(b)
        return t_max

    def tr_sched_updt(self, t, next_event_type):
        if next_event_type == 'a':
            self.tr_next_event.tr_sched_act[self.stns_event[0].name][0] = t
        else:
            self.tr_next_event.tr_sched_act[self.stns_event[0].name][1] = t