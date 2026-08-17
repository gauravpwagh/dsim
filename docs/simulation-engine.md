# Simulation engine — `final_sim_sj_4aug.py`

This ~2,900-line script (mirrored in `final_sim_sj_4aug.ipynb` for interactive runs) is
the heart of the project: a discrete-event simulation that replays a planned timetable
through the physical network model, resolves real-world conflicts, and writes out the
result. It is written as a single top-to-bottom script (not a library of importable
functions) — configuration, simulation, and output/reporting all happen as module-level
code that runs on import/execution.

## Configuration (top of file)

- `network_section` — which corridor to simulate: `'psa_ktv'`, `'sprd_vzm'`, or
  `'krdl_ktv'` — selects the station order/segment distances (from
  `wat_block_section_distances.py`) used for the output chart, via a `section_map` dict.
- The active train list is a **hardcoded import**, e.g.
  `from input_train_data_updated_after_goods_gen.p_g_sprd_vzm_2days import trains` — to run
  a different corridor/dataset you edit this import line (see
  [input-generation.md](input-generation.md)).
- `start_dt_mode`: `'planned'` (start = earliest planned time across all trains, plus
  `start_dt_buffer_minutes`) or `'manual'` (a fixed `start_dt_manual` timestamp).
- `chart_duration_hrs` — time window shown in the output time-distance chart.
- `chart_filename` / `excel_filename` / `animator` — output paths.
- `headway_distance = 3.6` km — minimum safe following distance used for **autoblock**
  sections.
- `GOODS_MAX_PRIORITY_WAIT = 20h` — a goods train that has been waiting this long past its
  originally-planned departure is force-dispatched on its next opportunity regardless of
  passenger occupancy, so continuous passenger traffic can never starve it forever (see
  "Priority rules" below).
- `autoblock_stations = ['alm', 'kuk', 'vzm']` — stations between which the block
  section(s) are treated as **autoblock** (signal-block, not full physical block)
  territory — see below.
- `USE_HALT_DEVIATION` / `USE_SPEED_RANDOMNESS` — toggle the two randomness models off for
  a deterministic run equal to the planned schedule.

## Core state

- `sched` / `sched_act` — every train instance's schedule flattened into a single list per
  train: `[station, arrival_ts, departure_ts, station, arrival_ts, departure_ts, ...]`.
  `sched_act` is the live, mutated-during-simulation version; `sched` and `given_sched`
  (a frozen copy) are kept for comparison/priority calculations.
- `total_schedule` — dict keyed by train instance id, holding three parallel timetables:
  `'planned'`, `'simulated'`, `'actual'` (from `tr_real_schedule`, if any) — this is what
  gets exported to Excel/JSON at the end.
- `blsec_lookup` — `{block_section_name: block_sec object}`, built once from
  `network.blocksections_list`.

## The event loop

```python
while t <= t_max and exec_sim == 0:
    event_list = build_event_list()          # next pending arrival/departure per train
    ... pick the earliest event (t, type, train) ...
    stns_event = get_station_event(...)       # station(s) involved
    blsec_t = blsec_id(...)                   # which block section this event concerns
    resource_update_event(next_event_type, next_event_tr_id, t)   # <- does the real work
    t_max = term_crit_calc()                  # recompute simulation end time
```

- `build_event_list()` scans every train's `sched_act` for its next not-yet-processed
  timestamp (anything before the `2100-06-01` "done" sentinel) and returns the globally
  earliest one, tagged `'a'` (arrival) or `'d'` (departure).
- `term_crit_calc()` recomputes the simulation's end time each iteration (the latest
  remaining un-processed event across all trains) — the loop naturally terminates once
  every train has reached its destination.
- `resource_update_event(...)` (the largest function, ~450 lines) is where a single
  arrival or departure event is actually resolved: it assigns a station line/platform,
  checks the target block section's occupancy/queue, applies priority and randomness
  rules, updates occupancy state, and pushes the (possibly delayed) new time back into
  `sched_act`.

## Block-section assignment — `blsec_id(stn1, stn2)`

Given a travel direction between two stations, this finds the concrete `block_sec` object
a train should use. It's non-trivial because a station pair can have multiple physical
lines (`dn1`/`up1`/`mid1`/`mid2`):

1. Filters `blocksections_list` to sections between the two stations, in the correct
   direction (or bidirectional `mid*`).
2. For an **arrival** event, prefers the section the train is already recorded as
   occupying.
3. Restricts candidates to those actually wired (via `stn_obj.connections`) to the station
   line the train currently occupies.
4. For a **departure**, if the train is already queued on one of the candidate sections,
   reuses that section if it's now free, or looks for a free "sibling" section (same
   station pair, different direction-suffix) via `find_free_sibling_blsec(...)` — this
   lets a train queued on a busy `mid1` line get redirected onto a free `dn1`/`up1` if one
   opens up, provided the sibling actually runs the same physical direction and is wired
   to the train's current station line.
