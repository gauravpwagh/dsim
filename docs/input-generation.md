# Input generation — from Excel timetables to simulator input

The simulator consumes a plain Python list of `train` objects
(`input_train_data_updated_after_goods_gen/p_g_*.py`). This document covers how those
files are produced.

## `excel_input_files_goods_sched_generation/` — source spreadsheets

Real passenger + goods timetable data per corridor, exported from an infrastructure
database:

- `p_g_kdrl_ktv_2days1.xlsx` — KRDL–KTV corridor.
- `p_g_ktv_psa_2days.xlsx` — KTV–PSA corridor.
- (a stray `~$krdl_ktv_p_g.xlsx` Excel lock file indicates the source workbook was open at
  some point — not itself a data file.)

Each row is one train, tagged `pgflag` = `'P'` (passenger) or `'G'` (goods), with a wide
set of `station_i` / `schdarvl_i` / `schddprt_i` / `actualarvl_i` / `actualdprt_i` columns
(one group of 5 per stop) recording that train's scheduled and actually-recorded
arrival/departure at each station.

## `2_find_goods_train_scheduling_final_7july.ipynb` — the goods-scheduling generator

Passenger timetables are treated as fixed/real; this notebook's job is to **insert goods
trains into whatever block-section capacity is left over**, since goods trains in the
source data typically only have a confirmed origin time, not a full timetable. Flow:

1. Load the corridor's Excel file; split into `df_p` (passenger) and `df_g` (goods).
2. Build `blsec_info`/`blocksection_times` from `network.blocksections_list` — the same
   merged network topology the main simulator uses — plus fixed crossing times from
   `blocksection_times.py`.
3. `goods_train(df_input)` walks every already-scheduled train (starting with just
   passengers) and records, **per physical line** (e.g. `'KRDL-BCHL-dn1'`, resolved via
   `lines_for_travel(curr_stn, next_stn)` + first-fit), which time intervals are occupied.
   `available_times()` then computes the complementary free-slot list for every line.
4. Passenger and goods rows are combined into `df_combined`; each goods train's schedule
   columns are cleared except its origin arrival (seeded from its real arrival time if
   available, else its scheduled one).
5. `event_list_creation(df_combined)` builds one pending-event entry per goods train, for
   its first unscheduled block section: `[trainno, row_idx, col_index, ready_time,
   curr_stn, next_stn]`.
6. `scheduling_goods_time(event_list1)` is the greedy scheduler run in a loop: repeatedly
   picks the goods train that's ready earliest, looks up the free slots on all physical
   lines serving its next block section, and places it in the first slot big enough for the
   fixed crossing time (`MIN_DWELL = 0` — no artificial extra wait beyond becoming ready
   and finding a slot). If no slot is ever found, that train is dropped with a warning
   rather than blocking the run. Each successful placement writes departure/arrival times
   back into `df_combined` and advances that train to its next block section
   (`event_list_update`); occupied/available times are recomputed after each placement so
   later trains see up-to-date capacity.
7. Once every goods train has reached its destination (or been dropped for lacking a
   slot), rows with data-quality issues (stations with a name but no arrival/departure)
   are filtered out, and `build_train_object(row, index, cons_number)` converts each
   surviving row into a `train(...)` object literal string (matching `trains.py`'s
   constructor exactly), writing all of them plus a final `trains = [tr0, tr1, ...]` list
   to a target `.py` file — this is exactly the format
   `input_train_data_updated_after_goods_gen/*.py` files are in.

The directory name `updated_after_goods_gen` reflects this: those files are the
**post-processing output** of this notebook — passenger schedules with goods trains
synthetically slotted in around them.

## `input_train_data_updated_after_goods_gen/` — generated per-corridor train lists

Each file has the same shape: `from trains import train`, `from pandas import Timestamp`,
a long flat sequence of `trN = train(id, type, sched_dict, origin, dest, max_speed,
instance_index, real_sched_dict)` statements, then a `trains = [tr0, tr1, ...]` list
(sometimes followed by a slice/filter, e.g. `trains = trains[0:200]` or an ID-exclusion
list — leftover manual truncation from test/debug runs).

| File | Corridor | Notes |
|---|---|---|
| `p_g_krdl_ktv_2day.py` | KRDL–KTV | Older/smaller dataset; has two competing `trains = [...]` assignments (second wins) — apparent leftover from iterative editing. |
| `p_g_krdl_ktv_2days.py` | KRDL–KTV | The canonical 2-day dataset (matches output filenames). |
| `p_g_ktv_psa_1day.py` | KTV–PSA (via VZM) | 1-day window, passenger trains only in the rows sampled. |
| `p_g_ktv_psa_2days.py` | KTV–PSA (via VZM) | 2-day window, sliced to `trains[0:200]`. |
| `p_g_sprd_vzm_2days.py` | SPRD–VZM (RV line) | Mixed passenger + goods (goods IDs use a `'G<n>'` naming convention), sliced to `trains[0:10]` for smaller test runs. |
| `p_g_network_2days.py` | Whole merged network | Largest file (342 trains before filtering); a couple of specific train IDs are excluded. |

`final_sim_sj_4aug.py` picks exactly one of these via a hardcoded import at the top of the
file, e.g.:

```python
from input_train_data_updated_after_goods_gen.p_g_sprd_vzm_2days import trains
```

To simulate a different corridor or dataset, change this import line (and the matching
`network_section` / output filename variables) and rerun.

## `test_cases/`

`test_cases_summary_sj_30March.xlsx` and `test_cases_summary_sj_16June.xlsx` — dated
snapshots of test scenarios, likely used to regression-test the simulator's conflict
resolution logic against known/expected outcomes as the engine evolved.
