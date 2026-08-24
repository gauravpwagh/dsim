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

As of Aug 2026 this lives in a proper `src/iidsim/` package (previously a flat directory
of top-level scripts) — see [restructure-notes.md](restructure-notes.md) for what moved
where and why.

This documentation is split into focused files:

| File | Covers |
|---|---|
| [architecture.html](architecture.html) | A one-page flowchart of the whole system — open in a browser |
| [web-ui.md](web-ui.md) | `iidsim serve` — a local web UI for launching runs and observing results (live log, animated time-distance view, per-train schedule) |
| [domain-model.md](domain-model.md) | The core classes: `train`, station, block section, and how the physical network graph is assembled (`iidsim.domain`, `iidsim.network`) |
| [simulation-engine.md](simulation-engine.md) | The simulation engine — the event loop, conflict/priority rules, randomness models, and outputs (`iidsim.engine`) |
| [data-files.md](data-files.md) | Auto-generated reference data: station longitudes, block-section distances/crossing-times/speeds, halt-deviation statistical fits (`iidsim.data`) |
| [input-generation.md](input-generation.md) | How the per-corridor train lists that the simulator consumes are produced, from Excel timetables through the goods-scheduling notebook (`iidsim.schedules`) |
| [outputs.md](outputs.md) | The charting and data-extraction helpers, and what lands in `output_files_*` (`iidsim.reporting`) |
| [restructure-notes.md](restructure-notes.md) | Old-path -> new-path mapping, how the restructure was verified, and what was deliberately deferred |
| [efficiency-review.md](efficiency-review.md) | Compute/time/memory findings — what was fixed and verified, and what's recommended but deferred |
| [event-manager-design.md](event-manager-design.md) | Proposed (not started): a heap-based `EventManager` and giving `Station`/`BlockSection`/`Train` their own decision logic — scalability analysis and staged migration plan |

## Big picture

```
Excel infra/timetable data
        │
        ▼
src/iidsim/network/boards/*.py           (physical track graph, 3 "boards")
        │                    merged by src/iidsim/network/__init__.py
        ▼
src/iidsim/data/{geography,timing,halt_deviation}.py
        │  (reference/statistical data, loaded from data/raw/*.json)
excel_input_files_goods_sched_generation/*.xlsx
        │  (notebooks/goods_scheduling.ipynb interleaves goods trains into
        │   free block-section slots around the passenger timetable)
        ▼
src/iidsim/schedules/raw/*.json          (per-corridor train lists)
        │  loaded via iidsim.schedules.load_trains(name)
        ▼
src/iidsim/engine/{state,resolve,priority,randomness,events,run}.py
        │  THE SIMULATION ENGINE: Simulation class + run_simulation() (in run.py) --
        │  discrete-event loop over arrivals/departures, using iidsim.domain /
        │  iidsim.network as the physical model
        ▼
output_files_*/  ->  *.xlsx (planned vs simulated vs actual + deviation stats)
                      *_time_distance_chart.pdf  (via iidsim.reporting)
                      *_animator.json            (per-train route, for a front-end)
```

## Running a simulation

```bash
pip install -e .
iidsim list-datasets
iidsim run --dataset p_g_sprd_vzm_2days --corridor sprd_vzm --output-dir output_files
```

or programmatically:

```python
from iidsim.engine import run_simulation

result = run_simulation(
    corridor_dataset="p_g_sprd_vzm_2days",
    network_section="sprd_vzm",
    output_dir="output_files",
)
```

`network_section` picks which corridor's station order/distances the output chart uses
(`'psa_ktv'`, `'sprd_vzm'`, or `'krdl_ktv'`); `corridor_dataset` picks which train schedule
to load (`iidsim.schedules.available_corridors()` lists what's available). See
`run_simulation`'s docstring in `src/iidsim/engine/run.py` for the full set of
options (halt-deviation/speed-randomness toggles, seeds, autoblock stations, etc.).

For interactive use, `notebooks/run_simulation.ipynb` does the same thing in a notebook, or
`iidsim serve` starts a local web UI for launching and observing runs — see
[web-ui.md](web-ui.md).

Dependencies are listed in [pyproject.toml](../pyproject.toml): pandas, numpy, openpyxl/
xlsxwriter (Excel I/O), matplotlib (charting), scipy (halt-deviation distributions);
jupyter/nbconvert/notebook are an optional `notebooks` extra
(`pip install -e ".[notebooks]"`).