5. If multiple free candidates remain, prefers a genuinely unidirectional (`up`/`dn`) line
   over a shared `mid` one; if none are free, picks whichever becomes free earliest
   (`get_queue_end_time`).

## Station line / platform assignment — `stn_line_assign(...)`

Chooses which station line (platform or loop) a train uses at a given stop, by walking
that station's free tracks and checking whether each candidate line actually connects to
both the incoming and outgoing block sections. Passenger trains that are genuinely halting
(arrival ≠ departure) are required to land on a platformed line (`tracks[j][1] != 0`) on a
first pass; a second, relaxed pass allows a platformless line only if every platformed
line is occupied, so a halting passenger train isn't stuck forever while a platformless
line sits idle. Goods trains, and passenger trains merely passing through, aren't subject
to the platform requirement.

## Priority rules

- **Passenger over goods, within a block-section queue** —
  `update_blsec_queue_priority(...)` re-sorts a section's wait queue so all passenger
  entries precede all goods entries whenever a passenger train joins a queue that already
  has goods trains waiting, shifting the goods trains' start/end times later accordingly
  and propagating the change into their schedules and station-line occupancy records.
- **A goods train yields to passenger traffic at a station** —
  `goods_delay_due_to_passenger(...)` delays a goods train's departure until the later of
  (a) the latest occupancy-end time among trains currently at the station, and (b) the
  arrival time of the last passenger train that used the block section the goods train is
  about to enter. `check_if_all_goods(...)` short-circuits this when every other train
  present is itself a goods train (nothing to yield to).
- **Starvation guard** — because continuous passenger traffic could otherwise re-trigger
  that yield check forever, once a goods train has been waiting `GOODS_MAX_PRIORITY_WAIT`
  (20h) past its originally planned (pre-delay) departure, it is dispatched unconditionally
  on its next opportunity.

## Randomness models

Both are optional (gated by `USE_HALT_DEVIATION` / `USE_SPEED_RANDOMNESS`) and driven by
fixed random seeds (`HALT_DEVIATION_SEED`, `SPEED_RANDOMNESS_SEED` = 1234) for
reproducible runs.

- **Halt-time deviation** (`add_halt_randomness` → `_generate_halt_deviation` →
  `_sample_halt_dev`) — draws a deviation (in minutes) from a per-station, per-train-type
  statistical distribution fitted from real movement data (see
  [data-files.md](data-files.md), `halt_deviation_fits.py`), clamped to the real observed
  maximum for that station so simulated deviations never exceed history.
- **Block-section crossing-time randomness** (`add_speed_randomness` →
  `_sample_blsec_time`) — samples a crossing time (weighted by observed frequency) from
  `blocksection_actual_times.py`'s per-direction, per-section distribution instead of using
  the scheduled speed; `new_arr_by_speed_randomness(...)` recomputes the resulting arrival
  time and, if it shifts by more than a minute, propagates the delay to every other train
  still queued behind it on the same block section (their own schedules and station-line
  occupancy end-times are shifted by the same increment).

## Autoblock sections

Stations listed in `autoblock_stations` (e.g. `alm`, `kuk`, `vzm`) represent territory
signalled by automatic block (multiple trains may be strung out along the same physical
line at once, spaced by a minimum time/distance headway) rather than one-train-per-section
physical blocking. These sections skip the normal `occ_ind`/queue machinery and instead
use `autoblsec_list`: each entry records a train's speed and timing, and a following train
is only allowed to depart once it can maintain at least `headway_distance` (3.6 km) of
separation from the previous train, computed from both trains' speeds.

## Ending and output

When the loop terminates, the script:

1. Prints per-train planned-vs-simulated statistics (`train.calc_tr_stats()`).
2. Builds a wide DataFrame (`Stn1/Arr1/Dept1, Stn2/Arr2/Dept2, ...` columns) from
   `total_schedule` and writes a 3-sheet Excel workbook (`excel_filename`):
   - **Sheet1** — full planned / simulated / actual timetables per train, plus computed
     deviation and "within max allowed deviation" rows (`max_allowed_deviation = 5 min`).
   - **Sheet2** — summary statistics (average absolute deviation, split by passenger vs.
     goods, with and without outliers removed via IQR filtering).
   - **Sheet3** — per-train deviation value listings in a merged/labeled grid, split by
     planned-vs-simulated and planned-vs-actual (with/without outliers).
3. Builds the time-distance chart via `master_time_distance_chart(...)`, which windows the
   simulated schedule to `chart_duration_hrs` (`data_extract.filter_df_by_date_window` /
   `get_formatted_data_from_df`) and renders it with `chart_logic3.plot_railway_chart`,
   saving `chart_filename` as a PDF.
4. Writes `animator` — a JSON file (`total_schedule_to_json`) with each train's ordered
   route (station, line, platform, arrival, departure, outgoing block section), for
   consumption by a separate train-animation front-end (not included in this repo).

See [outputs.md](outputs.md) for more detail on the charting/extraction helpers and what
ends up in `output_files_*`.
