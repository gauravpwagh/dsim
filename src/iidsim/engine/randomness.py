"""Part of the simulation engine -- see docs/restructure-notes.md and docs/simulation-engine.md. Mixed into Simulation (engine/run.py); every method here reads/writes shared per-run state via self.X (see SimulationState in engine/state.py)."""

# import json
# import time
import numpy as np
import pandas as pd
# from pandas import Timestamp
from scipy import stats as _halt_dev_stats
# from openpyxl.styles import Alignment, Font
# import iidsim.network as _network
# from iidsim import schedules
# from iidsim.data import geography, halt_deviation, timing
# from iidsim.reporting.chart import plot_railway_chart
# from iidsim.reporting.extract import filter_df_by_date_window, get_formatted_data_from_df

class RandomnessMixin:

    def _generate_halt_deviation(self, station, train_type, rng):
        """station: uppercase station code, 
            train_type: 'G' or 'P'. 
            Returns 0.0 if no fit exists for the station."""
        fit_dict = self.halt_dev_fits_g if train_type == 'G' else self.halt_dev_fits_p
        max_dict = self.station_max_g if train_type == 'G' else self.station_max_p
        fit = fit_dict.get(station)
        if fit is None:
            return 0.0
        value = self._sample_halt_dev(fit, rng)
        cap = max_dict.get(station)
        return min(value, float(cap)) if cap is not None else value

    def _sample_blsec_time(self, blsec_key, train_type, rng):
        times_dict = self.g_times if train_type == 'g' else self.p_times
        entry = times_dict.get('dn', {}).get(blsec_key) or times_dict.get('up', {}).get(blsec_key)
        if not entry:
            return None
        weights = np.array(entry['weights'], dtype=float)
        probs = weights / weights.sum()
        return rng.choice(entry['values'], p=probs)

    def _sample_halt_dev(self, fit, rng):
        """Draw one halt-deviation value (minutes) from a fitted per-station distribution."""
        if fit['type'] == 'empirical':
            return float(rng.choice(fit['data']))
        if rng.random() >= fit['p_zero']:
            dist = getattr(_halt_dev_stats, fit['dist'])
            draw = dist.rvs(*fit['params'], random_state=rng)
            return float(np.round(draw - 0.5 + fit['shift']))
        return 0.0

    def add_halt_randomness(self):
        if not self.USE_HALT_DEVIATION:
            return 0
        try:
            station = self.stns_event[0].name.upper()
            train_type = 'G' if self.tr_next_event.tr_type == 'g' else 'P'
        except Exception:
            return 0
        deviation_minutes = self._generate_halt_deviation(station, train_type, self._halt_dev_rng)
        return deviation_minutes

    def add_speed_randomness(self, base_speed):
        if not self.USE_SPEED_RANDOMNESS:
            return base_speed
        try:
            blsec_key = f'{self.stns_event[0].name.upper()}-{self.stns_event[1].name.upper()}'
            train_type = 'g' if self.tr_next_event.tr_type == 'g' else 'p'
        except Exception:
            return base_speed
        sampled_time_min = self._sample_blsec_time(blsec_key, train_type, self._speed_rand_rng)
        if not sampled_time_min or sampled_time_min <= 0:
            return base_speed
        return self.blsec_t.length * 60 / sampled_time_min

    def new_arr_by_speed_randomness(self, next_event_tr_id, t_ind):
        time_diff = self.sched_act[next_event_tr_id][t_ind + 2] - self.sched_act[next_event_tr_id][t_ind]
        time_diff_minutes = time_diff.total_seconds() / 60
        tr_dep_speed = self.blsec_t.length * 60 / time_diff_minutes
        t_blsec_end = self.blsec_t.length * 60 / tr_dep_speed
        t_blsec_end_int = int(np.ceil(t_blsec_end))
        t_blsec_end = pd.Timedelta(minutes=t_blsec_end_int)
        tr_dep_speed_mod = self.add_speed_randomness(tr_dep_speed)
        t_blsec_occ_end = self.blsec_t.length / tr_dep_speed_mod
        t_blsec_occ_end = t_blsec_occ_end * 60
        t_blsec_occ_end_int = int(np.ceil(t_blsec_occ_end))
        t_blsec_occ_end = pd.Timedelta(minutes=t_blsec_occ_end_int)
        new_arrival_time = self.t + t_blsec_occ_end
        new_arrival_time = new_arrival_time.replace(microsecond=0)
        original_arrival_time = self.sched_act[next_event_tr_id][t_ind + 2]
        time_change = new_arrival_time - original_arrival_time
        if time_change > pd.Timedelta(minutes=1):
            return [new_arrival_time, time_change]
        else:
            return [original_arrival_time]