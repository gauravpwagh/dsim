# Reference / statistical data files

> **Relocated.** These are now JSON files under `src/iidsim/data/raw/`, loaded through
> `src/iidsim/data/{geography,timing,halt_deviation}.py`. See
> [restructure-notes.md](restructure-notes.md) for the path mapping — the `.py` files
> named below no longer exist; their content and purpose are unchanged.

These files hold auto-generated reference data — geography, distances, and statistical
fits of real train-movement behavior — that the simulation engine treats as read-only
input. Their header comments identify them as generated from `WAT_Infra_Data.xlsx` and
real movement/timetable records for the WAT (Waltair) division network.

## `stations_longitude.py`

`station_longitudes` — a dict of lowercase station code → decimal longitude (float),
generated from `WAT_Infra_Data.xlsx` (Station sheet, `MANLONGITUDE` column). Used purely to
give each station object an approximate west→east geographic position, which the engine
relies on to decide block-section direction (`'dn'` = west→east, `'up'` = east→west) and
to order the time-distance chart. Note: the KRDL→VZM stretch uses a synthetic uniform step
(0.04° per station) rather than true surveyed longitude, so it approximates relative
ordering rather than exact geography for that segment.

Consumed by every `network/*_stations_data.py` board file and directly by
`final_sim_sj_4aug.py` (`train_direction`, `conn_base`, etc.).

## `wat_block_section_distances.py`

Defines the three named corridor orders and per-segment distances (km) used for chart
selection, independent of the full merged network graph:

- `krdl_ktv` / `krdl_ktv_segments` — KRDL→KTV via KRPU (OEC line).
- `sprd_vzm` / `sprd_vzm_segments` — SPRD→VZM (RV line).
- `psa_ktv` / `psa_ktv_segments` — PSA→KTV via VZM (main trunk).
- `block_section_distances` — the three segment dicts merged into one
  `(start_station, end_station) → distance_km` lookup.

`final_sim_sj_4aug.py` imports all of these and picks one triple via its
`section_map`/`network_section` config to drive the output chart's station order and
distances, and uses `block_section_distances` for average-speed calculations in the Excel
summary sheet.

## `blocksection_times.py`

Auto-generated **single-value** crossing times: `g_times = {'dn': {...}, 'up': {...}}`
(and a `p_times` counterpart), each mapping `'STN1-STN2'` → one `pandas.Timedelta` —
a proportion-weighted average where a station pair has multiple parallel block-section
objects. This is the simpler, earlier artifact; it's the one used by the **goods-schedule
generation notebook** (`2_find_goods_train_scheduling_final_7july.ipynb`) to look up a
fixed crossing time when slotting goods trains into free capacity.

## `blocksection_actual_times.py`

The richer **distributional** version, actually used by the main simulator for
weighted-random sampling: `g_times`/`p_times` = `{'up': {...}, 'dn': {...}}`, each entry
`'STN1-STN2': {'values': [minutes...], 'weights': [pct...]}` — the top 90%-by-frequency of
observed crossing times (capped at 50 minutes), for
`rng.choice(entry['values'], p=weights/weights.sum())`-style sampling.

Consumed by `final_sim_sj_4aug.py`'s `add_speed_randomness`/`_sample_blsec_time`, gated by
`USE_SPEED_RANDOMNESS`.

## `blocksection_speeds_data.py`

Auto-generated **average speed** (km/h) per block section per direction, structurally
parallel to `blocksection_times.py`: `g_speeds`/`p_speeds` = `{'dn': {'STN1-STN2': speed,
...}, 'up': {...}}`. Not directly imported by the main simulation script — likely a
derived/legacy artifact, or used elsewhere in the data-preparation tooling.

## `halt_deviation_fits.py`

By far the largest file in the repo (~225,000 lines) — a dictionary of **fitted
statistical distributions** describing how much a train's actual halt (dwell) time at a
station deviates from its scheduled halt time, fit separately for goods and passenger
trains from real WAT movement data.

Structure:

- `halt_dev_fits_g` / `halt_dev_fits_p` — dicts keyed by uppercase station code. Each
  value is either:
  - `{'type': 'mixture', 'p_zero': <probability of zero deviation>, 'dist': <scipy.stats
    distribution name, e.g. 'weibull_min' | 'gamma' | 'expon'>, 'params': (shape, loc,
    scale), 'shift': 1.0}`, or
  - `{'type': 'empirical', 'data': [...]}` for stations with too little data to fit a
    parametric distribution — sampling just draws directly from the recorded values.
- `station_max_g` / `station_max_p` — per-station real observed maximum deviation
  (minutes), used to clamp sampled values so simulated randomness never exceeds what was
  historically observed.

Consumed by `final_sim_sj_4aug.py`'s `add_halt_randomness` → `_generate_halt_deviation` →
`_sample_halt_dev`, gated by `USE_HALT_DEVIATION`. Both `HALT_DEVIATION_SEED` and a
dedicated `np.random.Generator` make the sampling reproducible across runs.

## Data-generation pipeline summary

```
WAT_Infra_Data.xlsx (Station / Block Section sheets, not in this repo)
        │
        ├── stations_longitude.py           (MANLONGITUDE column)
        └── wat_block_section_distances.py  (MANINTRDIST column)

Real WAT movement/timetable records
        │
        ├── blocksection_times.py           (single average crossing time)
        ├── blocksection_actual_times.py    (crossing-time distributions)
        ├── blocksection_speeds_data.py     (average speed)
        └── halt_deviation_fits.py          (per-station halt-deviation distribution fits)
```

All six files self-describe as "Auto-generated" in their header comments — they are build
artifacts, not hand-authored, and are regenerated from source Excel/movement data rather
than edited directly.
