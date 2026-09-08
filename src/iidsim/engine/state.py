"""Per-run simulation state, set up once in __init__ -- everything the other mixins (resolve/priority/randomness/events) and run() read/write via self.X. See docs/restructure-notes.md for how this was derived (Python's own co_freevars, not guesswork)."""

# import json
# import time
import numpy as np
import pandas as pd
# from pandas import Timestamp
# from scipy import stats as _halt_dev_stats
# from openpyxl.styles import Alignment, Font
import iidsim.network as _network
from iidsim.network import routes
from iidsim import schedules
from iidsim.data import geography, halt_deviation, timing
from iidsim.domain import Segment
# from iidsim.reporting.chart import plot_railway_chart
# from iidsim.reporting.extract import filter_df_by_date_window, get_formatted_data_from_df

class SimulationState:

    def __init__(self, corridor_dataset, network_section, *, trains_override=None, output_dir='output_files', start_dt_mode='planned', start_dt_manual=None, start_dt_buffer_minutes=10, chart_duration_hrs=23, headway_distance=3.6, goods_max_priority_wait_hours=20, autoblock_stations=('alm', 'kuk', 'vzm'), use_halt_deviation=True, use_speed_randomness=True, halt_deviation_seed=1234, speed_randomness_seed=1234, use_event_manager=True):
        # use_event_manager: the heap-based event selection from
        # docs/event-manager-design.md (stage 0), default since it was verified to
        # reproduce build_event_list()'s output exactly (tests/test_event_manager.py)
        # while running measurably faster. Pass False to fall back to the original
        # build_event_list() + linear min-scan path.
        self.USE_EVENT_MANAGER = use_event_manager
        self.chart_duration_hrs = chart_duration_hrs
        self.headway_distance = headway_distance
        self.autoblock_stations = autoblock_stations
        '''Run one end-to-end simulation and write the Excel report, time-distance
            chart PDF, and animator JSON for `corridor_dataset` on `network_section`.
            
            corridor_dataset: a name from iidsim.schedules.available_corridors(), e.g.
            'p_g_sprd_vzm_2days' -- replaces the old hardcoded per-corridor import. Still
            used to derive output filenames even when `trains_override` is given.
            network_section: one of 'psa_ktv', 'sprd_vzm', 'krdl_ktv' -- which corridor's
            station order / segment distances to use for the output chart.
            
            trains_override: optional list[iidsim.domain.train] to simulate directly instead of
            loading `corridor_dataset` from iidsim.schedules -- for synthetic/targeted test
            scenarios built against the real network (see tests/scenarios.py).
            
            Returns a dict with the three output file paths plus the in-memory
            total_schedule and trains the run produced.'''
        np.random.seed(1234)
        self.stations_list = _network.stations_list
        self.blocksections_list = _network.blocksections_list
        self.trains = trains_override if trains_override is not None else schedules.load_trains(corridor_dataset)
        self.trains_by_id = {}
        for _tr in self.trains:
            self.trains_by_id.setdefault(_tr.train_id, _tr)
        self.trains_by_instance_id = {f'{_tr.train_id}_{_tr.instance_index}': _tr for _tr in self.trains}
        self.stations_by_name = {s.name: s for s in self.stations_list}
        self.station_longitudes = geography.station_longitudes()
        self.blsec_lookup = {b.name: b for b in self.blocksections_list}
        # {'stn_west_stn_east': [block_sec, ...]} -- every block section whose name is
        # that base plus a '_dirsuffix' (dn1/up1/mid1/mid2), grouped so blsec_id() (and
        # any other station-pair candidate lookup) doesn't need to linear-scan the whole
        # network for every call. Station codes never contain '_', so stripping a name's
        # last '_'-segment always recovers exactly the base conn_base() would compute for
        # that pair -- the same assumption BlockSection.find_free_sibling() already
        # relies on. Preserves blocksections_list's original order within each bucket,
        # since a few callers depend on which candidate comes first.
        self.blsec_by_pair = {}
        for b in self.blocksections_list:
            base = '_'.join(b.name.split('_')[:-1])
            self.blsec_by_pair.setdefault(base, []).append(b)
        # {station_name: [block_sec, ...]} -- every block section touching that station
        # as either endpoint, for find_stn3() ("what's the next station beyond this
        # one") which needs to search by single station, not by pair. Same order
        # guarantee as blsec_by_pair.
        self.blsec_by_station = {}
        for b in self.blocksections_list:
            self.blsec_by_station.setdefault(b.stn_west.name, []).append(b)
            self.blsec_by_station.setdefault(b.stn_east.name, []).append(b)
        # {'stn_west_stn_east': Segment} -- one Segment per station pair, wrapping
        # the same line objects already grouped in blsec_by_pair. Purely additive:
        # nothing reads self.segments_by_pair yet (see docs discussion on the
        # Segment redesign) -- this just gives that grouping a name and a
        # direction-aware query method (Segment.lines_for_direction) instead of
        # leaving it as an anonymous index, without changing how any existing line
        # object behaves. Named segments_by_pair, not segments -- self.segments is
        # already taken below (network_section's chart station-pair distances).
        # stn_up/stn_down come from routes.branch_order() (the per-branch
        # "sequence from headquarters" lists) -- independent of the
        # longitude-derived stn_west/stn_east above. None/None for a pair no
        # branch list covers (harmless; direction_of_travel() just refuses to
        # guess for that segment rather than raising here).
        _branch_order = routes.branch_order()
        self.segments_by_pair = {}
        for base, lines in self.blsec_by_pair.items():
            up_down = _branch_order.get(frozenset((lines[0].stn_west.name, lines[0].stn_east.name)))
            stn_up, stn_down = up_down if up_down is not None else (None, None)
            self.segments_by_pair[base] = Segment(base, lines, stn_up=stn_up, stn_down=stn_down)
        if use_halt_deviation:
            self.halt_dev_fits_g = halt_deviation.fits_for('g')
            self.halt_dev_fits_p = halt_deviation.fits_for('p')
            self.station_max_g = halt_deviation.station_max_for('g')
            self.station_max_p = halt_deviation.station_max_for('p')
        else:
            self.halt_dev_fits_g = self.halt_dev_fits_p = self.station_max_g = self.station_max_p = {}
        if use_speed_randomness:
            self._crossing = timing.crossing_time_distributions()
            self.g_times = self._crossing['g']
            self.p_times = self._crossing['p']
        else:
            self.g_times = self.p_times = {}
        self.USE_HALT_DEVIATION = use_halt_deviation
        self.USE_SPEED_RANDOMNESS = use_speed_randomness
        self.SPEED_RANDOMNESS_SEED = speed_randomness_seed
        self._speed_rand_rng = np.random.default_rng(self.SPEED_RANDOMNESS_SEED)
        self._corridors = geography.corridors()
        self.station_order, self.segments = (self._corridors[network_section]['order'], self._corridors[network_section]['segments'])
        self.block_section_distances = geography.block_section_distances()
        self.chart_filename = f'{output_dir}/{corridor_dataset}_time_distance_chart.pdf'
        self.excel_filename = f'{output_dir}/{corridor_dataset}.xlsx'
        self.animator = f'{output_dir}/{corridor_dataset}_animator.json'
        self.GOODS_MAX_PRIORITY_WAIT = pd.Timedelta(hours=goods_max_priority_wait_hours)
        self.autoblock_stations = list(self.autoblock_stations)
        self.stn_line_occ_name = None
        self.previous_train_type = None
        self.prev_blsec_obj = None
        self.total_schedule = {}
        for tr in self.trains:
            self.tr_instance_id = tr.train_id + '_' + str(tr.instance_index)
            self.total_schedule[self.tr_instance_id] = {}
            self.total_schedule[self.tr_instance_id]['planned'] = [[tr.tr_type]]
            self.total_schedule[self.tr_instance_id]['simulated'] = [[tr.tr_type]]
            self.total_schedule[self.tr_instance_id]['actual'] = [[tr.tr_type]]
        for tr in self.trains:
            self.tr_instance_id = tr.train_id + '_' + str(tr.instance_index)
            for station_name in tr.tr_schedule:
                self.total_schedule[self.tr_instance_id]['planned'].append([station_name])
                self.total_schedule[self.tr_instance_id]['planned'].append([tr.tr_schedule[station_name][0]])
                self.total_schedule[self.tr_instance_id]['planned'].append([tr.tr_schedule[station_name][1]])
            for station_name in tr.tr_real_schedule:
                self.total_schedule[self.tr_instance_id]['actual'].append([station_name])
                self.total_schedule[self.tr_instance_id]['actual'].append([tr.tr_real_schedule[station_name][0]])
                self.total_schedule[self.tr_instance_id]['actual'].append([tr.tr_real_schedule[station_name][1]])
        self.big_time_value = pd.Timestamp('2100-06-01 00:00:00')
        if start_dt_mode == 'manual':
            self.start_dt = start_dt_manual
        elif start_dt_mode == 'planned':
            self.start_dt = self.compute_start_dt(self.trains, buffer_minutes=start_dt_buffer_minutes)
        else:
            raise ValueError(f'unknown start_dt_mode: {start_dt_mode}')
        print(f'start_dt ({start_dt_mode}): {self.start_dt}')
        self.sched = {}
        self.sched_act = {}
        for tr in self.trains:
            self.tr_sched = []
            self.tr_sched_name = tr.train_id + '_' + str(tr.instance_index)
            self.sched[self.tr_sched_name] = self.tr_sched
            for station_name in tr.tr_schedule:
                self.sched[self.tr_sched_name].append(station_name)
                self.sched[self.tr_sched_name].append(tr.tr_schedule[station_name][0])
                self.sched[self.tr_sched_name].append(tr.tr_schedule[station_name][1])
        self.sched_act = {k: list(v) for k, v in self.sched.items()}
        self.given_sched = {k: list(v) for k, v in self.sched.items()}
        self.HALT_DEVIATION_SEED = 1234
        self._halt_dev_rng = np.random.default_rng(self.HALT_DEVIATION_SEED)
        self.exec_sim = 0
        self.t_max = self.term_crit_calc()
        self.t = pd.Timestamp('2020-01-05 22:50:00')
        print('\n time at which simulation terminates: ', self.t_max)
        import time
        self.start_time = time.time()