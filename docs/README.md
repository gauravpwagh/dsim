# iidsim — Documentation

`iidsim` is a discrete-event **railway traffic simulator** for a real Indian Railways
section — the WAT (Waltair division) network around **VZM (Vizianagaram)**, covering the
lines KRDL↔KTV, SPRD↔VZM, and PSA↔KTV↔SCMN. It replays a day's (or two days') planned
timetable of passenger (`'p'`) and goods/freight (`'g'`) trains through a model of the
physical track (stations, platforms, single/double-line block sections, headway rules),
resolves conflicts (who waits for whom, which platform, which line), and adds realistic
randomness (dwell-time deviations, block-section crossing-time variation) fitted from real
movement data. The output is a simulated timetable compared against the planned schedule,
plus a time–distance ("train graph") PDF chart and a JSON file for a train-animation
front-end.

This documentation is split into focused files:

| File | Covers |
|---|---|
| [domain-model.md](domain-model.md) | The core classes: `train`, station, block section, and how the physical network graph is assembled (`trains.py`, `stations.py`, `blocksections.py`, `network/`, `station_routes.py`) |
| [simulation-engine.md](simulation-engine.md) | The main simulation script `final_sim_sj_4aug.py` — the event loop, conflict/priority rules, randomness models, and outputs |
| [data-files.md](data-files.md) | Auto-generated reference data: station longitudes, block-section distances/crossing-times/speeds, halt-deviation statistical fits |
| [input-generation.md](input-generation.md) | How the per-corridor train lists that the simulator consumes are produced, from Excel timetables through the goods-scheduling notebook |
| [outputs.md](outputs.md) | The charting and data-extraction helpers, and what lands in `output_files_*` |

## Big picture

```
Excel infra/timetable data
        │
        ▼
network/*_stations_data.py, *_blocksections_data.py   (physical track graph, 3 "boards")
        │                              merged by network/__init__.py
        ▼
stations_longitude.py, wat_block_section_distances.py,
blocksection_times.py / _actual_times.py / _speeds_data.py,
halt_deviation_fits.py                                (reference/statistical data)
        │
excel_input_files_goods_sched_generation/*.xlsx
        │  (2_find_goods_train_scheduling_final_7july.ipynb interleaves goods
        │   trains into free block-section slots around the passenger timetable)
        ▼
input_train_data_updated_after_goods_gen/p_g_*.py     (per-corridor `trains` lists)
        │
        ▼
final_sim_sj_4aug.py / .ipynb                          (THE SIMULATION ENGINE)
        │  discrete-event loop over arrivals/departures, using trains.py / stations.py /
        │  blocksections.py / station_routes.py as the domain model
        ▼
output_files_*/  →  *.xlsx (planned vs simulated vs actual + deviation stats)
                     *_time_distance_chart.pdf  (via chart_logic3.py + data_extract.py)
                     *_animator.json            (per-train route, for a front-end)
```

## Running a simulation

`final_sim_sj_4aug.py` (and its notebook twin `final_sim_sj_4aug.ipynb`) is a top-level
script, not a library — it picks its input corridor, output paths, and options via plain
module-level variables near the top of the file (`network_section`, `chart_filename`,
`excel_filename`, `animator`, `USE_HALT_DEVIATION`, `USE_SPEED_RANDOMNESS`, etc.) and runs
end-to-end when executed:

```bash
python final_sim_sj_4aug.py
```

Dependencies are listed in [requirements.txt](../requirements.txt): pandas, numpy,
openpyxl/xlsxwriter (Excel I/O), matplotlib (charting), scipy (halt-deviation
distributions), jupyter/nbconvert/notebook (the `.ipynb` variants), pygame (unused by the
files reviewed here — likely for a separate animation viewer).
