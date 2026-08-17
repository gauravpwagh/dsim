"""Discrete-event railway simulation engine.

Lifted from the original top-level final_sim_sj_4aug.py script into a callable,
parameterized function during the src/ package restructure -- see
docs/simulation-engine.md for what the engine does, and
docs/restructure-notes.md for why this file is one large function rather than
split into smaller modules (short version: nearly every helper function here
reads and writes a shared set of "current event" variables -- sched_act,
stns_event, blsec_t, tr_next_event, next_event_type, t, ... -- and several of
those names are *also* reused as unrelated local parameter names in other
functions in this same file. A safe split requires either an AST-aware
refactoring tool or a full regression-test suite covering every branch
(autoblock, starvation override, sibling-redirect, platform fallback, ...),
neither of which exist yet -- see that doc for the recommended follow-up path.

This lift-and-shift is behavior-preserving: the event-loop body below is the
original script's logic verbatim (mechanically indented one level, with
`global` -> `nonlocal` since the helpers are now nested functions instead of
module-level ones), verified by diffing this module's output against the
original script's output for the same corridor/seed. Only the *configuration*
section immediately below was rewritten -- hardcoded corridor selection and
file paths became function parameters.
"""
import copy
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


def run_simulation(
    corridor_dataset,
    network_section,
    *,
    output_dir="output_files",
    start_dt_mode="planned",
    start_dt_manual=None,
    start_dt_buffer_minutes=10,
    chart_duration_hrs=23,
    headway_distance=3.6,
    goods_max_priority_wait_hours=20,
    autoblock_stations=("alm", "kuk", "vzm"),
    use_halt_deviation=True,
    use_speed_randomness=True,
    halt_deviation_seed=1234,
    speed_randomness_seed=1234,
):
    """Run one end-to-end simulation and write the Excel report, time-distance
    chart PDF, and animator JSON for `corridor_dataset` on `network_section`.

    corridor_dataset: a name from iidsim.schedules.available_corridors(), e.g.
        'p_g_sprd_vzm_2days' -- replaces the old hardcoded per-corridor import.
    network_section: one of 'psa_ktv', 'sprd_vzm', 'krdl_ktv' -- which corridor's
        station order / segment distances to use for the output chart.

    Returns a dict with the three output file paths plus the in-memory
    total_schedule and trains the run produced.
    """
    np.random.seed(1234)

    # local (not module-level) so nested functions below can `nonlocal` them --
    # nonlocal only reaches enclosing *function* scopes, never module globals.
    stations_list = _network.stations_list
    blocksections_list = _network.blocksections_list

    trains = schedules.load_trains(corridor_dataset)

    station_longitudes = geography.station_longitudes()
    blsec_lookup = {b.name: b for b in blocksections_list}

    #  halt-deviation model, fitted from real WAT halt-time data (see docs/data-files.md)
    halt_dev_fits_g = halt_deviation.fits_for('g')
    halt_dev_fits_p = halt_deviation.fits_for('p')
    station_max_g = halt_deviation.station_max_for('g')
    station_max_p = halt_deviation.station_max_for('p')
    _crossing = timing.crossing_time_distributions()
    g_times = _crossing['g']
    p_times = _crossing['p']

    # if set False; no halt deviation(randomness) is added to the halt time; the halt time is always equal to the scheduled halt time
    USE_HALT_DEVIATION = use_halt_deviation
    USE_SPEED_RANDOMNESS = use_speed_randomness
    SPEED_RANDOMNESS_SEED = speed_randomness_seed
    _speed_rand_rng = np.random.default_rng(SPEED_RANDOMNESS_SEED)

    _corridors = geography.corridors()
    station_order, segments = _corridors[network_section]['order'], _corridors[network_section]['segments']
    block_section_distances = geography.block_section_distances()

    chart_filename = f'{output_dir}/{corridor_dataset}_time_distance_chart.pdf'
    excel_filename = f'{output_dir}/{corridor_dataset}.xlsx'
    animator = f'{output_dir}/{corridor_dataset}_animator.json'

    # a goods train yields to passenger priority (goods_delay_due_to_passenger) every time it's
    # re-evaluated -- with continuous passenger traffic on a block section that check can find a
    # fresh reason to defer forever, so a goods train would never depart. Once it has been waiting
    # this long past its originally planned departure (given_sched, before any delay), it departs
    # on its next opportunity regardless of passenger occupancy, so it's guaranteed to eventually run.
    GOODS_MAX_PRIORITY_WAIT = pd.Timedelta(hours=goods_max_priority_wait_hours)
    autoblock_stations = list(autoblock_stations)

    # names written from nested functions via `nonlocal` below must already exist as
    # locals of this function -- these three are never assigned at the old script's
    # true top level, only inside resource_update_event, so pre-initialize them here.
    stn_line_occ_name = None
    previous_train_type = None
    prev_blsec_obj = None

    # initialize dictionary to store planned, simulated, and actual timetable
    # total_schedule stores the planned, simulated, and actual timetable for all trains, with train instance id
    # planned sched is filled in the beginning, simulated sched is updated after each simulation step,
    # actual sched (if available for the train) comes from real-world movement data via tr.tr_real_schedule
    total_schedule = {} 
    for tr in trains:
        tr_instance_id = tr.train_id + '_' + str(tr.instance_index)  # e.g. '13352_dn1', '13352_up1'
        total_schedule[tr_instance_id] = {}
        total_schedule[tr_instance_id]['planned'] = [[tr.tr_type]]
        total_schedule[tr_instance_id]['simulated'] = [[tr.tr_type]]
        total_schedule[tr_instance_id]['actual'] = [[tr.tr_type]]

    for tr in trains:
        tr_instance_id = tr.train_id + '_' + str(tr.instance_index)
        for j in tr.tr_schedule:
            total_schedule[tr_instance_id]['planned'].append([j])
            total_schedule[tr_instance_id]['planned'].append([tr.tr_schedule[j][0]])
            total_schedule[tr_instance_id]['planned'].append([tr.tr_schedule[j][1]])
        for j in tr.tr_real_schedule:
            total_schedule[tr_instance_id]['actual'].append([j])
            total_schedule[tr_instance_id]['actual'].append([tr.tr_real_schedule[j][0]])
            total_schedule[tr_instance_id]['actual'].append([tr.tr_real_schedule[j][1]])


    # below function gets the effective end time of a block section based queue (if any) and autoblsec list (if any) and if queue is empty then it returns the blocksection occupancy end
    def get_queue_end_time(blsec):
        if len(blsec.blsec_queue) > 0:
            # for block section object 'blsec', find queue; finds the queue end times
            end_times = [blsec.blsec_queue[i] for i in range(5, len(blsec.blsec_queue), 6)
                            if isinstance(blsec.blsec_queue[i], pd.Timestamp)]
            if end_times: 
                return max(end_times)

        # if queue is empty, check autoblsec queue end times (if any)    
        if len(blsec.autoblsec_list) > 0:
            return blsec.autoblsec_list[-1][4]  #[entry[4] for entry in blsec.autoblsec_list if isinstance(entry[4], pd.Timestamp)] 

        # queue is empty and no autoblsec case then check if block itself is occupied
        if blsec.occ_ind == 1: 
            return blsec.occ_end

        # if blocksection is completely free
        return pd.Timestamp("1900-01-01 00:00:00")

    # given an occupied block section, look for a free, unqueued sibling covering the same
    # station pair (the other '_dn1'/'_up1'/'_mid1' counterpart of the same base name) that
    # a waiting train could use instead. If stn_obj/stn_line_name are given, only consider
    # siblings actually wired to that station line; pass either as None to skip that check.
    # train_dir ('up'/'dn'), if given, restricts candidates to siblings running the same
    # physical direction as the train (or bidirectional 'mid1') -- without this, a train
    # needing e.g. 'dn' could be handed a free 'up1' sibling, which runs the wrong way and
    # then never gets its occupancy released by that direction's normal arrival processing.
    def find_free_sibling_blsec(blsec, stn_obj=None, stn_line_name=None, train_dir=None):
        base = '_'.join(blsec.name.split('_')[:-1])
        for suffix in ('dn1', 'up1', 'mid1'):
            sib_name = f'{base}_{suffix}'
            if sib_name == blsec.name:
                continue
            sib = blsec_lookup.get(sib_name)
            if sib is None:
                continue
            if train_dir is not None and not (sib.dir_mvmt[0:2] == train_dir or sib.dir_mvmt[0:3] == 'mid'):
                continue
            if sib.occ_ind != 0 or len(sib.blsec_queue) > 0:
                continue
            if stn_obj is not None and stn_line_name is not None:
                if (sib.name + '_' + stn_line_name) not in stn_obj.connections:
                    continue
            return sib
        return None

    # function to find block sections that a train can take to go from one station to another
    def blsec_id(stn1, stn2): #train needs to go from stn1 to stn2
        nonlocal blocksections_list
        nonlocal stations_list

        for j in stations_list:
            if j.name == stn1:
                stn_start = j
                break

        for k in stations_list:
            if k.name == stn2:
                stn_end = k
                break

        # if stn_start.longitude - stn_end.longitude >= 0:
        #     train_dir = "up"
        #     blsec_init = stn_end.name + '_' + stn_start.name + '_' + train_dir
        # else:
        #     train_dir = "dn"
        #     blsec_init = stn_start.name + '_' + stn_end.name + '_' + train_dir


        if stn_start.longitude - stn_end.longitude > 0:
            train_dir = "up"
        else:                                   # equal longitude -> dn
            train_dir = "dn"

        same_long  = (stn_start.longitude == stn_end.longitude)
        blsec_base = conn_base(stn1, stn2)
        blsec_base_alt = conn_base(stn2, stn1)   # swapped ordering, used only for tied pairs
        print('blsec base ', blsec_base, '| same_long', same_long)
        print('inside blocksection assign function')


        # print(train_dir, blsec_init)
        blsec_list = [] 
        for l in blocksections_list:
            if l.dir_mvmt[0:2] == train_dir or l.dir_mvmt[0:3] == 'mid':
                if (l.name.startswith(blsec_base + '_')
                        or l.name.startswith(blsec_base_alt + '_')):
                    blsec_list.append(l)
                # if l.name[0:8] == blsec_init[0:8]:
                #     blsec_list.append(l)
        print('blsec list is ', [b.name for b in blsec_list])
        # if it an arrival event; the train still occupies the block section;
        # check the station line occupying the block section
        if next_event_type == 'a' and len(stns_event) > 1:
            for blsec in blsec_list:
                print('blsec is ', blsec.name)
                if blsec.occ_ind == 1 and blsec.occ_train == next_event_tr_id: 
                    # return [train_dir, blsec] 
                    print('arrival event and blsec is ', blsec.name)
                    return blsec  
                check_auto = autoblsec_check() 
                if check_auto:    
                    print('it is autoblock section')
                    print('auto blsec list is ', blsec.autoblsec_list)
                    if blsec.autoblsec_list and next_event_tr_id == blsec.autoblsec_list[0][0]: 
                        print('arrival event and autoblock case ', blsec.name)    
                        return blsec 

        print('block assign fun before checking the connections ', blsec_list) 
        print('block assign fun before checking the connections ', [b.name for b in blsec_list])
        # if there are more than two block sections in blsec_list;
        # return the one which is free; 
        # if both are occupied, return the one which gets free earlier;


        # when more than two blocksections; before assigning it, first find the outgoing connection if a given station line having outgoing with any of the blocksection then assign
        # sometimes if a station line is empty or has earliest endtime but it is not connected to the that blocksection then don't assign

        # find the station line the train is currently on at stn_start
        # find the station line the train is currently on at stn_start
        stn_line_occ_name = ''
        for j in stn_start.tracks:
            if stn_start.tracks[j][0] == 1 and stn_start.tracks[j][5] == tr_next_event.train_id:
                stn_line_occ_name = j
                break

        # keep only sections whose connection to that line actually exists
        if stn_line_occ_name:
            blsec_list = [
                l for l in blsec_list
                if (l.name + '_' + stn_line_occ_name) in stn_start.connections
            ]
            if not blsec_list:
                raise ValueError(
                    f"blsec_id({stn1!r}, {stn2!r}): station line {stn_line_occ_name!r} "
                    f"is not connected to any candidate block section"
                )
        print('block section assign function after checking the connections; block secction list is ', [(b.name, b.occ_train) for b in blsec_list]) 








        # if this train is already waiting in a candidate block section's queue,
        # assign that track immediately 
        # if next_event_type == 'd':
        #     for blsec in blsec_list:
        #         if next_event_tr_id in blsec.blsec_queue[0::6]:
        #             print('train', next_event_tr_id, 'is already queued in', blsec.name,
        #                 '-> assigning this block section directly')
        #             return blsec



        # if next event is dept type 
        # using the next_event_tr_id find the current train queue
        # if train is in the queue then get thta blocksection and 
        # check if it is mid1 blocksection if yes then find whethere it is occupied or not if not occupied then assign it; 
        # if occupied then find the sibling blocksection(may be up or dn based on the direction of a train also check
        #  the connection exists or not from that sibling blocksection to the current station line )if it is free and does not have a queue then assign it 
        # after assinging the sibling blocksection; remove the train from the mid1 blocksection queue 





        # if next_event_type == 'd':
        #     for blsec in blsec_list:
        #         if next_event_tr_id in blsec.blsec_queue[0::6]:
        #             current_suffix = blsec.name.split('_')[-1]

        #             if current_suffix == 'mid1':
        #                 base = '_'.join(blsec.name.split('_')[:-1])
        #                 redirect_blsec = None
        #                 for suffix in ('dn1', 'up1'):
        #                     sib = blsec_lookup.get(f'{base}_{suffix}')
        #                     if sib is None or sib.occ_ind != 0 or len(sib.blsec_queue) > 0:
        #                         continue
        #                     if stn_line_occ_name and (sib.name + '_' + stn_line_occ_name) not in stn_start.connections:
        #                         continue
        #                     redirect_blsec = sib
        #                     break

        #                 if redirect_blsec is not None:
        #                     print('train', next_event_tr_id, 'was queued in', blsec.name,
        #                           '-> redirecting to free sibling section', redirect_blsec.name)
        #                     t_index = sched_act[next_event_tr_id].index(t)
        #                     dep_list = [next_event_tr_id, next_event_train, tr_next_event.tr_type,
        #                                 t_index, t, sched_act[next_event_tr_id][t_index + 2]]
        #                     blsec.queue_remove(dep_list)
        #                     return redirect_blsec

        #             print('train', next_event_tr_id, 'is already queued in', blsec.name,
        #                 '-> assigning this block section directly')
        #             return blsec


        print('/n inside blsec_id function; blsec list is ', blsec_list)
        if next_event_type == 'd':
            # only one candidate block section -> assign it directly
            if len(blsec_list) == 1:
                print('single candidate', blsec_list[0].name, '-> assigning directly')
                return blsec_list[0] 
            print('\n length of the blsec_list is inside dept case ', len(blsec_list))
            # more than one -> find the section the train is queued in
            for blsec in blsec_list:
                if next_event_tr_id in blsec.blsec_queue[0::6]:
                    # queued section already free (mid1, dn1, or up1 alike) -> take it
                    if blsec.occ_ind == 0:
                        print('train', next_event_tr_id, 'is queued in free', blsec.name,
                              '-> assigning it')
                        return blsec

                    # still occupied -> look for a free, unqueued, connected sibling
                    # (works regardless of whether blsec itself is mid1, dn1, or up1)
                    sib = find_free_sibling_blsec(blsec, stn_start, stn_line_occ_name, train_dir=train_dir)
                    if sib is not None:
                        print('train', next_event_tr_id, 'was queued in occupied', blsec.name,
                              '-> redirecting to free sibling', sib.name)
                        t_index = sched_act[next_event_tr_id].index(t)
                        dep_list = [next_event_tr_id, next_event_train, tr_next_event.tr_type,
                                    t_index, t, sched_act[next_event_tr_id][t_index + 2]]
                        blsec.queue_remove(dep_list)
                        return sib

                    # occupied and no free sibling -> stay queued
                    print('train', next_event_tr_id, 'is queued in occupied', blsec.name,
                          '-> assigning this block section directly')
                    return blsec







        end_times = []
        end_times_name = []
        if len(blsec_list) > 1: 
            print('\n case when more than one block section')
            for blsec in blsec_list:
                blsec_end_time = get_queue_end_time(blsec)
                end_times.append((blsec, blsec_end_time))
                end_times_name.append((blsec.name, blsec_end_time))
                print(blsec.name, blsec_end_time)
            print('end times list is ', end_times_name)
            free_time = pd.Timestamp("1900-01-01 00:00:00")
            # all block sections completely free
            if all(t == free_time for _, t in end_times):
                print('when all blocksections are free')
                # if all this blocksetions are free; then assing the blocksection which is having up or dn; unidirectional
                preferred = [
                    (b, t) for b, t in end_times
                    if b.dir_mvmt.startswith(('up', 'dn'))]
                if preferred:
                    selected_blsec = preferred[0][0]
                else:
                    selected_blsec = end_times[0][0]

            else:  # if more than two blocksections and one some are occupied and some free; choose the one will free earlier
                selected_blsec = min(end_times, key = lambda x: x[1])[0]
                print('case when more than two blocksections; one is occupied and other is not ', selected_blsec.name)
        else:
            # return [train_dir, blsec_list[0]]
            return blsec_list[0]

        # return [train_dir, selected_blsec]
        return selected_blsec



    # this function finds the next train and gets the blocksection; which decides the direction of a train 
    def train_direction(t, current_stn):
        # Direction of train object t on the segment starting at current_stn. 1 = W->E, 0 = E->W

        stns = list(t.tr_sched_act.keys())  # the train's stations in travel order
        if current_stn not in stns:       
            return None               
        idx = stns.index(current_stn)     # position of current_stn in the schedule
        if idx + 1 >= len(stns):        # current_stn is the destination
            return None                                   
        nxt = stns[idx + 1]  # the next station on the route

        return 1 if station_longitudes[nxt] > station_longitudes[current_stn] else 0




    big_time_value = pd.Timestamp("2100-06-01 00:00:00")



    # this part of the code is related to the time-distance chart
    def get_earliest_time(schedule_dict):
        times = []
        for stn, times_pair in schedule_dict.items():
            for t in times_pair:
                if isinstance(t, pd.Timestamp) and t < big_time_value:
                    times.append(t)
        return min(times) if times else None

    def compute_start_dt(trains, buffer_minutes):
        candidates = [get_earliest_time(tr.tr_schedule) for tr in trains]
        candidates = [c for c in candidates if c is not None]
        if not candidates:
            raise ValueError("no valid timestamps found in planned schedules to derive start_dt")
        return min(candidates) + pd.Timedelta(minutes=buffer_minutes)

    if start_dt_mode == 'manual':
        start_dt = start_dt_manual
    elif start_dt_mode == 'planned':
        start_dt = compute_start_dt(trains, buffer_minutes=start_dt_buffer_minutes)
    else:
        raise ValueError(f"unknown start_dt_mode: {start_dt_mode}")

    print(f"start_dt ({start_dt_mode}): {start_dt}")



    # instead of finding the next station; based the train schedule. it finds it using the connected blocksection.
    def find_stn3(stn1, stn2):
        """Return the station adjacent to stn2 along the train's direction of travel,
        derived from block-section. Returns '' if stn2 is at the end of the
        physical network (no other block section touches it)."""
        curr_blsec_base = conn_base(stn1, stn2)   # forms the blocksection

        for b in blocksections_list:
            # skip the block section the train just came from
            if b.name.startswith(curr_blsec_base + '_'):
                continue
            # is this block section attached to stn2?
            if b.stn_west.name == stn2:
                return b.stn_east.name
            if b.stn_east.name == stn2:
                return b.stn_west.name
        return ''

    def check_next_blse_stn_occupancy(t_ind, len_sched): 
        nonlocal stns_event
        nonlocal sched_act

        next_stn_occ = {}
        next_stn_line_min_endtimes = pd.Timestamp("2100-01-01 00:00:00")
        up_dir_stn_count, dn_dir_stn_count = 0, 0
        count_next_blsec = 0
        count_curr_blsec = 0
        next_blsec_list = []
        next_blsec_list_names = []
        curr_blsec_list = []

        stn1 = stns_event[0].name  # stn from which train is departing
        stn2 = ''                  # stn at which train is arriving
        stn3 = ''                  # stn next to the arrival station

        # if t_ind != len_sched - 2:   # not destination
        if t_ind != len_sched - 1:
            stn2 = stns_event[1].name

            # current blocksection (west_east by longitude)
            curr_blsec = conn_base(stn1, stn2)
            print('current blocksection name is ', curr_blsec)
            for b in blocksections_list:
                if b.name.startswith(curr_blsec):
                    count_curr_blsec += 1

            # get next station line occupancies  
            for i, vals in stns_event[1].tracks.items():
                train = vals[5]
                train_dir = None
                for t in trains:
                    if t.train_id == train:          # match FIRST, then compute direction
                        train_dir = train_direction(t, stns_event[1].name)
                        break
                next_stn_occ[i] = [vals[0], vals[3], train_dir, vals[5]]
                print('type of vals[3] is ', type(vals[3]))
                if isinstance(vals[3], pd.Timestamp):
                    if vals[3] < next_stn_line_min_endtimes:
                        next_stn_line_min_endtimes = vals[3]
                if vals[0] == 1:
                    if train_dir == 0: dn_dir_stn_count += 1
                    else: up_dir_stn_count += 1

            # get stn3: first try train's actual schedule 
            if t_ind + 4 < len(sched_act[next_event_tr_id]):
                stn3_candidate = sched_act[next_event_tr_id][t_ind + 4]
                if isinstance(stn3_candidate, str):
                    stn3 = stn3_candidate

            # # fallback: step one station past stn2 in direction of travel (stn1 -> stn2)
            # if stn3 == '':
            #     ordered = sorted((s.name for s in stations_list), key=lambda n: station_longitudes[n])  # west -> east
            #     stn2_idx = ordered.index(stn2)
            #     step = 1 if station_longitudes[stn2] > station_longitudes[stn1] else -1
            #     nxt = stn2_idx + step
            #     print('step values is ', step)
            #     print('nxt value is ', nxt)
            #     if 0 <= nxt < len(ordered):
            #         stn3 = ordered[nxt]


            # fallback: derive stn3 from block-section topology (not longitude -- bhns/krdl share a longitude)
            if stn3 == '':
                stn3 = find_stn3(stn1, stn2)
                print('next to next station is found so, stn3 is ', stn3)

            # if stn3 found, find next blocksection and its occupancy 
            if stn3 != '':
                next_blsec_name = conn_base(stn2, stn3)
                print('next to next blocksection name ', next_blsec_name)
                for b in blocksections_list:
                    if b.name.startswith(next_blsec_name): 
                        count_next_blsec += 1
                        blsec_tr_dir = None
                        blsec_occ_train_name = b.occ_train.split('_')[0] if b.occ_train else None
                        for t in trains:
                            if t.train_id == blsec_occ_train_name:        # match FIRST
                                blsec_tr_dir = train_direction(t, b.stn_west.name)
                                print('train name is ', t.train_id, ' and its direction is ', blsec_tr_dir)
                                print('blsec occ train name is ', blsec_occ_train_name)
                                break
                        next_blsec_list.append([b, blsec_tr_dir])
                        next_blsec_list_names.append([b.name, blsec_tr_dir])
            else:
                print('next to next station not found; stn2 is last in corridor')
                count_next_blsec = count_curr_blsec

        print(f'down dir stn line count is ', {dn_dir_stn_count}, 'up dir stn line count is ', {up_dir_stn_count})
        print('next blocksections list ', next_blsec_list_names)
        print('next station lines occ details ', next_stn_occ)
        return [dn_dir_stn_count, up_dir_stn_count, next_stn_line_min_endtimes, count_next_blsec, count_curr_blsec, next_blsec_list]




    sched = {} # store the schedule in flat list format with train instance id as key and schedule deatails in list 
    sched_act = {} 
    for i in trains:
        tr_sched = [] # temporary list to hold schedule of each train
        tr_sched_name = i.train_id + '_' + str(i.instance_index)
        sched[tr_sched_name] = tr_sched 
        # sched_act[tr_sched_name] = tr_sched
        for j in i.tr_schedule:
            sched[tr_sched_name].append(j)
            sched[tr_sched_name].append(i.tr_schedule[j][0])
            sched[tr_sched_name].append(i.tr_schedule[j][1])
        #sched[i.train_id] = i.tr_schedule
        #sched_act[i.train_id] = i.tr_sched_act


    sched_act = copy.deepcopy(sched) # initial actual schedule is same as planned schedule; it will be updated during the simulation
    given_sched = copy.deepcopy(sched) # to keep a copy of the original schedule; for comparison
    print('\n planned schedule of trains: ', sched)


    # create list with an element for each train in the schedule
    # each element has the time of the next event and type of event:
    # 'a' for arrival at station, 'd' for departure from station
    def build_event_list():
        event_list = []
        for j in sched_act: # j in the train instance like '12345_dn1'; this loop finds the
            b = [k for k in sched_act[j] if isinstance(k, str) == False and k < pd.Timestamp("2100-06-01 22:50:00")]
            if len(b) > 0:
                a = min(b)
                # print('\n ', a)
                a_ind = sched_act[j].index(a)
                # print('\n ', a_ind)
                if isinstance(sched_act[j][a_ind - 1], str): a_type = 'a'
                elif isinstance(sched_act[j][a_ind - 1], str) == False: a_type = 'd'
                tr_num_ind = j.index('_')
                tr_name = j[0:tr_num_ind]
                # this below four parameters will be put in the event list; train name, event time, event type(arrival or dept), train id
                event_list.append(tr_name)
                event_list.append(a)
                event_list.append(a_type)
                event_list.append(j)
            else: 'do nothing'
        return event_list


    # define termination criterion
    # note that termination criterion has to be updated after each event
    def term_crit_calc():
        nonlocal sched_act
        b = [] 
        for j in sched_act:
            c = [k for k in sched_act[j] if isinstance(k, str) == False and k < pd.Timestamp("2100-06-01 22:50:00")]
            if len(c) > 0: b.append(max(c))
            else: b.append(pd.Timestamp("1900-01-01 00:00:00"))
        t_max = max(b)
        return t_max


    # get the list of stations_list involved in the current event; arrival and dept station
    # gives the list of stations_list; if arrival event then [arrival station, prev dept station] and if dept case then [dept station, next arrival station]
    def get_station_event(t, next_event_tr_id, next_event_type, stations_list): 
        len_sched = len(sched_act[next_event_tr_id])
        a = sched_act[next_event_tr_id].index(t) # a is the index position of the 't' event time
        next_event_stn_up1 = ''
        next_event_stn_mid1 = ''
        if next_event_type == 'a':
            next_event_stn_up1 = sched_act[next_event_tr_id][a-1] #station at which train is arriving
            if a > 1: next_event_stn_mid1 = sched_act[next_event_tr_id][a-4] #station from which train is arriving (when arrival station is not the first (origin) in its schedule)
            else:
                'do nothing'
                #next_event_stn_mid1 = sched_act[next_event_tr_id][a+2] ##next station on train route after station at which it is arriving
        else:
            next_event_stn_up1 = sched_act[next_event_tr_id][a-2] #station from which train is departing
            if a < len_sched - 1: next_event_stn_mid1 = sched_act[next_event_tr_id][a+1] #station to which train is going (when arrival station is not the last (destination) in its schedule)
            else: 'do nothing'
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




    # function to give priority to passenger trains over goods trains in block section queue
    # no changes if all are pasenger trains 
    # if recent added train is passenger and previously available trains are goods; then updates the list and put the passenget train before goods trains. 
    def update_blsec_queue_priority(blsec, train_type, next_event_tr_id):
        """
        Ensures all passenger trains are at the front of the queue and all goods trains at the end.
        Updates occ_start/occ_end and schedules for goods trains if needed.
        """
        if not blsec.blsec_queue:  # If the queue is empty, do nothing
            return

        # Build queue as list of entries
        queue = [blsec.blsec_queue[i:i+6] for i in range(0, len(blsec.blsec_queue), 6)] # convert flat list to list of lists
        # Sort queue: passenger trains first, goods trains last
        passenger_trains = [q for q in queue if q[2] == 'p']
        goods_trains = [q for q in queue if q[2] == 'g']
        queue = passenger_trains + goods_trains

        # below code will execute only when given train is a passenger train.
        if passenger_trains and goods_trains and train_type == 'p':
            current_train_start_time = goods_trains[0][4]
            # current_train_start_time = last_passenger_end + pd.Timedelta(minutes=1)  # Ensure goods trains start after last passenger train
            #time taken by the given event passenger train to cover the blocksection
            time_taken = passenger_trains[-1][5] - passenger_trains[-1][4]  # this is the time taken by current passenger train to cover the block section
            current_train_end_time = current_train_start_time + time_taken  # Maintain original duration for goods trains
            current_train_ind = passenger_trains[-1][3]  # Index in the queue for the last passenger train
            # after getting new start and end time to the given passenger train update its schedule
            # for now inside sched_upt t_ind is taken but later could be changed on the position of the this function
            sched_updt(current_train_start_time, current_train_ind, next_event_tr_id)  #update the schedule for this given passenger train
            # also update the station line occupancy
            stn_line= get_train_stnline_for_departure_delay(stns_event, passenger_trains[-1][1])
            stns_event[0].set_occupancy_updt(stn_line, passenger_trains[-1][0])
            passenger_trains[-1][4] = current_train_start_time  # occ_start
            passenger_trains[-1][5] = current_train_end_time  # occ_end

            # after updating the schedule for the given passenger train update the goods trains
            prev_end = current_train_end_time + pd.Timedelta(minutes=1)  # Ensure goods trains start after the last passenger train's end time
            for gq in goods_trains:
                duration = gq[5] - gq[4]
                gq[4] = max(prev_end, gq[4]) + pd.Timedelta(minutes=1)  # occ_start
                gq[5] = gq[4] + duration      # occ_end
                tr_id = gq[0]
                t_ind_queue = gq[3]  # index in the queue
                sched_updt(gq[4], t_ind_queue, tr_id)  # Update schedule for goods train
                # also update the station line occupancy time accordingly. set_occupancy_updt(stn_line_name, occ_end)
                stn_line_stn0 = get_train_stnline_for_departure_delay(stns_event, gq[1])  # checks stns_event[0]
                stn_line_stn1 = get_train_stnline_for_arrival_delay(stns_event, gq[1])    # checks stns_event[1]
                print('gq[1] value is ', gq[1])
                print('gq value is ', gq)
                print('inside goods train upt function; get_train_stnline stn0:', stn_line_stn0, 'stn1:', stn_line_stn1)
                if stn_line_stn0 is not None:
                    stns_event[0].set_occupancy_updt(stn_line_stn0, gq[5])
                elif stn_line_stn1 is not None:
                    stns_event[1].set_occupancy_updt(stn_line_stn1, gq[5])
                else:
                    print(f'[goods train update] train {gq[1]} not found at either station, skipping stn line update')
                prev_end = gq[5]   # also update pre_end time for the next goods train

            blsec.blsec_queue = [item for sublist in queue for item in sublist]  # Flatten the list back to original format
        else: 
            'do nothing'  # No need to update if only passenger or only goods trains



    #function to check if an event involves an autoblocksection case: 
    def autoblsec_check():
        if (stns_event[0].name in autoblock_stations and stns_event[1].name in autoblock_stations):
            return True
        else: return False

    # The new start time (as a pandas Timestamp) from which we want to update the schedule. This is the time we want to shift the schedule to.
    # t_ind: The index (integer) in the schedule list (sched_act[next_event_tr_id]) where the update should begin. All times at and after this index will be shifted.
    # next_event_tr_id: The key (string, e.g., '12345_mid1') for the train in the sched_act dictionary whose schedule needs to be updated
    def sched_updt(t_updt_start, t_ind, next_event_tr_id):
        nonlocal sched
        nonlocal sched_act
        num_updt = sched_act[next_event_tr_id][t_ind:]
        updt_inc = t_updt_start - sched_act[next_event_tr_id][t_ind]
        for j in range(len(num_updt)):
            if isinstance(sched_act[next_event_tr_id][t_ind+j], str): 'do nothing'
            else:
                sched_act[next_event_tr_id][t_ind+j] = sched_act[next_event_tr_id][t_ind+j] + updt_inc


    def tr_sched_updt(t, next_event_type):
        nonlocal tr_next_event
        nonlocal stns_event
        if next_event_type == 'a':
            tr_next_event.tr_sched_act[stns_event[0].name][0] = t
        else:
            tr_next_event.tr_sched_act[stns_event[0].name][1] = t

    def conn_base(a, b, dir_mvmt=None):
        w, e = (a, b) if station_longitudes[a] <= station_longitudes[b] else (b, a)
        print(f'conn base output is = {w}_{e}_{dir_mvmt}')
        return f'{w}_{e}_{dir_mvmt}' if dir_mvmt else f'{w}_{e}'

    def conn_exists(stn, a, b, dir_mvmt, line):
        """Return the real connection key (a_b or swapped b_a) present at `stn`, else None.
           Handles equal-longitude pairs where west/east ordering is ambiguous."""
        print('inside the conn_exists function')
        for base in (conn_base(a, b, dir_mvmt), conn_base(b, a, dir_mvmt)):
            print('base blec name coming form conn_base is ', base)
            key = base + '_' + str(line)
            print('connection key in conn_exits is ', key)
            if key in stn.connections:
                return key
        return None


    def stn_line_assign(t_ind, next_event_tr_id, len_sched):
        nonlocal stns_event
        nonlocal sched_act

        stn_line_occ_flag = 0
        stn_line_occ_name = ''
        next_event_conn1 = ''
        next_event_conn2 = ''

        stn1 = ''
        stn2 = stns_event[0].name
        stn3 = ''

        print('stns_events list is ', [s.name for s in stns_event])

        if t_ind > 1:
            if t_ind != len_sched - 2:
                stn1 = stns_event[1].name
                stn3 = sched_act[next_event_tr_id][t_ind + 2]
                print('stn1, stn2 and stn3 before finding the blsec is ', stn1, stn2, stn3)
                out_blsec_dir = blsec_id(stn2, stn3).dir_mvmt  
                print('next blsec outgoing direction is ', out_blsec_dir)
            else: 
                stn1 = sched_act[next_event_tr_id][t_ind - 4]

            arrived_dir = blsec_t.dir_mvmt
            print('train arrived blocksection direction is ', arrived_dir)

        else:
            stn3 = sched_act[next_event_tr_id][t_ind + 2]
            out_blsec_dir = blsec_id(stn2, stn3).dir_mvmt
            print('outgoing connection direction is ', out_blsec_dir)

        tracks = stns_event[0].tracks

        if tr_next_event.tr_type == 'g':
            track_order = sorted(tracks.keys(), key=lambda j: tracks[j][1] != 0)
        else:
            track_order = list(tracks.keys())

        arrival_time = tr_next_event.tr_sched_act[stns_event[0].name][0]
        departure_time = tr_next_event.tr_sched_act[stns_event[0].name][1]
        same_arr_dep = (arrival_time == departure_time)

        # Passenger train with a halt must be assigned a station line that has a platform.
        # Pass 0 enforces that. Pass 1 only runs if pass 0 found nothing at all (i.e. every
        # platform line is occupied) -- as a constraint-relaxation fallback so the train can
        # still be assigned a platformless line instead of being stuck retrying/queuing
        # indefinitely while a platformless line sits free. Goods trains and pass-through
        # passenger trains are unaffected by the platform rule and may always use any free
        # line, so for them a second identical pass would just repeat the same work -- only
        # spend the extra pass when it could actually change the outcome.
        halting_passenger = (tr_next_event.tr_type == 'p' and not same_arr_dep)
        total_passes = 2 if halting_passenger else 1

        for pass_no in range(total_passes):

            for j in track_order:

                print('\n station line under consideration: ', j, stns_event[0].tracks[j][0])

                if stns_event[0].tracks[j][0] != 0:
                    continue

                # only platform lines allowed on the first pass; relaxed on the fallback
                # pass (pass_no == 1) so a platformless line can be used
                if pass_no == 0 and halting_passenger and stns_event[0].tracks[j][1] == 0:
                    continue

                print('\n current stn line is free')

                if t_ind > 1:
                    print('current blocksection is ', blsec_t.name)
                    c1 = blsec_t.name + '_' + str(j)
                    if c1 not in stns_event[0].connections:
                        c1 = None  
                    # c1 = conn_exists(stns_event[0], stn1, stn2, arrived_dir, j)
                    print('incoming connection c1 connection is ', c1)

                    if t_ind != len_sched - 2:
                        c2 = conn_exists(stns_event[0], stn2, stn3, out_blsec_dir, j)
                        print('out going connection is ', c2)
                        if c1 and c2:
                            next_event_conn1, next_event_conn2 = c1, c2
                        else:
                            next_event_conn1 = next_event_conn2 = ''

                    else:
                        next_event_conn1 = c1 if c1 else ''
                        next_event_conn2 = ''

                else:
                    c1 = conn_exists(stns_event[0], stn2, stn3, out_blsec_dir, j)
                    next_event_conn1 = c1 if c1 else ''
                    next_event_conn2 = ''

                print('\n next_event_conn1 and next_event_conn2 after connection check: ',
                      next_event_conn1, next_event_conn2)

                if next_event_conn1 != '':
                    stn_line_occ_flag = 1
                    stn_line_occ_name = j
                    return [stn_line_occ_flag, stn_line_occ_name,
                            next_event_conn1, next_event_conn2]

        return [stn_line_occ_flag, stn_line_occ_name,
                next_event_conn1, next_event_conn2]


    # train is waiting at the stn line; blocksection is occupied; get the stn_line to update its occupancy end time 
    def get_train_stnline_for_arrival_delay(stns_event, train_name):
        for stn_line in stns_event[1].tracks: 
            print(stn_line)
            if stns_event[1].tracks[stn_line][5]== train_name:
                return stn_line

    # train is waiting at the stn line; blocksection is occupied; get the stn_line to update its occupancy end time
    def get_train_stnline_for_departure_delay(stns_event, train_name):
        for stn_line in stns_event[0].tracks:
            print(stn_line)
            if stns_event[0].tracks[stn_line][5]== train_name:
                return stn_line




    HALT_DEVIATION_SEED = 1234         # fixed seed -> reproducible simulation runs
    _halt_dev_rng = np.random.default_rng(HALT_DEVIATION_SEED) # it creates a random number generator object (an instance of numpy.random.Generator)
    def _sample_halt_dev(fit, rng):
        """Draw one halt-deviation value (minutes) from a fitted per-station distribution."""
        if fit['type'] == 'empirical': # most of the deviation values are just zero
            return float(rng.choice(fit['data'])) # draw any of the deviation value from the data of the station

        if rng.random() >= fit['p_zero']:
            dist = getattr(_halt_dev_stats, fit['dist']) 
            draw = dist.rvs(*fit['params'], random_state=rng)
            return float(np.round(draw - 0.5 + fit['shift']))  # undo continuity shift, back to whole minutes
        return 0.0

    def _generate_halt_deviation(station, train_type, rng):
        """station: uppercase station code, train_type: 'G' or 'P'. Returns 0.0 if no fit exists for the station."""
        fit_dict = halt_dev_fits_g if train_type == 'G' else halt_dev_fits_p
        max_dict = station_max_g if train_type == 'G' else station_max_p
        fit = fit_dict.get(station)
        if fit is None:
            return 0.0
        value = _sample_halt_dev(fit, rng)
        cap = max_dict.get(station)             # clamp to the real observed max for this station
        return min(value, float(cap)) if cap is not None else value



    def add_halt_randomness():
        if not USE_HALT_DEVIATION:
            return 0

        try:
            station = stns_event[0].name.upper() 
            train_type = 'G' if tr_next_event.tr_type == 'g' else 'P'
        except Exception:
            return 0  # station/train not available (shouldn't normally happen) -> no deviation

        Y = _generate_halt_deviation(station, train_type, _halt_dev_rng)
        print(f'\n [halt-deviation] station={station} train_type={train_type} sampled Y={Y} min')
        return Y





    def _sample_blsec_time(blsec_key, train_type, rng):
        times_dict = g_times if train_type == 'g' else p_times
        entry = times_dict.get('dn', {}).get(blsec_key) or times_dict.get('up', {}).get(blsec_key)
        if not entry:
            return None
        print('inside the function of finding the sample blsec crossing time')
        weights = np.array(entry['weights'], dtype=float)
        probs = weights / weights.sum() 
        return rng.choice(entry['values'], p=probs)


    def add_speed_randomness(base_speed):
        if not USE_SPEED_RANDOMNESS:
            return base_speed
        try:
            blsec_key = f"{stns_event[0].name.upper()}-{stns_event[1].name.upper()}"
            train_type = 'g' if tr_next_event.tr_type == 'g' else 'p'
        except Exception:
            return base_speed  # block section/station not available -> no randomness

        sampled_time_min = _sample_blsec_time(blsec_key, train_type, _speed_rand_rng)
        if not sampled_time_min or sampled_time_min <= 0:
            return base_speed

        return (blsec_t.length * 60) / sampled_time_min  # km/hr


    # while dept randomeness is added in the speed so new arrival will change; based on teh added stochasticity in the speed
    def new_arr_by_speed_randomness(next_event_tr_id, t_ind):
        # convert Timedelta to minutes i.e. a float value so that it can be used in the speed calculation
        time_diff = sched_act[next_event_tr_id][t_ind+2] - sched_act[next_event_tr_id][t_ind]
        time_diff_minutes = time_diff.total_seconds() / 60 # Convert to minutes
        # now the speed is in km/hr
        tr_dep_speed = (blsec_t.length*60) / (time_diff_minutes) # time is in hr
        t_blsec_end = blsec_t.length*60 / tr_dep_speed # time is in minutes
        t_blsec_end_int = int(np.ceil(t_blsec_end))
        t_blsec_end = pd.Timedelta(minutes=t_blsec_end_int)
        print('before adding the randomness the blsec crossing time is ', t_blsec_end)
        # ADD RANDOMNESS TO SPEED
        tr_dep_speed_mod = add_speed_randomness(tr_dep_speed)
        t_blsec_occ_end = blsec_t.length / tr_dep_speed_mod # time is in hr
        t_blsec_occ_end = t_blsec_occ_end * 60 # convert to minutes
        t_blsec_occ_end_int = int(np.ceil(t_blsec_occ_end))
        t_blsec_occ_end = pd.Timedelta(minutes=t_blsec_occ_end_int)
        print('after adding the randomness blsec crossing time is ', t_blsec_occ_end)
        # Calculate new arrival time at next station
        new_arrival_time = t + t_blsec_occ_end
        new_arrival_time = new_arrival_time.replace(microsecond=0)
        original_arrival_time = sched_act[next_event_tr_id][t_ind+2]
        time_change = new_arrival_time - original_arrival_time
        # returns the new arrival time if change is more than 1 minute.
        if time_change > pd.Timedelta(minutes=1):
            return [new_arrival_time, time_change]
        else:
            return [original_arrival_time]





    def get_min_endtime(stn_event, t_ind, is_origin_stn): # finds the min endtime of a station. so, that next incoming train schedule will be updated based on that.
        nonlocal sched
        len_sched = len(sched[next_event_tr_id])
        min_endtime = pd.Timestamp("2100-01-05 22:50:00")
        print('inside the get_min_edntime function')

        # a passenger train that isn't halting here (arrival == departure) is just passing
        # through, so it may use a platformless line same as goods trains -- only a genuine
        # halt requires a platform. Matches the same rule already applied in stn_line_assign.
        _arr = tr_next_event.tr_sched_act[stn_event.name][0]
        _dep = tr_next_event.tr_sched_act[stn_event.name][1]
        same_arr_dep = (_arr == _dep)

        def outgoing_blsec_name(a, b):
            # Return the name of the block section the train would take from a to b.
            base = conn_base(a, b)            # west_east station pair, e.g. 'nwp_kbm'
            # east_bound = station_longitudes[b] > station_longitudes[a]
            base_alt = conn_base(b,a) # added later
            east_bound = station_longitudes[b] >= station_longitudes[a]
            wanted = 'dn' if east_bound else 'up'
            # prefer the unidirectional match; fall back to a mid (bidirectional) section
            candidates = [x for x in blocksections_list 
                          if x.name.startswith(base + '_')
                          or  x.name.startswith(base_alt + '_')] # added later 
            for x in candidates:
                if x.dir_mvmt.startswith(wanted):
                    return x.name
            for x in candidates:
                if x.dir_mvmt.startswith('mid'):
                    return x.name
            return None

        if is_origin_stn:
            # origin station: no incoming blsec, only the outgoing one
            next_stn = sched[next_event_tr_id][t_ind + 2]
            curr_stn = sched[next_event_tr_id][t_ind - 1]
            out_blsec = outgoing_blsec_name(curr_stn, next_stn)

            for j in stn_event.tracks:
                print(f"station line {j}", stn_event.tracks[j][3], stn_event.tracks[j][5])

                # passenger needs platform only if it actually halts here
                if tr_next_event.tr_type == 'p' and not same_arr_dep and stn_event.tracks[j][1] == 0:
                    continue

                if out_blsec is None:
                    continue
                next_conn = out_blsec + '_' + str(j)
                print('origin station, next outgoing connection could be ', next_conn)

                if (next_conn in stn_event.connections
                        and isinstance(stn_event.tracks[j][3], pd.Timestamp)
                        and min_endtime > stn_event.tracks[j][3]):
                    min_endtime = stn_event.tracks[j][3]
                    print(f"min_endtime is {min_endtime}")

            print('\n station line becomes free at: ', min_endtime)
            return min_endtime



        # not origin
        curr_blsec_name = blsec_t.name             
        print('\n current block section under consideration: ', curr_blsec_name)

        if t_ind == len_sched - 2:
            # destination: only incoming connection to check
            for j in stn_event.tracks:
                print(f"station line {j}", stn_event.tracks[j][3], stn_event.tracks[j][5])

                if tr_next_event.tr_type == 'p' and not same_arr_dep and stn_event.tracks[j][1] == 0:
                    continue

                conn_key = curr_blsec_name + '_' + str(j)
                if (conn_key in stn_event.connections
                        and min_endtime > stn_event.tracks[j][3]):
                    min_endtime = stn_event.tracks[j][3]

            print('\n station line becomes free at: ', min_endtime)
            return min_endtime

        # mid-corridor: both incoming and outgoing connections required
        next_stn = sched[next_event_tr_id][t_ind + 2]
        curr_stn = sched[next_event_tr_id][t_ind - 1]
        out_blsec = outgoing_blsec_name(curr_stn, next_stn)
        print('outgoing could be ', out_blsec)
        for j in stn_event.tracks:
            print(f"station line {j}", stn_event.tracks[j][3], stn_event.tracks[j][5])

            if tr_next_event.tr_type == 'p' and not same_arr_dep and stn_event.tracks[j][1] == 0:
                continue
            if out_blsec is None:
                continue

            next_conn = out_blsec + '_' + str(j)
            conn_key = curr_blsec_name + '_' + str(j)
            # print('next conn, conn_key ', next_conn, conn_key)
            # if (conn_key in stn_event.connections
            #         and next_conn in stn_event.connections
            #         and min_endtime > stn_event.tracks[j][3]):
            #     min_endtime = stn_event.tracks[j][3]

            if (conn_key in stn_event.connections
                        and next_conn in stn_event.connections
                        and isinstance(stn_event.tracks[j][3], pd.Timestamp)
                        and min_endtime > stn_event.tracks[j][3]):
                min_endtime = stn_event.tracks[j][3]

        print('\n station line becomes free at: ', min_endtime)
        # if min_endtime == pd.Timestamp("2100-01-05 22:50:00"):
        #     raise ValueError(f"get_min_endtime: no valid station line found at {stn_event.name} for train {next_event_tr_id}, so min_endtime set {min_endtime}")
        return min_endtime



    # while departing the goods trains, check all station line trains and previous blocksection passenger trains if any
    # if yes, then get the maximum end time among those lines and passenger trains because goods train can depart after all these lines and passenger trains are free.
    # basically this function ensures the priority of passenger trains over goods trains for departure from station when station lines and blocksection are occupied by both passenger and goods trains.
    def get_pass_train_stnline_endtimes(t, next_event_tr_id):
        stn_lines = [] # get only those station lines which are connected to the desired blocksection 
        for stn_line in stns_event[0].tracks:
        # get all connections which connects to the next block section. 
        # this function is called at the dept event case. 
            conn_key = blsec_t.name + '_' + str(stn_line)
            if conn_key in stns_event[0].connections:
                stn_lines.append(conn_key.split('_')[-1])
        print('list of stn lines', stn_lines)
        print('goods train timetable is', sched_act[next_event_tr_id])

        # direction the current (goods) train is heading from this station, using the
        # same station-name/next-station convention as check_next_blse_stn_occupancy
        current_train_dir = train_direction(tr_next_event, stns_event[0].name)
        print('current departing train direction is', current_train_dir)
        pass_train_stnline_endtimes = []
        for stn_line in stn_lines:
            try:
                tr_info = stns_event[0].tracks[stn_line]  #stores the list [ind, platorm_no, occ_start, end, dur, "tr_name"]
            except Exception:
                continue
            if not isinstance(tr_info, (list, tuple)):      #tr_info, could be a list or tuple... sanity check
                continue
            print('tr info for station line ', stn_line, ' is ', tr_info)
            # tracks[...][5] is likely the occupying train id -- check existence
            occ_train_id = tr_info[5] if len(tr_info) > 5 else  None
            if occ_train_id is None:
                continue 
            print('occ train id is', occ_train_id)
            # find train object and its type
            occ_train_obj = next((tr for tr in trains if tr.train_id == occ_train_id), None)
            occ_type = getattr(occ_train_obj, 'tr_type', None) if occ_train_obj is not None else None
            if occ_type == 'p':
                # direction check: this station must not be occ_train_obj's destination
                # (train_direction returns None in that case), and its direction of travel
                # from here must match the departing goods train's direction -- otherwise
                # this passenger train has no real conflict with blsec_t and shouldn't delay goods.
                occ_train_dir = train_direction(occ_train_obj, stns_event[0].name)
                print('occ passenger train', occ_train_id, 'direction is', occ_train_dir)
                if occ_train_dir is None or occ_train_dir != current_train_dir:
                    print('skipping', occ_train_id, '-- destination station or opposite direction, no conflict with', blsec_t.name)
                    continue

                print('occ type is', occ_type )
                print('tr info is', tr_info)
                print('train id is', occ_train_id)
                end_time = tr_info[3] if len(tr_info) > 3 else None
                if isinstance(end_time, pd.Timestamp) and end_time >= t:
                    pass_train_stnline_endtimes.append(end_time)
        if len(pass_train_stnline_endtimes)>0:
            max_endtime= max([i for i in pass_train_stnline_endtimes if isinstance(i, pd.Timestamp) and i>t])
            print('list of endtimes here is', pass_train_stnline_endtimes)
            print('\n station line ', stn_line_occ_name, 'at station ', stns_event[0].name, 'will be free starting at t = ', max_endtime+ pd.Timedelta(minutes=1))
            print('given stn line is ', stn_line_occ_name)
            print('curent station is', stns_event[0].name, stns_event[1].name)
            return max_endtime
        else: return None



    # while departing the goods trains, get the previous blocksection object; using this we will get the its occupancy details if occupied by the passenger train. if yes then given gooods train will be halted. 
    # if it is a single line blocksection then while departing the train it won't look for the 
    # passenger train; as in case of single blocksection case alredy it is packed with so many constraint
    def get_prev_blsec_obj(t_ind, next_event_tr_id):
        # if this is the origin station, there is no previous block section
        if t_ind - 5 < 0:
            print('previous block section is  None  (train at origin)')
            return None

        previous_stn = sched_act[next_event_tr_id][t_ind - 5]
        curr_stn = stns_event[0].name

        # west_east base name; matches the longitude-driven blsec naming
        prev_base    = conn_base(previous_stn, curr_stn)
        # 'dn' if the train moved previous -> current eastward, else 'up'
        east_bound   = station_longitudes[curr_stn] >= station_longitudes[previous_stn]
        wanted       = 'dn' if east_bound else 'up'
        prev_blsec_obj = next(
            (b for b in blocksections_list
             if b.name.startswith(prev_base + '_')
             and isinstance(b.dir_mvmt, str)
             and b.dir_mvmt.startswith(wanted)),
            None
        )

        print('previous block section is ', prev_blsec_obj.name if prev_blsec_obj else None)
        return prev_blsec_obj

    # using the previous blocksection object, check if it is occupied by passenger train; if yes then get its arrival time to the current station because 
    # given goods train will have to wait for that passenger train to arrive at the station and depart from the blocksection; so, we will shift the departure of goods train after that arrival time.
    def get_prev_pass_train_arr_time(t_ind, next_event_tr_id):    #gives None if prev_blsec is empty or occupied by goods train
        prev_blsec_obj= get_prev_blsec_obj(t_ind, next_event_tr_id) # get the prev blocksection object 
        if prev_blsec_obj is None:                 # at origin -> no previous section
            return None
        if prev_blsec_obj.occ_ind == 1:
            train_on_prev_blsec = prev_blsec_obj.occ_train
            train_on_prev_blsec = train_on_prev_blsec.split('_')[0]
            print('train on previous block section is ', train_on_prev_blsec)
            prev_train = next((tr for tr in trains if tr.train_id == train_on_prev_blsec), None)
            print('previous train object is ', prev_train)
            if prev_train:
                previous_train_type = prev_train.tr_type
            else:
                previous_train_type = None
            print('previous train type on previous block section is ', previous_train_type)

            if previous_train_type == 'p' and prev_blsec_obj.occ_ind == 1:
                # Third step is to find the previous trains arrival time to the current station and add some time minutes to it shift it ahead
                previous_pass_train_arr_time = getattr(prev_blsec_obj, 'occ_end', None) or getattr(prev_blsec_obj, 'occ_end_time', None)
                previous_pass_train_id = getattr(prev_blsec_obj, 'occ_train', None)
                print('previous passenger train id is on previous block section is ', previous_pass_train_id)
                print('previous passenger train arrival time is ', previous_pass_train_arr_time)
                return previous_pass_train_arr_time

            else: return None

        else:
            print("Previous blsec is empty")
            return None


    # get the updated departure time for the goods train considering the passenger train priority; 
    # if finds the max time amongst station line occupancy and prev blsec occupany 
    def goods_delay_due_to_passenger(sched_act, t, t_ind, next_event_tr_id):
        # below function gives the prev blocksection object 
        max_endtime_among_stn_trains= get_pass_train_stnline_endtimes(t, next_event_tr_id)
        prev_pass_train_arr_time= get_prev_pass_train_arr_time(t_ind, next_event_tr_id)

        if not max_endtime_among_stn_trains and not prev_pass_train_arr_time:
            return sched_act[next_event_tr_id][t_ind]

        elif max_endtime_among_stn_trains and prev_pass_train_arr_time:
            updt_dep_time= max(max_endtime_among_stn_trains, prev_pass_train_arr_time)
            return updt_dep_time

        elif max_endtime_among_stn_trains and not prev_pass_train_arr_time:
            updt_dep_time= max_endtime_among_stn_trains
            return updt_dep_time
        else:
            updt_dep_time= prev_pass_train_arr_time
            return updt_dep_time

    # this funtion checks on the given all the trains are goods or not 
    def check_if_all_goods(t_ind, next_event_tr_id):
        stn_lines = []
        for stn_line in stns_event[0].tracks:
        # get all connections which connects block section
            conn_key = blsec_t.name + '_' + str(stn_line)
            if conn_key in stns_event[0].connections:
                stn_lines.append(conn_key.split('_')[-1])

        for stn_line in stn_lines:
            try:
                tr_info = stns_event[0].tracks[stn_line]  #stores the list [ind, platorm_no, occ_start, end, dur, "tr_name"]
            except Exception:
                continue
            if not isinstance(tr_info, (list, tuple)):      #tr_info, could be a list or tuple... sanity check
                continue

            # tracks[...][5] is likely the occupying train id -- check existence
            occ_train_id = tr_info[5] if len(tr_info) > 5 else  None

            # an empty line has no train on it at all -- it isn't a blocking passenger,
            # so it shouldn't count against "all goods" (previously this fell through to
            # occ_type=None below and incorrectly returned False for a merely-free line)
            if not occ_train_id:
                continue

            # find train object and its type
            occ_train_obj = next((tr for tr in trains if tr.train_id == occ_train_id), None)
            occ_type = getattr(occ_train_obj, 'tr_type', None) if occ_train_obj is not None else None
            if occ_type=='g':
                continue
            else:
                return False

        print("Since all trains on station are goods and prev blsec has passenger we would have to depart this gooods train")
        return True



    # This is a main core simulation logic function which handles arrival and departure events and updates the schedules.
    def resource_update_event(next_event_type, next_event_tr_id, t):
        nonlocal sched_act, stns_event, blsec_t, tr_next_event, t_max, next_event_train
        nonlocal trains, stations_list, blocksections_list
        nonlocal total_schedule, stn_line_occ_name
        nonlocal previous_train_type, prev_blsec_obj


        stn_line_occ_flag = 0 #indicates whether a station line is free (0) or not (1)
        stn_line_occ_end = pd.Timestamp("2100-06-01 22:50:00")
        stn_line_occ_endtimes = []
        len_sched = len(sched_act[next_event_tr_id]) # find length of schedule for train associated with current event
        t_ind = sched_act[next_event_tr_id].index(t) # index of current event in the schedule

        # arrival event actions
        # arr.1: station update
        # arr.1.1: check whether station line is free at t
        # arr.1.1.a: if a line is free: update station line occupancy, update occupancy of block section from which it has come (if not origin station), update train actual schedule
        # arr.1.1.b: if not: find time at which station line is free, update the next event time for this train (i.e. update its schedule), update block section occupancy, pass control back to main
        if next_event_type == 'a': 
            print('\n event at time t = ', t, ' is arrival of train ', next_event_train, ' at station', stns_event[0].name)
            t_end = sched_act[next_event_tr_id][t_ind + 1] # find the time at which station halt ends
            print('\n scheduled station halt end time is: ', t_end)
            stn_line = stn_line_assign(t_ind, next_event_tr_id, len_sched) 
            print('\n station line assignment information: ', stn_line)

            # if it is arrrival at origin station, then no need to update block section occupancy from which it has come
            # and then if station line is not free, then find the minimum of all end times of occupied station lines
            # and update the next event time for this train (i.e. update its schedule)
            stn_line_occ_flag = stn_line[0]
            if stn_line_occ_flag == 0: # if free station line is not found
                is_origin_stn = (t_ind == 1)

                if is_origin_stn: # if origin station 
                    min_endtime= get_min_endtime(stns_event[0], t_ind, t_ind==1)
                    new_arr_time= min_endtime + pd.Timedelta(minutes=1) 
                    # guard: get_min_endtime can fall back to its not-found sentinel, which
                    # would otherwise let new_arr_time land at or before t (no progress) and
                    # make this arrival event get reselected and reprocessed forever.
                    if new_arr_time <= t:
                        new_arr_time = t + pd.Timedelta(minutes=1)
                    sched_updt(new_arr_time, t_ind, next_event_tr_id) #update schedule for the train 
                    t_max = term_crit_calc() # update simulation termination time point

                else: # if not origin station and get the minimum end time 
                    min_endtime= get_min_endtime(stns_event[0], t_ind, t_ind==1)
                    print('min end time is ', min_endtime)
                    # update schedules of all trains in the queue for this block section
                    new_arr_time = min_endtime + pd.Timedelta(minutes=1) # add 1 minute after the station line becomes free
                    # guard: get_min_endtime can fall back to its not-found sentinel, which
                    # would otherwise let new_arr_time land at or before t (no progress) and
                    # make this arrival event get reselected and reprocessed forever.
                    if new_arr_time <= t:
                        new_arr_time = t + pd.Timedelta(minutes=1)
                    new_occ_inc = new_arr_time - t   # new occupancy increament
                    print('\n new occ increament: ', new_occ_inc)
                    sched_updt(new_arr_time, t_ind, next_event_tr_id) #update schedule for the train
                    #print('\n updated schedule for train ', next_event_tr_id, ' is: \n', sched_act[next_event_tr_id])
                    blsec_t.train_occ_updt(new_arr_time, 1) #here 1 means occupied, update schedule for the block section
                    print('\n block section ', blsec_t.name, ' will be occupied by train ', next_event_train, 'until ', new_arr_time)

                    # if queue exists for the given blocksction; update all the events according to the time increament 
                    if len(blsec_t.blsec_queue) > 0:
                            q_len = len(blsec_t.blsec_queue)
                            # store the train ids of the trains in the queue to update their schedules and station line occupancies.
                            q_tr_id = []
                            v = 0 
                            while v < q_len:
                                if blsec_t.blsec_queue[v] in sched_act:
                                    q_tr_id.append(blsec_t.blsec_queue[v])
                                # v+=4
                                v+=6  # as each entry in the queue has 6 elements

                            # before pushing every queued train further back by new_occ_inc,
                            # see if any of them can escape onto a free, unqueued sibling
                            # block section instead of waiting out blsec_t's growing delay
                            # (blsec_t just got held up because the destination station has
                            # no free line -- that shouldn't also jam trains that could take
                            # an idle parallel track). Checked here, before queue_updt/the
                            # shift loop below, so a redirected train is rescheduled fresh
                            # (via sched_updt) rather than shifted and then overridden.
                            redirected = []
                            # direction these queued trains actually need, same station pair
                            # and formula blsec_t itself was derived from (stns_event[1] ->
                            # stns_event[0], the crossing they're all waiting to make) -- a
                            # sibling running the opposite way must never be handed out here.

                            # redirected will collect the train ids of the trains to the sibling block section; so that they can be removed from the queue of the current block section.
                            # _queue_dir  figures out which physical direction ('up' or 'dn') these queued trains actually need to travel,

                            _queue_dir = 'up' if station_longitudes[stns_event[1].name] > station_longitudes[stns_event[0].name] else 'dn'
                            for k in q_tr_id:
                                train_name_r = k[:k.index("_")]
                                stn_line_stn0_r = get_train_stnline_for_arrival_delay(stns_event, train_name_r)
                                stn_line_stn1_r = get_train_stnline_for_departure_delay(stns_event, train_name_r)
                                if stn_line_stn0_r is not None: 
                                    redirect_stn_obj, redirect_stn_line = stns_event[1], stn_line_stn0_r
                                elif stn_line_stn1_r is not None:
                                    redirect_stn_obj, redirect_stn_line = stns_event[0], stn_line_stn1_r
                                else:
                                    redirect_stn_obj, redirect_stn_line = None, None
                                sib = (find_free_sibling_blsec(blsec_t, redirect_stn_obj, redirect_stn_line, train_dir=_queue_dir)
                                       if redirect_stn_obj is not None else None)
                                if sib is not None:  
                                    qi = blsec_t.blsec_queue.index(k)
                                    tr_index_q = blsec_t.blsec_queue[qi + 3]
                                    print('queued train', k, 'redirected off still-delayed', blsec_t.name,
                                          '-> free sibling', sib.name, 'is available')
                                    blsec_t.queue_remove([k])
                                    sched_updt(t + pd.Timedelta(minutes=1), tr_index_q, k)
                                    redirected.append(k)
                            q_tr_id = [k for k in q_tr_id if k not in redirected]

                            blsec_t.queue_updt(new_occ_inc)
                            print('\n list of train schedules from queue to be updated: ', q_tr_id)
                            for k in q_tr_id:
                                u = 0
                                for l in sched_act[k]:
                                    if isinstance(l, str) == False and l < pd.Timestamp("2100-06-01 22:50:00"):
                                        sched_act[k][u]= l + new_occ_inc
                                    u+=1
                                #print('\n updated schedule of train', k, ' is: ', sched_act[k])

                                train_name= k[:k.index("_")]  
                                # check which station the queued train is sitting at
                                # get the station line at which the given train id is sitting at;

                                # both stnline arrival and departure delay is called because it will handle both unidirectional and bidirectional cases
                                stn_line_stn0 = get_train_stnline_for_arrival_delay(stns_event, train_name)  # checks stns_event[1]
                                stn_line_stn1 = get_train_stnline_for_departure_delay(stns_event, train_name)  # checks stns_event[0]
                                # stn_line= get_train_stnline_for_arrival_delay(stns_event, train_name)
                                print('station line is ', stn_line_stn0, stn_line_stn1)
                                if stn_line_stn0 is not None:
                                    # train is at stns_event[1] (the arrival station)
                                    updt_dep_time = stns_event[1].tracks[stn_line_stn0][3] + new_occ_inc
                                    stns_event[1].set_occupancy_updt(stn_line_stn0, updt_dep_time)
                                    print(f'[queue update] train {train_name} at {stns_event[1].name}, stn line {stn_line_stn0}, updated occ_end to {updt_dep_time}')

                                elif stn_line_stn1 is not None: 
                                    # train is at stns_event[0] (the departure station, bidirectional case)
                                    updt_dep_time = stns_event[0].tracks[stn_line_stn1][3] + new_occ_inc
                                    stns_event[0].set_occupancy_updt(stn_line_stn1, updt_dep_time)
                                    print(f'[queue update] train {train_name} at {stns_event[0].name}, stn line {stn_line_stn1}, updated occ_end to {updt_dep_time}')

                                else:
                                    print(f'[queue update] train {train_name} not found at either station, skipping station line update')
                                # print('station line to updated name is ', stn_line)
                                # print('stns event list is ', stns_event[0].name, stns_event[1].name)
                                # updt_dep_time= stns_event[1].tracks[stn_line][3] + new_occ_inc
                                # stns_event[1].set_occupancy_updt(stn_line, updt_dep_time)
                            print('\n updated block section queue status: \n', blsec_t.blsec_queue)

                    #if below is added in queue then also make provision to remove it from queue in arrival case of station line is free
                    # blsec_t.blsec_queue[0:0] = [next_event_tr_id, next_event_train, tr_next_event.tr_type, t_ind, t, new_arr_time]

                    print('\n updated block section queue status after adding current event train at starting: \n', blsec_t.blsec_queue)
                    # put this event in queue at the starting only
                    t_max = term_crit_calc() # update simulation termination time point
                    print('\n updated time at which simulation terminates: ', t_max)


                    # when station line is not free, update the autoblocksection list events
                    if not is_origin_stn:
                        if len(blsec_t.autoblsec_list) > 0:
                            check_if_auto =autoblsec_check()
                            if next_event_tr_id == blsec_t.autoblsec_list[0][0] and check_if_auto:
                                # update the autoblock section list event for this train
                                blsec_t.autoblsecsection_trains_updt(new_occ_inc)  # new_occ_inc is the time incremenntn to be added
                                print('\n updated autoblock section list for block section ', blsec_t.name, ' is now ', blsec_t.autoblsec_list)
                                # also update their individual train schedule
                                # get the train id from autoblock section list using for loop
                                for lst in blsec_t.autoblsec_list:
                                    print('\n updating individual train schedule for train ', lst)
                                    tr_id = lst[0]
                                    new_arr_time = lst[4] # this is a arrival time at the next station
                                    print('\n new arrival time after updating autoblock section list is: ', new_arr_time)
                                    new_ind = lst[2]  # this is the index position of arrival time in the schedule
                                    print('\n index position: ', new_ind, t_ind)
                                    sched_updt(pd.Timestamp(new_arr_time), new_ind, tr_id)
                    t_max = term_crit_calc()

            else:
                # station line is free
                stn_line_occ_name = stn_line[1] # which station line is occupied
                # ADD RANDOMNESS TO HALT DURATION
                original_halt_duration = t_end - t      # in timedelta format
                # print('original_halt_duration: ', original_halt_duration)
                Y = add_halt_randomness()
                new_halt_duration = original_halt_duration + pd.Timedelta(minutes=Y)
                t_end_new = t + new_halt_duration
                t_end_new = t_end_new.replace(microsecond=0)
                if t_end_new < t:
                    t_end_new = t  # prevent departure scheduled before arrival due to sub-microsecond precision in t
                print('\n new station halt duration after adding randomness is: ', new_halt_duration, 'and', Y)
                stns_event[0].set_occupancy_arr(stn_line_occ_name, t, t_end_new, tr_next_event.train_id) # update station line occupancy in station object
                stns_event[0].set_occupancy_updt(stn_line[1], t_end_new) # update stn line - blsec connection occupancy

                sched_updt(t_end_new, t_ind + 1, next_event_tr_id) 
                # t_max = term_crit_calc() # update simulation termination time point
                # sync_individual_schedule_from_global(tr_next_event, next_event_tr_id)
                # Update individual train schedule
                tr_next_event.tr_sched_act[stns_event[0].name][1] = t_end_new

                # NOTE (halt-deviation fix): this used to force t_end_new back up to the
                # original, un-randomized given_sched departure time whenever the halt-deviation-
                # adjusted t_end_new was earlier than that original schedule -- which silently
                # discarded every negative halt deviation (train departs earlier/on-time).
                # Removed so negative deviations from add_halt_randomness actually take effect.
                # t_end_new is already clamped to be >= arrival time t a few lines above
                # (`if t_end_new < t: t_end_new = t`), so a departure before an arrival is
                # still impossible -- the floor is 0-minute halt, not a negative one.

                    #print('\n updated schedule for train ', next_event_tr_id, ' is: \n', sched_act[next_event_tr_id])

                print('\n train arrival event details at ', stns_event[0].name, ' station are:', stns_event[0].tracks[stn_line[1]][2])
                print('\n -----> station line occupied: ', stn_line_occ_name)
                if stns_event[0].tracks[stn_line_occ_name][1] != 0: print('\n -----> platform occupied: ', 'P'+ str(stns_event[0].tracks[stn_line_occ_name][1]))
                if t_ind >= 4: 
                    print('train arrival blocksection is ', blsec_t.name)
                    print('blocksection direction name is ', blsec_t.dir_mvmt)
                    next_event_conn = blsec_t.name + '_' + stn_line_occ_name
                    # next_event_conn = conn_base(stns_event[0].name, stns_event[1].name, blsec_t.dir_mvmt) + '_' + stn_line_occ_name
                    print('connection name is ', next_event_conn) 

                    stns_event[0].set_occ_conn_in(next_event_conn, tr_next_event.train_id, 0) # free up stn line - blsec connection
                    print('\n station line connection ', next_event_conn, ' is now free', stns_event[0].connections[next_event_conn])
                    blsec_t.train_occ_end(t) #free up block section
                    print('\n block section ', blsec_t.name, ' is now free')
                    print('\n prev block section (blsec_t) occupancy status is ', blsec_t.occ_ind)
                    print('\n prev block section occ end time is ', blsec_t.occ_end)
                sched_act[next_event_tr_id][t_ind] = pd.Timestamp("2100-06-01 22:50:00")  # 100002
                tr_sched_updt(t, next_event_type)
                #print('\n desired train schedule: ', tr_next_event.tr_schedule)
                #print('\n updated actual train schedule: ', tr_next_event.tr_sched_act)
                occupancy_end = sched_act[next_event_tr_id][t_ind + 1]
                print('station line ',stn_line_occ_name, 'occ end time at station',stns_event[0].name, ' is ', stns_event[0].tracks[stn_line_occ_name][3])
                stns_event[0].set_occupancy_updt(stn_line_occ_name, occupancy_end)
                # UPDATE stn_line_occ global with station, line and platform for this train
                print('stns evnet length is ', len(stns_event))


                # to remove the train from the autoblock section list; as it arrives at the station
                if len(stns_event) > 1:
                    print('inside to remvoe autoblock train ')
                    print('blocksection name is ', blsec_t.name)
                    check_if_auto=autoblsec_check()
                    if blsec_t.autoblsec_list and next_event_tr_id == blsec_t.autoblsec_list[0][0] and check_if_auto:
                        # remove the train from the autoblock section list
                        blsec_t.autoblsecsection_trains_remove()
                        print('\n train ', next_event_train, ' removed from autoblock section list of block section ', blsec_t.autoblsec_list)
                t_max = term_crit_calc()
                print('t_max is ', t_max)
                # update the total schedule for this train with station line occupancy details
                try: 
                   platform = stns_event[0].tracks[stn_line_occ_name][1]
                except Exception:
                   platform = None
                total_schedule[next_event_tr_id]['simulated'].append([stns_event[0].name, stn_line_occ_name, platform])
                total_schedule[next_event_tr_id]['simulated'].append([t])


        # departure event actions
        # actions to perform for a departure event
            # dep.1. check whether block section is free: if yes, proceed; else update time of departure from station
            # call station method to update occupancy
            # call connection method to update occupancy
            # call block section method to update occupancy

        else:
            print('\n event at time t = ', t, ' is departure of train ', next_event_train, ' from station', stns_event[0].name)
            stn_line_occ_name = ''  # reset before search to avoid stale global value 
            for j in stns_event[0].tracks:
                print('\n station line under consideration for departure event: ', j)
                if stns_event[0].tracks[j][0] == 1 and stns_event[0].tracks[j][5] == tr_next_event.train_id:
                    # print('\n station line information: ', stns_event[0].tracks[j])
                    stn_line_occ_name = j
                    print('\n station line from which train ', next_event_train, ' will depart is ', stn_line_occ_name)

                    break
            print('\n current train sched is ', sched_act[next_event_tr_id])
            if t_ind == len_sched - 1: # if departure event is from the last station in the train schedule; finishes its journey
                stns_event[0].set_occupancy_dep(stn_line_occ_name, t)
                print('\n station line ', stn_line_occ_name, 'at station ', stns_event[0].name, 'will be free starting at t = ', t)
                tr_sched_updt(t, next_event_type)
                sched_act[next_event_tr_id][t_ind] = pd.Timestamp("2100-06-01 22:52:00")
                total_schedule[next_event_tr_id]['simulated'].append([t])

            if t_ind < len_sched - 1:
                # next_event_conn = conn_base(stns_event[0].name, stns_event[1].name, blsec_t.dir_mvmt) + '_' + stn_line_occ_name
                next_event_conn = blsec_t.name + '_' + stn_line_occ_name
                print('departure event connection is ', next_event_conn) 

                # before departing the train; below function checks the category of next blocksecction and current blocksection; if both or one of them is a single line. special conditions are applied
                # this function gives all the occupancy details of next station and blocksection
                # in case of single line(bidirectional blockection) a bottleneck situation may occur hence have to consider all this complexities.
                occ_details = check_next_blse_stn_occupancy(t_ind, len_sched) 
                print('occ_details list is ', occ_details)
                stn1 = stns_event[0].name 
                stn2 = stns_event[1].name # if train is moving from stn1 to stn2; 
                # and if the stn2 is on the east of stn1 means long_diff(stn2 - stn1) positive
                current_train_dir = 1 if station_longitudes[stn2] > station_longitudes[stn1] else 0

                dn_stn_count      = occ_details[0]
                up_stn_count      = occ_details[1]
                count_next_blsec  = occ_details[3]
                count_curr_blsec  = occ_details[4]
                next_blsec_list   = occ_details[5]

                total_stn_lines    = len(stns_event[1].tracks)
                total_stn_occ      = dn_stn_count + up_stn_count
                same_dir_stn_count = dn_stn_count if current_train_dir == 0 else up_stn_count
                free_stn_lines     = total_stn_lines - total_stn_occ

                curr_is_single = (count_curr_blsec == 1)
                next_is_single = (count_next_blsec == 1)

                ready_to_dept = True

                #  Case 1: curr_blsec = SL, next_blsec = SL 
                if curr_is_single and next_is_single:
                    print('both current and next block sections are single line')
                    if free_stn_lines >= 2: # if more than 2 stn liens are free; directly depart the train
                        ready_to_dept = True

                    elif free_stn_lines == 1: # if only one stn line is free; check for other cases
                        print('one stn line is free block')                    
                        blsec_obj, blsec_dir = next_blsec_list[0]
                        print('next block section occupancy status is ', next_blsec_list[0])
                        print('dir and block is', blsec_dir, current_train_dir, blsec_obj.occ_ind)
                        if blsec_obj.occ_ind == 0:
                            ready_to_dept = True
                        elif blsec_dir == current_train_dir and blsec_obj.occ_ind == 1: # if next blsec is occupied; but have direction like given train; depart the train
                            ready_to_dept = True
                        else:
                            ready_to_dept = False

                    elif free_stn_lines == 0: # all next stations_list station lines are occupied
                        if same_dir_stn_count == 0: # all having opposite dir trains; do not depart
                            ready_to_dept = False
                        else:
                            blsec_obj, blsec_dir = next_blsec_list[0]
                            if blsec_obj.occ_ind == 0: # at least one is free and next blsec is free
                                ready_to_dept = True
                            elif blsec_dir == current_train_dir: # if next blsec is occupied but having same dir depart the train
                                ready_to_dept = True
                            else:
                                # update the sched and stn occupancy with new halt end time
                                ready_to_dept = False

                #  Case 2: curr_blsec = SL, next_blsec = DL 
                elif curr_is_single and not next_is_single:
                    print('current block section is single line and next block section is double line')

                    if free_stn_lines >= 2:
                        # two or more free station lines -> depart freely
                        ready_to_dept = True

                    elif free_stn_lines == 1:
                        # exactly one station line is free -> check next blsec occupancy
                        free_blsec_count  = sum(1 for b in next_blsec_list if b[0].occ_ind == 0)
                        same_dir_blsec_count = sum(1 for b in next_blsec_list if b[1] == current_train_dir)

                        if free_blsec_count == len(next_blsec_list):
                            # both blsec lines free; depart
                            ready_to_dept = True

                        elif free_blsec_count >= 1 and same_dir_stn_count >= 1:
                            # at least one blsec free AND at least one stn line has same dir; depart
                            ready_to_dept = True

                        elif same_dir_blsec_count >= 1:
                            # at least one occupied blsec has same dir as given train -> depart
                            ready_to_dept = True

                        else:
                            # all blsec lines occupied by oncoming trains
                            print('the only free station line is occupied by an oncoming train and both lines of the next block section are occupied by oncoming trains, so we need to wait at the station')
                            ready_to_dept = False

                    elif free_stn_lines == 0 and same_dir_stn_count == 0:
                        # all stn lines occupied by opposing trains; halt
                        print('all station lines are occupied by opposing trains, so we need to wait at the station')
                        ready_to_dept = False

                    elif free_stn_lines == 0 and same_dir_stn_count >= 1:
                        # all stn lines occupied but at least one same dir; check blsec
                        same_dir_blsec_count = sum(1 for b in next_blsec_list if b[1] == current_train_dir)
                        if same_dir_blsec_count >= 1:
                            ready_to_dept = True
                        else:
                            print('all station lines are occupied by opposing trains, but at least one train has same direction as given train and both lines of the next block section are occupied by oncoming trains, so we need to wait at the station')
                            ready_to_dept = False

                #  Case 3: curr_blsec = DL, next_blsec = SL 
                elif not curr_is_single and next_is_single:
                    print('current block section is double line and next block section is single line')
                    if free_stn_lines >= 2:
                        ready_to_dept = True
                    elif free_stn_lines == 1:
                        blsec_obj, blsec_dir = next_blsec_list[0]
                        if blsec_obj.occ_ind == 0:
                            ready_to_dept = True
                        elif blsec_dir == current_train_dir:
                            ready_to_dept = True
                        else:
                            print('the only free station line is occupied by an oncoming train and the next block section is single line occupied by an oncoming train, so we need to wait at the station')
                            ready_to_dept = False
                    elif free_stn_lines == 0:
                        if same_dir_stn_count == 0:
                            print('all station lines are occupied by opposing trains, so we need to wait at the station')
                            ready_to_dept = False
                        else:
                            blsec_obj, blsec_dir = next_blsec_list[0]
                            if blsec_obj.occ_ind == 0:
                                ready_to_dept = True
                            elif blsec_dir == current_train_dir:
                                ready_to_dept = True
                            else:
                                print('the only free station line is occupied by an oncoming train and the next block section is single line occupied by an oncoming train, so we need to wait at the station')
                                ready_to_dept = False

                elif ready_to_dept is False:
                    t_max = term_crit_calc()

                #  Case 4: curr_blsec = DL, next_blsec = DL 
                else: # in case double line; we have unidirectional blockscction; striclty handling up and dn direction trains; in this case depart the train
                    # because will always get the dedicated blocksection line depending on the direction
                    ready_to_dept = True
                    print('single line block section case is not found ready to depart True')
                print(f'ready_to_dept={ready_to_dept} | free_stn={free_stn_lines} | same_dir_stn={same_dir_stn_count} | curr_SL={curr_is_single} | next_SL={next_is_single}')




                check_if_auto = autoblsec_check()
                print('autoblock case is result is ', check_if_auto)


                if blsec_t.occ_ind == 0 and len(blsec_t.blsec_queue) == 0 and not check_if_auto and ready_to_dept is True: # blocksection is free and no train is waiting in the queue and this is not the case of autoblsec
                    # check whether passenger train is coming from the previous station if yes and current dept train is
                    # goods train then give priority to passenger train by waiting at the station only and dept time of the goods train will be updated
                    # goods train dept time will be updated based on the time taken by passenger train to cover the next block section
                    # print('/n given train type and t_ind value are: ', tr_next_event.tr_type, t_ind)
                    print('\n case when block free and queue is empty')
                    if t_ind >= 4 and tr_next_event.tr_type == 'g':
                        updt_dep_time= goods_delay_due_to_passenger(sched_act, t, t_ind, next_event_tr_id)
                        original_dep_time= sched_act[next_event_tr_id][t_ind]
                        # goods_delay_due_to_passenger is re-checked fresh every time this event
                        # comes up; with back-to-back passenger traffic it can always find a new
                        # reason to defer, so cap how long this train can be pushed back relative
                        # to its own originally planned departure before priority is overridden.
                        starved_too_long = (t - given_sched[next_event_tr_id][t_ind]) >= GOODS_MAX_PRIORITY_WAIT
                        if starved_too_long:
                            print('goods train', next_event_tr_id, 'has waited', t - given_sched[next_event_tr_id][t_ind],
                                  '-> overriding passenger priority, departing now') 

                        if updt_dep_time != original_dep_time and not check_if_all_goods(t_ind, next_event_tr_id) and not starved_too_long:
                            stns_event[0].set_occupancy_updt(stn_line_occ_name, updt_dep_time + pd.Timedelta(minutes=1))
                            sched_updt(updt_dep_time + pd.Timedelta(minutes=1), t_ind, next_event_tr_id)
                            t_max = term_crit_calc() 

                            print('After consideration of passenger trains at current station, and that coming from prev blsec /n')
                            #print('updated dept time of the goods train is ',sched_act[next_event_tr_id][t_ind])

                        else:
                            #print(sched_act[next_event_tr_id])
                            new_arrival_time= new_arr_by_speed_randomness(next_event_tr_id, t_ind)[0]
                            sched_updt(new_arrival_time, t_ind + 2, next_event_tr_id)
                            t_blsec_occ_end= new_arrival_time - t
                            t_max = term_crit_calc()
                            _expected_dir = 'up' if station_longitudes[stns_event[0].name] > station_longitudes[stns_event[1].name] else 'dn'
                            assert blsec_t.dir_mvmt[0:2] == _expected_dir or blsec_t.dir_mvmt[0:3] == 'mid', (
                                f"direction mismatch: train {next_event_tr_id} departing "
                                f"{stns_event[0].name}->{stns_event[1].name} (expected dir {_expected_dir!r}) "
                                f"about to occupy {blsec_t.name} (dir_mvmt={blsec_t.dir_mvmt!r})"
                            )
                            blsec_t.train_occ_start(t, t + t_blsec_occ_end, next_event_tr_id) # update block section occupancy

                            print('\n block section ', blsec_t.name, ' will be occupied by train ', next_event_train, ' until ', new_arrival_time)
                            stns_event[0].set_occ_conn_out(next_event_conn, tr_next_event.train_id, 1)
                            print ('\n train ', next_event_train, 'departing station ', stns_event[0].name, ' from connection ', next_event_conn)
                            stns_event[0].set_occupancy_dep(stn_line_occ_name, t)
                            print('\n station line ', stn_line_occ_name, 'at station ', stns_event[0].name, 'will be free starting at t = ', t)
                            tr_sched_updt(t, next_event_type)
                            #print('\n desired train schedule: ', tr_next_event.tr_schedule)
                            #print('\n updated actual train schedule: ', tr_next_event.tr_sched_act)
                            sched_act[next_event_tr_id][t_ind] = pd.Timestamp("2100-06-01 22:52:00")   # 100002
                            print('\n block section ', blsec_t.name, 'queue status: ', blsec_t.blsec_queue)
                            total_schedule[next_event_tr_id]['simulated'].append([t])

                    else:
                        #print(sched_act[next_event_tr_id])
                        new_arrival_time= new_arr_by_speed_randomness(next_event_tr_id, t_ind)[0]
                        sched_updt(new_arrival_time, t_ind + 2, next_event_tr_id)
                        t_blsec_occ_end= new_arrival_time - t
                        t_max = term_crit_calc()
                        _expected_dir = 'up' if station_longitudes[stns_event[0].name] > station_longitudes[stns_event[1].name] else 'dn'
                        assert blsec_t.dir_mvmt[0:2] == _expected_dir or blsec_t.dir_mvmt[0:3] == 'mid', (
                            f"direction mismatch: train {next_event_tr_id} departing "
                            f"{stns_event[0].name}->{stns_event[1].name} (expected dir {_expected_dir!r}) "
                            f"about to occupy {blsec_t.name} (dir_mvmt={blsec_t.dir_mvmt!r})"
                        )
                        blsec_t.train_occ_start(t, t + t_blsec_occ_end, next_event_tr_id) # update block section occupancy
                        print('\n block section ', blsec_t.name, ' will be occupied by train ', next_event_train, ' until ', new_arrival_time)
                        stns_event[0].set_occ_conn_out(next_event_conn, tr_next_event.train_id, 1)
                        print ('\n train ', next_event_train, 'departing station ', stns_event[0].name, ' from connection ', next_event_conn)
                        stns_event[0].set_occupancy_dep(stn_line_occ_name, t)
                        print('\n station line ', stn_line_occ_name, 'at station ', stns_event[0].name, 'will be free starting at t = ', t)
                        tr_sched_updt(t, next_event_type)
                        #print('\n desired train schedule: ', tr_next_event.tr_schedule)
                        #print('\n updated actual train schedule: ', tr_next_event.tr_sched_act)
                        sched_act[next_event_tr_id][t_ind] = pd.Timestamp("2100-06-01 22:52:00")   # 100002
                        print('\n block section ', blsec_t.name, 'queue status: ', blsec_t.blsec_queue)
                        total_schedule[next_event_tr_id]['simulated'].append([t])


                # blocksection is free and queue is not empty.
                # bring the event from the queue and depart that initial train from the queue
                elif blsec_t.occ_ind == 0 and len(blsec_t.blsec_queue) > 0 and not check_if_auto and ready_to_dept is True:
                    print('when block is free and queue is not empty')
                    # First check given train type (p or g); if 'g' then go ahead with conditions
                    # This will happen only all the trains in the queue are of 'goods' train type
                    if tr_next_event.tr_type == 'g' and t_ind >= 4:
                        # Second step to find the previous blocksection train type
                        updt_dep_time= goods_delay_due_to_passenger(sched_act, t, t_ind, next_event_tr_id)
                        original_dep_time= sched_act[next_event_tr_id][t_ind]
                        # see comment at the other goods_delay_due_to_passenger call site --
                        # cap how long this train can be repeatedly deferred by fresh passenger
                        # conflicts before priority is overridden and it's let through.
                        starved_too_long = (t - given_sched[next_event_tr_id][t_ind]) >= GOODS_MAX_PRIORITY_WAIT
                        if starved_too_long:
                            print('goods train', next_event_tr_id, 'has waited', t - given_sched[next_event_tr_id][t_ind],
                                  '-> overriding passenger priority, departing now')
                        # if arr and dept is not same and not all are goods trains
                        if updt_dep_time != original_dep_time and not check_if_all_goods(t_ind, next_event_tr_id) and not starved_too_long:
                            stns_event[0].set_occupancy_updt(stn_line_occ_name, updt_dep_time + pd.Timedelta(minutes=1))
                            sched_updt(updt_dep_time + pd.Timedelta(minutes=1), t_ind, next_event_tr_id)
                            t_max = term_crit_calc() 

                            print('After consideration of passenger trains at current station, and that coming from prev blsec /n')
                            #print('updated dept time of the goods train is ',sched_act[next_event_tr_id][t_ind])
                            time_increament = updt_dep_time + pd.Timedelta(minutes=1) - t
                            blsec_t.queue_updt(time_increament) # it will update/increase the times of all goods trains present in queue
                            # B) station line departure udpate and schedule dept update
                            # For this first find out the station lines occupied by goods trains; there could be a case where more than goods train have occupied the station lines
                            for i in range(0, len(blsec_t.blsec_queue), 6):
                                trainid, traintype, blsec_occupancy_start  = blsec_t.blsec_queue[i] ,blsec_t.blsec_queue[i+2], blsec_t.blsec_queue[i+4]
                                for line, data in stns_event[0].tracks.items():
                                    print('given train id is ', trainid)
                                    print('goods train data is ', data)
                                    print('goods train station line', line)
                                    if data[-1] == trainid:
                                        stns_event[0].set_occupancy_updt(line, blsec_occupancy_start + pd.Timedelta(minutes=1))
                                        sched_updt(blsec_occupancy_start + pd.Timedelta(minutes=1), blsec_t.blsec_queue[i+3], trainid)
                                        t_max = term_crit_calc()

                        else:
                            # if given train is passenger or all are goods train 
                            # depart the train directly without looking for any condition
                            speed_rand= new_arr_by_speed_randomness(next_event_tr_id, t_ind)
                            new_arrival_time = speed_rand[0]
                            # after adding the randomness for the current train
                            # it will reach to the next station late, so along with shedule update of current trains also update the queue and schedule of the queued trains
                            if len(speed_rand) > 1 and len(blsec_t.blsec_queue) > 6:
                                time_inc = speed_rand[1]
                                # store [train_id, t_ind] for the OTHER trains still waiting in this block
                                # section's queue (exclude the current departing train; its own schedule
                                # is updated separately below). t_ind is the queue's own stored index
                                # (blsec_queue[v+3]), same field used by the other sched_updt call sites.
                                q_len = len(blsec_t.blsec_queue)
                                q_tr_id = []
                                v = 0
                                while v < q_len:
                                    if blsec_t.blsec_queue[v] in sched_act and blsec_t.blsec_queue[v] != next_event_tr_id:
                                        q_tr_id.append([blsec_t.blsec_queue[v], blsec_t.blsec_queue[v+3]])
                                    v += 6  # as each entry in the queue has 6 elements
                                blsec_t.queue_updt(time_inc)
                                print('list of train schedules from queue to be updated due to speed randomness: ', q_tr_id)
                                for k, t_ind_q in q_tr_id:
                                    # update this queued train's own schedule precisely, using its stored index
                                    sched_updt(sched_act[k][t_ind_q] + time_inc, t_ind_q, k)

                                    # also udpate the station line tracks at the station where this queued train is residing
                                    train_name = k[:k.index("_")]
                                    stn_line_stn0 = get_train_stnline_for_arrival_delay(stns_event, train_name)  # checks stns_event[1]
                                    stn_line_stn1 = get_train_stnline_for_departure_delay(stns_event, train_name)  # checks stns_event[0]
                                    if stn_line_stn0 is not None:
                                        # train is at stns_event[1] (the arrival station)
                                        updt_dep_time = stns_event[1].tracks[stn_line_stn0][3] + time_inc
                                        stns_event[1].set_occupancy_updt(stn_line_stn0, updt_dep_time)
                                        print(f'[queue update] train {train_name} at {stns_event[1].name}, stn line {stn_line_stn0}, updated occ_end to {updt_dep_time}')
                                    elif stn_line_stn1 is not None:
                                        # train is at stns_event[0] (the departure station, bidirectional case)
                                        updt_dep_time = stns_event[0].tracks[stn_line_stn1][3] + time_inc
                                        stns_event[0].set_occupancy_updt(stn_line_stn1, updt_dep_time)
                                        print(f'[queue update] train {train_name} at {stns_event[0].name}, stn line {stn_line_stn1}, updated occ_end to {updt_dep_time}')
                                    else:
                                        print(f'[queue update] train {train_name} not found at either station, skipping station line update')
                                print('updated block section queue status due to speed randomness: ', blsec_t.blsec_queue)

                            sched_updt(new_arrival_time, t_ind + 2, next_event_tr_id)
                            t_blsec_occ_end= new_arrival_time - t
                            t_max = term_crit_calc()
                            _expected_dir = 'up' if station_longitudes[stns_event[0].name] > station_longitudes[stns_event[1].name] else 'dn'
                            assert blsec_t.dir_mvmt[0:2] == _expected_dir or blsec_t.dir_mvmt[0:3] == 'mid', (
                                f"direction mismatch: train {next_event_tr_id} departing "
                                f"{stns_event[0].name}->{stns_event[1].name} (expected dir {_expected_dir!r}) "
                                f"about to occupy {blsec_t.name} (dir_mvmt={blsec_t.dir_mvmt!r})"
                            )
                            _expected_dir = 'up' if station_longitudes[stns_event[0].name] > station_longitudes[stns_event[1].name] else 'dn'
                            assert blsec_t.dir_mvmt[0:2] == _expected_dir or blsec_t.dir_mvmt[0:3] == 'mid', (
                            f"direction mismatch: train {next_event_tr_id} departing "
                            f"{stns_event[0].name}->{stns_event[1].name} (expected dir {_expected_dir!r}) "
                            f"about to occupy {blsec_t.name} (dir_mvmt={blsec_t.dir_mvmt!r})"
                            )
                            blsec_t.train_occ_start(t, t + t_blsec_occ_end, next_event_tr_id) # update block section occupancy

                            print('\n block section ', blsec_t.name, ' will be occupied by train ', next_event_train, ' until ', new_arrival_time)
                            stns_event[0].set_occ_conn_out(next_event_conn, tr_next_event.train_id, 1)
                            print ('\n train ', next_event_train, 'departing station ', stns_event[0].name, ' from connection ', next_event_conn)
                            stns_event[0].set_occupancy_dep(stn_line_occ_name, t)
                            print('\n station line ', stn_line_occ_name, 'at station ', stns_event[0].name, 'will be free starting at t = ', t)
                            tr_sched_updt(t, next_event_type)
                            #print('\n desired train schedule: ', tr_next_event.tr_schedule)
                            #print('\n updated actual train schedule: ', tr_next_event.tr_sched_act)
                            sched_act[next_event_tr_id][t_ind] = pd.Timestamp("2100-06-01 22:52:00")   # 100002
                            t_index = t_ind
                            dep_list = [next_event_tr_id, next_event_train, tr_next_event.tr_type, t_index,t, sched_act[next_event_tr_id][t_ind + 2]]
                            blsec_t.queue_remove(dep_list)
                            print('\n block section ', blsec_t.name, 'queue status: ', blsec_t.blsec_queue)
                            print('current train sched is ', sched_act[next_event_tr_id])
                            total_schedule[next_event_tr_id]['simulated'].append([t])



                    # if train type is passenger depart 
                    else:
                        speed_rand = new_arr_by_speed_randomness(next_event_tr_id, t_ind)
                        new_arrival_time = speed_rand[0]
                        # after adding the randomness for the current train, it may reach the next
                        # station late, so besides updating this train's own schedule below, also shift
                        # the queue, schedules and station line tracks of other trains still waiting here
                        if len(speed_rand) > 1 and len(blsec_t.blsec_queue) > 6:
                            time_inc = speed_rand[1]
                            # store [train_id, t_ind] for the OTHER trains still waiting in this block
                            # section's queue; t_ind is the queue's own stored index (blsec_queue[v+3]).
                            q_len = len(blsec_t.blsec_queue)
                            q_tr_id = [] # appending the train id and train index 
                            v = 0
                            while v < q_len:
                                if blsec_t.blsec_queue[v] in sched_act and blsec_t.blsec_queue[v] != next_event_tr_id:
                                    q_tr_id.append([blsec_t.blsec_queue[v], blsec_t.blsec_queue[v+3]])
                                v += 6  # as each entry in the queue has 6 elements
                            blsec_t.queue_updt(time_inc) # udpate the queue 
                            print('list of train schedules from queue to be updated due to speed randomness: ', q_tr_id)
                            for k, t_ind_q in q_tr_id:
                                # update this queued train's own schedule precisely, using its stored index
                                sched_updt(sched_act[k][t_ind_q] + time_inc, t_ind_q, k)


                                # now udpate the station line times of each train 
                                train_name = k[:k.index("_")]
                                stn_line_stn0 = get_train_stnline_for_arrival_delay(stns_event, train_name)  # checks stns_event[1]
                                stn_line_stn1 = get_train_stnline_for_departure_delay(stns_event, train_name)  # checks stns_event[0]
                                if stn_line_stn0 is not None:
                                    updt_dep_time = stns_event[1].tracks[stn_line_stn0][3] + time_inc
                                    stns_event[1].set_occupancy_updt(stn_line_stn0, updt_dep_time)
                                    print(f'[queue update] train {train_name} at {stns_event[1].name}, stn line {stn_line_stn0}, updated occ_end to {updt_dep_time}')
                                elif stn_line_stn1 is not None:
                                    updt_dep_time = stns_event[0].tracks[stn_line_stn1][3] + time_inc
                                    stns_event[0].set_occupancy_updt(stn_line_stn1, updt_dep_time)
                                    print(f'[queue update] train {train_name} at {stns_event[0].name}, stn line {stn_line_stn1}, updated occ_end to {updt_dep_time}')
                                else:
                                    print(f'[queue update] train {train_name} not found at either station, skipping station line update')
                            print('updated block section queue status due to speed randomness: ', blsec_t.blsec_queue)
                        sched_updt(new_arrival_time, t_ind + 2, next_event_tr_id)
                        print('new arrival time is ', new_arrival_time)
                        print('after schedule update for arrival time, schedule is ', sched_act[next_event_tr_id])
                        t_blsec_occ_end= new_arrival_time - t
                        t_max = term_crit_calc() 
                        _expected_dir = 'up' if station_longitudes[stns_event[0].name] > station_longitudes[stns_event[1].name] else 'dn'
                        assert blsec_t.dir_mvmt[0:2] == _expected_dir or blsec_t.dir_mvmt[0:3] == 'mid', (
                            f"direction mismatch: train {next_event_tr_id} departing "
                            f"{stns_event[0].name}->{stns_event[1].name} (expected dir {_expected_dir!r}) "
                            f"about to occupy {blsec_t.name} (dir_mvmt={blsec_t.dir_mvmt!r})"
                        )
                        blsec_t.train_occ_start(t, t + t_blsec_occ_end, next_event_tr_id) # update block section occupancy
                        print('\n block section ', blsec_t.name, ' will be occupied by train ', next_event_train, ' until ', t + t_blsec_occ_end)
                        stns_event[0].set_occ_conn_out(next_event_conn, tr_next_event.train_id, 1)
                        print ('\n train ', next_event_train, 'departing station ', stns_event[0].name, ' from connection ', next_event_conn)
                        print(stns_event[0].tracks[stn_line_occ_name][0] if stn_line_occ_name in stns_event[0].tracks else 'N/A (train has no station track)')
                        stns_event[0].set_occupancy_dep(stn_line_occ_name, t)
                        print('\n station line ', stn_line_occ_name, 'at station ', stns_event[0].name, 'will be free starting at t = ', t)
                        print(stns_event[0].tracks[stn_line_occ_name][0] if stn_line_occ_name in stns_event[0].tracks else 'N/A (train has no station track)')
                        tr_sched_updt(t, next_event_type)
                        #print('\n desired train schedule: ', tr_next_event.tr_schedule)
                        #print('\n updated actual train schedule: ', tr_next_event.tr_sched_act)
                        sched_act[next_event_tr_id][t_ind] = pd.Timestamp("2100-06-01 22:52:00")  # 100002
                        t_index = t_ind
                        dep_list = [next_event_tr_id, next_event_train, tr_next_event.tr_type, t_index,t, sched_act[next_event_tr_id][t_ind + 2]]
                        blsec_t.queue_remove(dep_list)
                        print('\n block section ', blsec_t.name, 'queue status: ', blsec_t.blsec_queue)

                        total_schedule[next_event_tr_id]['simulated'].append([t])


                # in case of autoblock section; blocksection occupancy start and end are not implemented. 
                # it is purely based on auto block section list
                elif check_if_auto: # proceed if auto block section 
                    print('auto block section name is ', blsec_t.name)
                    if (stns_event[0].name and stns_event[1].name) in autoblock_stations:
                        print('inside the autoblock section case')
                        # 1. block section is completely free
                        # 2. train can easily depart 
                        if len(blsec_t.autoblsec_list) < 1: # check if same blsec_t is to be used or create a new one for this autoblock section class
                            start_time = t
                            end_time = sched_act[next_event_tr_id][t_ind+2]
                            print("blsec_t.length=", blsec_t.length)
                            print("duration=", end_time-start_time)
                            speed = blsec_t.length / ((end_time - start_time).total_seconds() / 3600) # speed in km/hr
                            print('calculated speed for autoblock section is ', speed)
                            # here t_ind+1 is occupancy end time index
                            blsec_t.autoblsecsection_trains([next_event_tr_id, speed,t_ind+2, start_time, end_time])
                            tr_sched_updt(t, next_event_type)
                            sched_act[next_event_tr_id][t_ind] = pd.Timestamp("2100-06-01 22:52:00")
                            occupancy_end = sched_act[next_event_tr_id][t_ind+1]
                            stns_event[0].set_occ_conn_out(next_event_conn, tr_next_event.train_id, 1)
                            stns_event[0].set_occupancy_dep(stn_line_occ_name, t)

                            total_schedule[next_event_tr_id]['simulated'].append([t])
                            print('autoblock section case list', blsec_t.autoblsec_list)


                        # 2. blocks section is occupied
                        # 2.a. check the safe distance is attained if yes proceed
                        # 2.b. if not attained then delay the train departure time
                        elif len(blsec_t.autoblsec_list) >= 1 :
                            last_train_speed = blsec_t.autoblsec_list[-1][1] # get the speed of the last train in the autoblock section
                            print("blsec_t.length=", blsec_t.length)
                            print("duration=", sched_act[next_event_tr_id][t_ind+2] - t)
                            current_train_speed = blsec_t.length / ((sched_act[next_event_tr_id][t_ind+2] - t).total_seconds() / 3600) # speed in km/hr
                            print('last train speed in autoblock section is ', last_train_speed, 'current train speed is ', current_train_speed)
                            # find the time taken to cover the safe distance (3.6 km)
                            time_taken_by_last_train = 3.6 / last_train_speed # time is in hr
                            print('time taken by last train to cover 3.6km safe distance is ', time_taken_by_last_train, ' hr')
                            print(pd.Timedelta(hours=time_taken_by_last_train), pd.Timedelta(hours=time_taken_by_last_train).total_seconds()/60)
                            print(blsec_t.autoblsec_list[-1][3], type(blsec_t.autoblsec_list[-1][3])) 
                            # autoblsec_list[-1][3] = is the last trains dept time 
                            # last_train_time_to_safe_distance = before leaving the train this much distance should have maintained
                            last_train_time_to_safe_distance = blsec_t.autoblsec_list[-1][3] + pd.Timedelta(hours=time_taken_by_last_train)
                            print("delay in minutes is", pd.Timedelta(hours= time_taken_by_last_train).total_seconds()/60)
                            print('last train time to safe distance is ', last_train_time_to_safe_distance)
                            if tr_next_event.tr_type=='p':
                                if last_train_speed > current_train_speed:
                                # if last train speed is greater than current train speed; then very easily soon safe distane of 3.6km will be achieved
                                    print('inside the condition when last train speed > current train speed')
                                    # calculate the end time of this current train
                                    if t >= last_train_time_to_safe_distance: 
                                        # safe distance is maintained; because current time is more than the safe time 
                                        blsec_start_time = t
                                        end_time = sched_act[next_event_tr_id][t_ind+2]
                                        speed = blsec_t.length / ((end_time - t).total_seconds() / 3600) # speed in km/hr
                                        # add a train in autoblocksection list 
                                        blsec_t.autoblsecsection_trains([next_event_tr_id, speed,t_ind+2, blsec_start_time, end_time])
                                        sched_act[next_event_tr_id][t_ind] = pd.Timestamp("2100-06-01 22:52:00")
                                        occupancy_end = sched_act[next_event_tr_id][t_ind+1]
                                        stns_event[0].set_occupancy_dep(stn_line_occ_name, t)
                                        stns_event[0].set_occ_conn_out(next_event_conn, tr_next_event.train_id, 1)
                                        tr_sched_updt(t, next_event_type)
                                        # stns_event[0].set_occupancy_updt(stn_line_occ_name, occupancy_end)
                                        print('autoblock section list', blsec_t.autoblsec_list)
                                        total_schedule[next_event_tr_id]['simulated'].append([t])
                                    else: # first/last train has not covered 3.6km distance yet
                                        # delay the train departure time till the 3.6 km is covered
                                        print("Case of departure delay")
                                        dept_time = last_train_time_to_safe_distance
                                        stns_event[0].set_occupancy_updt(stn_line_occ_name, dept_time)
                                        sched_updt(dept_time, t_ind, next_event_tr_id)
                                        tr_sched_updt(dept_time, next_event_type)
                                        print('autoblock section list', blsec_t.autoblsec_list)
                                        # stns_event[0].set_occupancy_updt(stn_line_occ_name, occupancy_end)
                                elif last_train_speed == current_train_speed:
                                        print('inside the condition when last train speed = current train speed')
                                        # calculate the distance between the two trains if it is greater than or equal to 3.6km then let the train proceed
                                        if t >= last_train_time_to_safe_distance: 
                                            # both trains having the same sppeed and safe distance is also maintained 
                                            # so depart the train directly 
                                            blsec_start_time = t
                                            end_time = sched_act[next_event_tr_id][t_ind+2]
                                            speed = blsec_t.length / ((end_time - t).total_seconds() / 3600) # speed in km/hr
                                            blsec_t.autoblsecsection_trains([next_event_tr_id, speed,t_ind+2, blsec_start_time, end_time])
                                            sched_act[next_event_tr_id][t_ind] = pd.Timestamp("2100-06-01 22:52:00")
                                            occupancy_end = sched_act[next_event_tr_id][t_ind+1]
                                            stns_event[0].set_occupancy_dep(stn_line_occ_name, t)
                                            stns_event[0].set_occ_conn_out(next_event_conn, tr_next_event.train_id, 1)
                                            tr_sched_updt(t, next_event_type)
                                            # stns_event[0].set_occupancy_updt(stn_line_occ_name, occupancy_end)
                                            print('autoblock section list', blsec_t.autoblsec_list)
                                            total_schedule[next_event_tr_id]['simulated'].append([t])
                                        else: # first/last train has not covered 3.6km distance yet
                                            # delay the train departure time; till 3.6 km distance is achieved
                                            dept_time = last_train_time_to_safe_distance
                                            stns_event[0].set_occupancy_updt(stn_line_occ_name, dept_time)
                                            sched_updt(dept_time, t_ind, next_event_tr_id)
                                            tr_sched_updt(t, next_event_type)
                                            print('autoblock section list', blsec_t.autoblsec_list)
                                elif last_train_speed < current_train_speed:
                                    print('inside the condition when last train spped < current train speed')
                                    # find the td2 considering the whole distance to be covered
                                    t_d1 = pd.Timestamp(blsec_t.autoblsec_list[-1][3])
                                    print('t_d1 value is ', t_d1)
                                    print('t_d1 is which is previous trains dept time is', t_d1)
                                    print('type of t_d1 is', type(t_d1))
                                    # t_d2 is the safe distance after which only current train should depart; becasue current train speed is more than last train. 
                                    t_d2 = t_d1 + pd.Timedelta(hours=((blsec_t.length / last_train_speed) - (blsec_t.length - headway_distance)/ current_train_speed)) # some distance related calculations
                                    print('calculated t_d2 is ', t_d2)
                                    print('type of t_d2 is', type(t_d2))
                                    # t_d2 is that safe time at which second train can depart
                                    # finding the sppeed of a train based on blsec lenght and time taken to cover it based on scheduled timetable. 
                                    speed = blsec_t.length / ((sched_act[next_event_tr_id][t_ind+2] - t).total_seconds() / 3600) # speed in km/hr
                                    print('calculated speed for autoblock section is ', speed)
                                    if t_d2 <= t:
                                        # safe distace is already achieved so, depart the train 
                                        print('case when t_d2 <= t')
                                        blsec_start_time = t
                                        sched_act[next_event_tr_id][t_ind] = pd.Timestamp("2100-06-01 22:50:00")
                                        # stns_event[0].set_occupancy_updt(stn_line_occ_name, occupancy_end)
                                        end_time = sched_act[next_event_tr_id][t_ind+2]
                                        stns_event[0].set_occupancy_dep(stn_line_occ_name, t)
                                        stns_event[0].set_occ_conn_out(next_event_conn, tr_next_event.train_id, 1)
                                        # adding the train in autoblocksection list to track the record.
                                        blsec_t.autoblsecsection_trains([next_event_tr_id, speed, t_ind+2, blsec_start_time, end_time])
                                        tr_sched_updt(t, next_event_type)
                                        print('train added in autoblock section list is ', blsec_t.autoblsec_list)
                                        #print('actual schedule after updation is ', sched_act[next_event_tr_id])
                                        total_schedule[next_event_tr_id]['simulated'].append([t])
                                    else:
                                        # delay the train departure time; till t_d2 distance is achieved 
                                        print('case when t_d2 > t; means train got delayed')
                                        dept_time = t_d2
                                        stns_event[0].set_occupancy_updt(stn_line_occ_name, dept_time)
                                        sched_updt(dept_time, t_ind, next_event_tr_id)
                                        tr_sched_updt(dept_time, next_event_type)
                                        #print('actual schedule after updation is ', sched_act[next_event_tr_id])

                            if tr_next_event.tr_type=='g':
                                print("Given train is Goods")
                                if last_train_speed > current_train_speed:
                                # if last train speed is greater than current train speed; then very easily soon safe distane of 3.6km will be achieved
                                    print('inside the condition when last train speed > current train speed')
                                    # calculate the end time of this current train
                                    if t >= last_train_time_to_safe_distance:
                                        blsec_start_time = t
                                        end_time = sched_act[next_event_tr_id][t_ind+2]
                                        speed = blsec_t.length / ((end_time - t).total_seconds() / 3600) # speed in km/hr
                                        blsec_t.autoblsecsection_trains([next_event_tr_id, speed,t_ind+2, blsec_start_time, end_time])
                                        sched_act[next_event_tr_id][t_ind] = pd.Timestamp("2100-06-01 22:52:00")
                                        occupancy_end = sched_act[next_event_tr_id][t_ind+1]
                                        stns_event[0].set_occupancy_dep(stn_line_occ_name, t)
                                        stns_event[0].set_occ_conn_out(next_event_conn, tr_next_event.train_id, 1)
                                        tr_sched_updt(t, next_event_type)
                                        # stns_event[0].set_occupancy_updt(stn_line_occ_name, occupancy_end)
                                        print('autoblock section list', blsec_t.autoblsec_list)
                                        total_schedule[next_event_tr_id]['simulated'].append([t])
                                    else: # first/last train has not covered 3.6km distance yet
                                        # delay the train departure time
                                        dept_time = last_train_time_to_safe_distance
                                        stns_event[0].set_occupancy_updt(stn_line_occ_name, dept_time)
                                        sched_updt(dept_time, t_ind, next_event_tr_id)
                                        tr_sched_updt(dept_time, next_event_type)
                                        print('autoblock section list', blsec_t.autoblsec_list)
                                    # stns_event[0].set_occupancy_updt(stn_line_occ_name, occupancy_end)
                                elif last_train_speed == current_train_speed:
                                    print('inside the condition when last train speed = current train speed')
                                # calculate the distance between the two trains if it is greater than or equal to 3.6km then let the train proceed
                                    if t >= last_train_time_to_safe_distance:
                                        blsec_start_time = t
                                        end_time = sched_act[next_event_tr_id][t_ind+2]
                                        speed = blsec_t.length / ((end_time - t).total_seconds() / 3600) # speed in km/hr
                                        blsec_t.autoblsecsection_trains([next_event_tr_id, speed,t_ind+2, blsec_start_time, end_time])
                                        sched_act[next_event_tr_id][t_ind] = pd.Timestamp("2100-06-01 22:52:00")
                                        occupancy_end = sched_act[next_event_tr_id][t_ind+1]
                                        stns_event[0].set_occupancy_dep(stn_line_occ_name, t)
                                        stns_event[0].set_occ_conn_out(next_event_conn, tr_next_event.train_id, 1)
                                        tr_sched_updt(t, next_event_type)
                                        # stns_event[0].set_occupancy_updt(stn_line_occ_name, occupancy_end)
                                        print('autoblock section list', blsec_t.autoblsec_list)
                                        total_schedule[next_event_tr_id]['simulated'].append([t])
                                    else: # first/last train has not covered 3.6km distance yet
                                        # delay the train departure time
                                        dept_time = last_train_time_to_safe_distance
                                        stns_event[0].set_occupancy_updt(stn_line_occ_name, dept_time)
                                        #print(dept_time)
                                        sched_updt(dept_time, t_ind, next_event_tr_id)
                                        #print(sched_act[next_event_tr_id])
                                        tr_sched_updt(t, next_event_type)
                                        print('autoblock section list', blsec_t.autoblsec_list)
                                elif last_train_speed < current_train_speed:
                                    print('inside the condition when last train spped < current train speed')
                                    # find the td2 considering the whole distance to be covered
                                    t_d1 = pd.Timestamp(blsec_t.autoblsec_list[-1][3])
                                    print('t_d1 is which is previous trains dept time is', t_d1)
                                    print('type of t_d1 is', type(t_d1))
                                    t_d2 = t_d1 + pd.Timedelta(hours=((blsec_t.length / last_train_speed) - (blsec_t.length - headway_distance)/ current_train_speed)) # some distance related calculations
                                    print('calculated t_d2 is ', t_d2)
                                    print('type of t_d2 is', type(t_d2))
                                    # t_d2 is that safe time at which second train can depart
                                    speed = blsec_t.length / ((sched_act[next_event_tr_id][t_ind+2] - t).total_seconds() / 3600) # speed in km/hr
                                    print('calculated speed for autoblock section is ', speed)
                                    if t_d2 <= t:
                                        print('case when t_d2 <= t')
                                        blsec_start_time = t 
                                        sched_act[next_event_tr_id][t_ind] = pd.Timestamp("2100-06-01 22:50:00")
                                        # stns_event[0].set_occupancy_updt(stn_line_occ_name, occupancy_end)
                                        end_time = sched_act[next_event_tr_id][t_ind+2]
                                        stns_event[0].set_occupancy_dep(stn_line_occ_name, t)
                                        stns_event[0].set_occ_conn_out(next_event_conn, tr_next_event.train_id, 1)
                                        # sched_updt(t, t_ind,)
                                        blsec_t.autoblsecsection_trains([next_event_tr_id, speed, t_ind+2, blsec_start_time, end_time])
                                        tr_sched_updt(t, next_event_type)
                                        print('train added in autoblock section list is ', blsec_t.autoblsec_list)
                                        #print('actual schedule after updation is ', sched_act[next_event_tr_id])
                                        total_schedule[next_event_tr_id]['simulated'].append([t])
                                    else:
                                        # delay the train departure time
                                        print('case when t_d2 > t; means train got delayed')
                                        dept_time = t_d2
                                        stns_event[0].set_occupancy_updt(stn_line_occ_name, dept_time)
                                        sched_updt(dept_time, t_ind, next_event_tr_id)
                                        tr_sched_updt(dept_time, next_event_type)
                                        #print('actual schedule after updation is ', sched_act[next_event_tr_id])


                # if departure case is not satified; train will be halted at the station line only
                # update schedule and queue for the current train
                elif ready_to_dept is False:
                    new_halt_end = occ_details[2] + pd.Timedelta(minutes=2)
                    if new_halt_end <= t:
                        new_halt_end = t + pd.Timedelta(minutes=1)
                    sched_updt(new_halt_end, t_ind, next_event_tr_id)
                    stns_event[0].set_occupancy_updt(stn_line_occ_name, new_halt_end)

                    if next_event_tr_id in blsec_t.blsec_queue[0::6]:
                        q_idx = blsec_t.blsec_queue.index(next_event_tr_id)
                        blsec_t.blsec_queue[q_idx + 4] = new_halt_end                          # occ_start
                        blsec_t.blsec_queue[q_idx + 5] = sched_act[next_event_tr_id][t_ind + 2]  # occ_end (next-station arrival)
                        print('refreshed stale queue entry for', next_event_tr_id, 'in', blsec_t.name)

                    print('after updating train shced ', sched_act[next_event_tr_id])


                else:            
                    print('\n Third case when blocksection is not free \n ') 
                    # block section not free
                    print('before adding or updating queue; queue status is ',blsec_t.blsec_queue)
                    if blsec_t.occ_ind == 1 and len(blsec_t.blsec_queue) < 6: # means empty queue and block section is occupied
                        t_dep_updt = blsec_t.occ_end + pd.Timedelta(minutes=1) # get the blocksection end time 
                        print(t_dep_updt)
                    elif next_event_tr_id not in blsec_t.blsec_queue:
                        # queue behind the train currently at the back of the queue (its
                        # occ_end is the last element of the flat 6-per-entry blsec_queue
                        # list), not max() over every timestamp ever queued. The old max()
                        # over the whole queue meant a single already-resolved or stale
                        # entry anywhere in the queue could set an ever-growing floor for
                        # every unrelated train that later queued here -- delay from one
                        # train would permanently propagate onto trains that never
                        # actually conflicted with it, compounding without bound.
                        last_queued_occ_end = blsec_t.blsec_queue[-1]
                        t_dep_updt = max(last_queued_occ_end + pd.Timedelta(minutes=1), blsec_t.occ_end + pd.Timedelta(minutes=1)) # To handle, the case wherein, the train in queue has departure before that in blsec due to order in which the schedule is passed. (Both trains would have the same departure timestamp, and so, the difference would come due to order of listing (Nature of Python))
                    else: 
                        t_dep_updt = blsec_t.occ_end + pd.Timedelta(minutes=1)



                    # guard: without this, a stale/equal blsec_t.occ_end can make t_dep_updt
                    # equal to (or earlier than) the current event time t, so sched_updt below
                    # becomes a zero/backward update and this exact (train, departure) event
                    # gets reselected and reprocessed forever at the same simulation clock time.

                    if t_dep_updt <= t:
                        t_dep_updt = t + pd.Timedelta(minutes=1)




                    print('\n block section ', blsec_t.name, ' is not free at t = ', t)
                    print('\n block section currently occupied by ', blsec_t.occ_train)
                    # now get the up1 and dn1 then use them to get the their objects after this i have to get the occ_train and occ_end for thei same


                    # e.g. blsec_t.name = 'jmpt_knrt_mid1'
                    print('\n current block section is ', blsec_t.name)
                    base = '_'.join(blsec_t.name.split('_')[:-1])   # 'mid1' removed -> base = 'jmpt_knrt'

                    for suffix in ('up1', 'dn1'):
                        sib_name = f'{base}_{suffix}'               # 'jmpt_knrt_up1', 'jmpt_knrt_dn1'
                        sib = blsec_lookup.get(sib_name)
                        if sib is not None:
                            print(sib.name, '| occ_train:', sib.occ_train, '| occ_end:', sib.occ_end)



                    print('\n block section ', blsec_t.name, ' will become free for ', next_event_tr_id, ' at t = ', t_dep_updt - pd.Timedelta(minutes=1))
                    stns_event[0].set_occupancy_updt(stn_line_occ_name, t_dep_updt) # update the stn line; occupied by current train.

                    sched_updt(t_dep_updt, t_ind, next_event_tr_id) 
                    print('current train sched is ', sched_act[next_event_tr_id]) 
                    blsec_occ_end = sched_act[next_event_tr_id][t_ind+2] # means this is the arrival time of this train to the next station.
                    if next_event_tr_id not in blsec_t.blsec_queue: 
                        t_index = t_ind 
                        # add a train in a queue
                        blsec_t.queue_add(next_event_tr_id, next_event_train,tr_next_event.tr_type,t_index, t_dep_updt, blsec_occ_end)
                        print("After queue_add:", blsec_t.name, '  ', blsec_t.blsec_queue)
                        # update the queue based on train type 
                        update_blsec_queue_priority(blsec_t, tr_next_event.tr_type, next_event_tr_id) # call this when this fucntion is called outside of th blocksection class

                        # if queue exists; there is delay in the departure so update all the queue events.
                        i=0  
                        while i < len(blsec_t.blsec_queue):
                            stn_line= get_train_stnline_for_departure_delay(stns_event, blsec_t.blsec_queue[i+1])
                            if stn_line is not None:
                                stns_event[0].set_occupancy_updt(stn_line, blsec_t.blsec_queue[i+4])
                            sched_updt(blsec_t.blsec_queue[i+4], blsec_t.blsec_queue[i+3], blsec_t.blsec_queue[i])
                            i+=6
                        print('\n after update_blsec_queue_priority:',blsec_t.name,'  ', blsec_t.blsec_queue)
                        print('\n given blsec_t occ_end is ', blsec_t.occ_end)
                    else: # if curent train is available in a queue 
                        print('time diff is', t_dep_updt -t ) 
                        blsec_t.queue_updt(t_dep_updt - t)
                        q_len = len(blsec_t.blsec_queue)
                        q_tr_id = []
                        v = 0
                        while v < q_len:
                            if blsec_t.blsec_queue[v] in sched_act:
                                # q_tr_id.append(blsec_t.blsec_queue[v])
                                q_tr_id.append([blsec_t.blsec_queue[v], blsec_t.blsec_queue[v+3]]) 

                            v+=6  # as each entry in the queue has 6 elements
                        print('\n list of train schedules from queue to be updated: ', q_tr_id) 
                        for k in q_tr_id:
                            train_name= k[0][:k[0].index("_")]  
                            tr_index = k[1] 
                            print('index number is ', tr_index)
                            print('next evetn train id is ', next_event_tr_id)
                            print('current train id is ', k[0])
                            stn_line= get_train_stnline_for_departure_delay(stns_event, train_name)
                            print('train no is ', train_name, 'and its station line is ', stn_line)
                            print('train id is ', k[0])
                            train_id = k[0]
                            print('train schedule before updation is ', sched_act[train_id])

                            if stn_line is not None:
                                updt_dep_time= stns_event[0].tracks[stn_line][3] + (t_dep_updt -t)
                                print('updt dept time for a given train is ', updt_dep_time)
                                stns_event[0].set_occupancy_updt(stn_line, updt_dep_time)
                                sched_updt(updt_dep_time, tr_index, k[0])
                            else:
                                print('train', train_name, 'not at any station track, skipping station occupancy update')

                    print('t_dep_updt is', sched_act[next_event_tr_id][t_ind])

                    print('\n station line occupied by the given train is ', stns_event[0].tracks.get(stn_line_occ_name, 'N/A (train has no station track)'))
                    #print('\n updated schedule: ', sched_act) 
                    t_max = term_crit_calc()
                    print('\n updated time at which simulation terminates: ', t_max)
                    print('\n block section ', blsec_t.name, 'queue status: ', blsec_t.blsec_queue)


    # ----------------------------------------------execute simulation-------------------------------------------
    exec_sim = 0
    t_max = term_crit_calc()

    # just to initialize the simulation clock
    t = pd.Timestamp("2020-01-05 22:50:00") # simulation clock

    print('\n time at which simulation terminates: ', t_max)



    import time

    start_time = time.time()   #  add this BEFORE loop

    while t <= t_max and exec_sim == 0:

       #  HARD STOP CONDITION (add THIS at the top)
        # if time.time() - start_time > 600:   # 600 sec limit (adjust)
        #     print("Simulation force-stopped (timeout)")
        #     break
        event_list = build_event_list()
        next_event_time = min([i for i in event_list if isinstance(i, str) == False and i < pd.Timestamp("2100-06-01 22:50:00")]) # 100000 #time of next event
        next_event_type = event_list[event_list.index(next_event_time)+1] #arrival or departure - next event
        next_event_train = event_list[event_list.index(next_event_time)-1] #name / id of train associated with next event
        next_event_tr_id = event_list[event_list.index(next_event_time)+2] #train id in the schedule

        t = next_event_time # advance simulation clock to time of next event
        print('\n -------------------t = ', t, '-------------------------')
        print('\n event list at t = ', t, ' ', event_list)

        print('\n next event type is ', next_event_type)

        next_event_tr_id = event_list[(event_list.index(next_event_time)) + 2] # e.g., '12345_mid1' get that unique train id from event list
        # Extract instance index from train ID string 
        instance_index = int((next_event_tr_id.split('_')) [1]) # if it is '12345_mid1' then instance_index = 2

        for i in trains:
            if i.train_id == next_event_train and i.instance_index == instance_index:
                tr_next_event = i # train object for which next event is at t
                break 




        stns_event = get_station_event(t, next_event_tr_id, next_event_type, stations_list)

        if next_event_type == 'd':
            if len(stns_event) > 1:
                blsec_t = blsec_id(stns_event[0].name, stns_event[1].name)
            else:
                blsec_t = None 
        else: # if an arrival event
            if len(stns_event) > 1:
                blsec_t = blsec_id(stns_event[1].name, stns_event[0].name)
            else:
                blsec_t = None

        if blsec_t is not None:
            print('\n current block section is ', blsec_t.name)
            base = '_'.join(blsec_t.name.split('_')[:-1])   # 'mid1' removed -> base = 'jmpt_knrt'
            for suffix in ('up1', 'dn1'):
                sib_name = f'{base}_{suffix}'               # 'jmpt_knrt_up1', 'jmpt_knrt_dn1'
                sib = blsec_lookup.get(sib_name)
                if sib is not None:
                    print(sib.name, '| occ_train:', sib.occ_train, '| occ_end:', sib.occ_end)



        resource_update_event(next_event_type, next_event_tr_id, t)
        t_max = term_crit_calc()


    print('whole train schedule is ',next_event_tr_id, tr_next_event.tr_sched_act)
    print('whole sched is really ', sched_act[next_event_tr_id])
    print('\n ----------------simulation has ended-------------------------')
    for idx, j in enumerate(trains, start=1):
        print(f"Train serial number: {idx}")
        print('\n planned schedule for train', j.train_id, 'is: \n', j.tr_schedule)
        print('\n schedule operated for train', j.train_id, 'is: \n', j.tr_sched_act)
        print('\n train performance statistics: \n', j.calc_tr_stats())
        print('\n ---------------------next train--------------------------')  





    # ---- Prepare data for DataFrame ----
    rows = []
    max_len = 0
    for train_id, data in total_schedule.items():
        for sched_type, sched_data in data.items():
            formatted = [", ".join(map(str, item)) for item in sched_data]
            train_type = formatted[0]
            row = [train_id, sched_type, train_type] + formatted[1:]
            rows.append(row)
            max_len = max(max_len, len(row))

    # pad rows to equal length
    for r in rows:
        r += [''] * (max_len - len(r))

    # ---- Build column names dynamically ----
    columns = ['Train_ID', 'Schedule_Type', 'Train_Type']
    n_extra = max_len - 3  # -3 instead of -4 since no Stats column anymore
    pattern = ['Stn', 'Arr', 'Dept']
    for i in range(n_extra):
        name = pattern[i % 3] + str(i // 3 + 1)
        columns.append(name)

    # ---- Create DataFrame ----
    df = pd.DataFrame(rows, columns=columns)

    # ---- Add Abs Deviation, [Min, Max] dev, and Within Max rows ----
    max_allowed_deviation = pd.Timedelta(minutes=5)
    extra_rows = []

    time_cols = [c for c in columns if c.startswith('Arr') or c.startswith('Dept')]

    def build_deviation_rows(train_id, row_a, row_b, label):
        """Compare row_a vs row_b across time_cols, return [abs_dev_row, minmax_row]."""
        abs_dev_row = [train_id, f'Abs Deviation: {label}', '']
        abs_devs = []

        for col in columns[3:]:
            if col in time_cols:
                a_val = row_a.iloc[0][col]
                b_val = row_b.iloc[0][col]

                if pd.isna(a_val) or pd.isna(b_val) or a_val == '' or b_val == '':
                    abs_dev_row.append('')
                    continue

                try:
                    a_ts = pd.Timestamp(a_val)
                    b_ts = pd.Timestamp(b_val)
                    dev = abs((b_ts - a_ts).total_seconds() / 60)
                    abs_dev_row.append(f"{dev:.1f} min")
                    abs_devs.append(dev)
                except Exception:
                    abs_dev_row.append('')
            else:
                abs_dev_row.append('')  # blank out station name columns

        if abs_devs:
            min_dev = min(abs_devs)
            max_dev = max(abs_devs)
            minmax_label = f"[{min_dev:.1f}, {max_dev:.1f}] min"
        else:
            minmax_label = ''

        minmax_row = [train_id, f'[Abs Min dev, Abs Max dev]: {label}', minmax_label] + [''] * (len(columns) - 3)

        return [abs_dev_row, minmax_row]

    for train_id in df['Train_ID'].unique():
        train_rows = df[df['Train_ID'] == train_id]

        planned_row   = train_rows[train_rows['Schedule_Type'] == 'planned']
        simulated_row = train_rows[train_rows['Schedule_Type'] == 'simulated']
        actual_row    = train_rows[train_rows['Schedule_Type'] == 'actual']

        if planned_row.empty or simulated_row.empty:
            continue

        if not actual_row.empty:
            extra_rows.extend(build_deviation_rows(train_id, simulated_row, actual_row, 'sim vs actual'))

        extra_rows.extend(build_deviation_rows(train_id, planned_row, simulated_row, 'sim vs planned'))
    # ---- Merge extra rows into df ----
    df_extra = pd.DataFrame(extra_rows, columns=columns)

    df_final_parts = []
    for train_id in df['Train_ID'].unique():
        df_final_parts.append(df[df['Train_ID'] == train_id])
        df_final_parts.append(df_extra[df_extra['Train_ID'] == train_id])

    df = pd.concat(df_final_parts, ignore_index=True)

    # now will sort the rows based on Arr1 column taking taking two rows together (planned and actual)
    df['Arr1_sort'] = pd.to_datetime(df['Arr1'], errors='coerce')
    df_sorted = df.sort_values(by=['Train_ID', 'Arr1_sort']).drop(columns=['Arr1_sort'])

    df['Arr1_sort'] = pd.to_datetime(df['Arr1'], errors='coerce')
    # Sort by earliest Arr1, keeping planned/actual rows grouped by Train_ID
    df_sorted = pd.concat([df[df['Train_ID'] == tid] for tid in
                          df.groupby('Train_ID')['Arr1_sort'].first().sort_values().index])
    df_sorted = df_sorted.drop(columns=['Arr1_sort']).reset_index(drop=True)


    # ==== Sheet2 (self-contained -- does not modify df_sorted / Sheet1) ====
    # block_section_distances already set above from geography.block_section_distances()

    def avg_sd_str(series):
        s = series.dropna()
        if s.empty:
            return ''
        return f"{s.mean():.1f} ({s.std():.1f})"

    def remove_outliers_iqr(series):
        """Drop values outside [Q1 - 1.5*IQR, Q3 + 1.5*IQR]."""
        s = series.dropna()
        if s.empty:
            return s
        q1, q3 = s.quantile(0.25), s.quantile(0.75)
        iqr = q3 - q1
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        return s[(s >= lower) & (s <= upper)]

    def avg_sd_str_no_outliers(series):
        s = remove_outliers_iqr(series)
        if s.empty:
            return ''
        return f"{s.mean():.1f} ({s.std():.1f})"

    def get_max_dev(row_a, row_b, time_cols):
        """Max absolute deviation (minutes) across stations between two schedule rows for one train."""
        devs = []
        for col in time_cols:
            a_val = row_a.iloc[0][col]
            b_val = row_b.iloc[0][col]
            if pd.isna(a_val) or pd.isna(b_val) or a_val == '' or b_val == '':
                continue
            try:
                a_ts = pd.Timestamp(a_val)
                b_ts = pd.Timestamp(b_val)
                devs.append(abs((b_ts - a_ts).total_seconds() / 60))
            except Exception:
                continue
        return max(devs) if devs else None

    # ---- completion times (computed here only, not written to Sheet1) ----
    planned_completion = max(tr.tr_schedule[tr.tr_destination][0] for tr in trains)
    simulated_completion = max(tr.tr_sched_act[tr.tr_destination][0] for tr in trains)

    actual_completion_candidates = [
        tr.tr_real_schedule[tr.tr_destination][0]
        for tr in trains
        if tr.tr_destination in tr.tr_real_schedule
        and tr.tr_real_schedule[tr.tr_destination][0] is not None
    ]
    actual_completion = max(actual_completion_candidates) if actual_completion_candidates else None

    # ---- deviation summary (passenger + goods) ----
    dev_summary = []
    for train_id in df['Train_ID'].unique():
        train_rows = df[df['Train_ID'] == train_id]
        planned_row   = train_rows[train_rows['Schedule_Type'] == 'planned']
        simulated_row = train_rows[train_rows['Schedule_Type'] == 'simulated']
        actual_row    = train_rows[train_rows['Schedule_Type'] == 'actual']

        if planned_row.empty or simulated_row.empty:
            continue

        train_type = planned_row.iloc[0]['Train_Type']

        max_dev_sim_vs_planned = get_max_dev(planned_row, simulated_row, time_cols)
        max_dev_actual_vs_planned = get_max_dev(planned_row, actual_row, time_cols) if not actual_row.empty else None

        dev_summary.append({
            'train_id': train_id,
            'train_type': train_type,
            'max_dev_actual_vs_planned': max_dev_actual_vs_planned,
            'max_dev_sim_vs_planned': max_dev_sim_vs_planned
        })

    dev_summary_df = pd.DataFrame(
        dev_summary,
        columns=['train_id', 'train_type', 'max_dev_actual_vs_planned', 'max_dev_sim_vs_planned']
    )

    # actual vs planned: report both with-outliers and outliers-removed stats
    p_actual_str             = avg_sd_str(dev_summary_df.loc[dev_summary_df.train_type == 'p', 'max_dev_actual_vs_planned'])
    p_actual_str_no_outliers = avg_sd_str_no_outliers(dev_summary_df.loc[dev_summary_df.train_type == 'p', 'max_dev_actual_vs_planned'])
    g_actual_str             = avg_sd_str(dev_summary_df.loc[dev_summary_df.train_type == 'g', 'max_dev_actual_vs_planned'])
    g_actual_str_no_outliers = avg_sd_str_no_outliers(dev_summary_df.loc[dev_summary_df.train_type == 'g', 'max_dev_actual_vs_planned'])

    # simulated vs planned: outliers are never removed
    p_sim_str    = avg_sd_str(dev_summary_df.loc[dev_summary_df.train_type == 'p', 'max_dev_sim_vs_planned'])
    g_sim_str    = avg_sd_str(dev_summary_df.loc[dev_summary_df.train_type == 'g', 'max_dev_sim_vs_planned'])

    # ---- speed summary ----
    stn_cols  = [c for c in columns if c.startswith('Stn')]
    arr_cols  = [c for c in columns if c.startswith('Arr')]
    dept_cols = [c for c in columns if c.startswith('Dept')]

    def get_distance(stn_a, stn_b):
        if (stn_a, stn_b) in block_section_distances:
            return block_section_distances[(stn_a, stn_b)]
        if (stn_b, stn_a) in block_section_distances:
            return block_section_distances[(stn_b, stn_a)]
        return None

    def clean_stn(val):
        if val is None or (isinstance(val, float) and pd.isna(val)) or val == '':
            return None
        return str(val).split(',')[0].strip()

    def compute_train_avg_speed(row):
        total_dist = 0.0
        total_hours = 0.0
        n = len(stn_cols)
        for i in range(n - 1):
            stn_a = clean_stn(row.iloc[0][stn_cols[i]])
            stn_b = clean_stn(row.iloc[0][stn_cols[i + 1]])
            dept_a, arr_b = row.iloc[0][dept_cols[i]], row.iloc[0][arr_cols[i + 1]]
            if not stn_a or not stn_b or pd.isna(dept_a) or pd.isna(arr_b) or dept_a == '' or arr_b == '':
                continue
            dist = get_distance(stn_a, stn_b)
            if dist is None:
                continue
            try:
                hours = (pd.Timestamp(arr_b) - pd.Timestamp(dept_a)).total_seconds() / 3600
            except Exception:
                continue
            if hours <= 0:
                continue
            total_dist += dist
            total_hours += hours
        if total_hours == 0:
            return None
        return total_dist / total_hours

    speed_summary = []
    for train_id in df['Train_ID'].unique():
        train_rows = df[df['Train_ID'] == train_id]
        planned_row   = train_rows[train_rows['Schedule_Type'] == 'planned']
        simulated_row = train_rows[train_rows['Schedule_Type'] == 'simulated']
        actual_row    = train_rows[train_rows['Schedule_Type'] == 'actual']
        if planned_row.empty:
            continue
        train_type = planned_row.iloc[0]['Train_Type']
        if train_type != 'g':
            continue
        speed_summary.append({
            'train_id': train_id,
            'speed_planned': compute_train_avg_speed(planned_row),
            'speed_actual': compute_train_avg_speed(actual_row) if not actual_row.empty else None,
            'speed_simulated': compute_train_avg_speed(simulated_row) if not simulated_row.empty else None,
        })

    speed_summary_df = pd.DataFrame(
        speed_summary,
        columns=['train_id', 'speed_planned', 'speed_actual', 'speed_simulated']
    )

    g_speed_planned_str   = avg_sd_str(speed_summary_df['speed_planned'])
    g_speed_actual_str    = avg_sd_str(speed_summary_df['speed_actual'])
    g_speed_simulated_str = avg_sd_str(speed_summary_df['speed_simulated'])

    # ---- assemble Sheet2 (all metric rows always present) ----
    summary_rows = [
        ['Metric', 'planned', 'actual', 'simulated'],
        ['overall schedule completion time',
         str(planned_completion),
         str(actual_completion) if actual_completion is not None else '',
         str(simulated_completion)],
        ['passenger trains: avg absolute deviation from overall schedule (SD, minutes)', '--', p_actual_str, p_sim_str],
        ['goods trains: avg absolute deviation from overall schedule (SD, minutes)', '--', g_actual_str, g_sim_str],
        ['average speed of goods trains for the schedule (SD, km/hr)', g_speed_planned_str, g_speed_actual_str, g_speed_simulated_str],
        ['', '', '', ''],
        ['', '', '', ''],
        ['after outliers removal from actual scheduled data', '', '', ''],
        ['passenger trains: avg absolute deviation from overall schedule (SD, minutes)', '--', p_actual_str_no_outliers, p_sim_str],
        ['goods trains: avg absolute deviation from overall schedule (SD, minutes)', '--', g_actual_str_no_outliers, g_sim_str],
    ]
    summary_df = pd.DataFrame(summary_rows[1:], columns=summary_rows[0])


    # ==== Sheet3: per-train deviation values in the labeled block format ====
    # planned vs simulated has NO outlier split (outliers are never removed for sim),
    # so it appears once; planned vs actual spans both with/without-outliers blocks.

    def dev_list(df_, type_, col):
        return df_.loc[df_.train_type == type_, col].dropna().tolist()

    # planned vs simulated (single version -- unfiltered)
    p_sim  = dev_list(dev_summary_df, 'p', 'max_dev_sim_vs_planned')
    g_sim  = dev_list(dev_summary_df, 'g', 'max_dev_sim_vs_planned')

    # planned vs actual -- with outliers
    p_act_w = dev_list(dev_summary_df, 'p', 'max_dev_actual_vs_planned')
    g_act_w = dev_list(dev_summary_df, 'g', 'max_dev_actual_vs_planned')

    # planned vs actual -- without outliers (IQR-filtered)
    p_act_no = remove_outliers_iqr(dev_summary_df.loc[dev_summary_df.train_type == 'p', 'max_dev_actual_vs_planned']).tolist()
    g_act_no = remove_outliers_iqr(dev_summary_df.loc[dev_summary_df.train_type == 'g', 'max_dev_actual_vs_planned']).tolist()

    series = [p_sim, g_sim, p_act_w, g_act_w, p_act_no, g_act_no]
    max_n  = max((len(s) for s in series), default=0)

    def r2(v):
        return round(float(v), 2) if v is not None else None

    # leading label column (A) + 6 data columns (B-G)
    title_row  = ['', 'Deviations from the planned schedule', '', '', '', '', '']
    row_cmp    = ['', 'planned vs simulated', 'planned vs simulated', 'Planned vs actual', 'Planned vs actual', 'Planned vs actual', 'Planned vs actual']
    row_out    = ['', '', '', 'with outliers', 'with outliers', 'without outliers', 'without outliers']
    row_type   = ['', 'Passenger', 'Goods', 'Passenger', 'Goods', 'Passenger', 'Goods']
    range_row  = ['range='] + [f"[{min(s):.2f}, {max(s):.2f}]" if s else '' for s in series]
    value_rows = [[''] + [(r2(series[c][r]) if r < len(series[c]) else None) for c in range(6)] for r in range(max_n)]

    sheet3_grid = [title_row, row_cmp, row_out, row_type, range_row] + value_rows


    # excel file output (all three sheets)
    from openpyxl.styles import Alignment, Font

    with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
        df_sorted.to_excel(writer, sheet_name='Sheet1', index=False)
        summary_df.to_excel(writer, sheet_name='Sheet2', index=False)

        # Sheet3 written manually so the label header can be merged
        ws3 = writer.book.create_sheet('Sheet3')
        for row in sheet3_grid:
            ws3.append(['' if v is None else v for v in row])

        for rng in ('B1:G1', 'B2:C2', 'D2:G2', 'B3:C3', 'D3:E3', 'F3:G3'):
            ws3.merge_cells(rng)
        for r in (1, 2, 3, 4, 5):                       # header + range row bold/centered
            for c in range(1, 8):
                cell = ws3.cell(row=r, column=c)
                cell.alignment = Alignment(horizontal='center', vertical='center')
                cell.font = Font(bold=True)

        # 2-decimal display on the value cells (rows 6 onward, cols B-G)
        for r in range(6, 5 + max_n + 1):
            for c in range(2, 8):
                cell = ws3.cell(row=r, column=c)
                if isinstance(cell.value, (int, float)):
                    cell.number_format = '0.00'

    print(f"Saved -> {excel_filename} (Sheet1 + Sheet2 + Sheet3)")




    # to get the time distance chart output 
    #  Get simulated rows only 
    sim_rows = []

    for train_id, data in total_schedule.items():
        sched_data = data['simulated']
        formatted  = [", ".join(map(str, item)) for item in sched_data]
        train_type = formatted[0]
        row        = [train_id, train_type] + formatted[1:]
        sim_rows.append(row)

    # pad rows to equal length
    max_len = max(len(r) for r in sim_rows)
    for r in sim_rows:
        r += [''] * (max_len - len(r))

    #  Build column names 
    columns_sim = ['Train_ID', 'Train_Type']
    n_extra     = max_len - 2
    pattern     = ['Stn', 'Arr', 'Dept'] 
    for i in range(n_extra):
        columns_sim.append(pattern[i % 3] + str(i // 3 + 1))

    # Create DataFrame  for time distance chart
    df_simulated = pd.DataFrame(sim_rows, columns=columns_sim)
    stn_cols = [c for c in df_simulated.columns if c.startswith('Stn')]
    for col in stn_cols:
        df_simulated[col] = df_simulated[col].apply(
            lambda x: x.split(',')[0].strip() if isinstance(x, str) and x != '' else x
        )
    print(f'Total trains: {len(df_simulated)}')



    # filter_df_by_date_window / get_formatted_data_from_df / plot_railway_chart
    # already imported at module level above

    def master_time_distance_chart(df, station_order, segments, start_dt, end_dt, filename):
        df_day = filter_df_by_date_window(df, start_dt)
        if len(df_day) == 0:
            print('Stopping -- no data for provided date')
        else:
            train_data, chart_date = get_formatted_data_from_df(df_day, start_dt=start_dt, end_dt=end_dt)
            plot_railway_chart(station_order, segments, train_data, chart_date, filename)

    master_time_distance_chart(
        df_simulated,
        station_order,
        segments,
        start_dt = start_dt,
        end_dt   = start_dt + pd.Timedelta(hours=chart_duration_hrs),
        filename = chart_filename
    )



    # create an json file 

    import json

    def total_schedule_to_json(total_schedule, output_filename='schedule_simulated.json'):

        trains_list = []

        for train_id, data in total_schedule.items():

            sched_data = data['simulated']
            train_type = sched_data[0][0]

            # first parse all stops into a list
            stops = []
            i = 1
            while i + 2 <= len(sched_data) - 1:
                stn_info   = sched_data[i]
                station    = stn_info[0]
                line       = stn_info[1] if len(stn_info) > 1 else 's1'
                platform   = stn_info[2] if len(stn_info) > 2 else 1
                next_block = stn_info[3] if len(stn_info) > 3 else None
                arr_str    = sched_data[i + 1][0].strftime('%Y-%m-%d %H:%M:%S')
                dep_str    = sched_data[i + 2][0].strftime('%Y-%m-%d %H:%M:%S')

                stops.append({
                    'station'   : station,
                    'line'      : line,
                    'platform'  : platform,
                    'arr'       : arr_str,
                    'dep'       : dep_str,
                    'next_block': next_block  # this is the INCOMING block at this station
                })
                i += 3

            # now build route -- shift next_block by one position
            # stop[i]'s incoming block = stop[i-1]'s outgoing block
            route = []
            for idx, stop in enumerate(stops):
                stop_entry = {
                    'station' : stop['station'],
                    'line'    : stop['line'],
                    'platform': stop['platform'],
                    'arr'     : stop['arr'],
                    'dep'     : stop['dep'],
                }

                # outgoing block for this stop = incoming block of NEXT stop
                if idx + 1 < len(stops):
                    outgoing_block = stops[idx + 1]['next_block']
                    if outgoing_block is not None:
                        stop_entry['next_block'] = outgoing_block
                # last station -- no next_block added

                route.append(stop_entry)

            trains_list.append({
                'train_id'  : train_id,
                'train_type': train_type,
                'route'     : route
            })

        all_times = []
        for t in trains_list:
            for r in t['route']:
                all_times.append(r['arr'])
                all_times.append(r['dep'])

        output = {
            'simulation': {
                'start_time': min(all_times),
                'end_time'  : max(all_times)
            },
            'trains': trains_list
        }

        with open(output_filename, 'w') as f:
            json.dump(output, f, indent=2)

        print(f'Saved {len(trains_list)} trains to {output_filename}')
    total_schedule_to_json(total_schedule, animator)


    return {
        "excel_filename": excel_filename,
        "chart_filename": chart_filename,
        "animator_filename": animator,
        "total_schedule": total_schedule,
        "trains": trains,
    }
