# Web UI — running and observing simulations in a browser

`iidsim serve` starts a local Flask app (`src/iidsim/webapp/`) with a form to configure and
launch a run, a live log, and, once the run finishes, an animated time-distance view, a
per-train schedule browser, and download links for the three output files.

```bash
pip install -e ".[webapp]"
iidsim serve --port 5000
```

Then open `http://127.0.0.1:5000/`. Run it from the repo root (same requirement as
`iidsim run`, since output paths are relative to the current directory).

## How a run executes

Each run is launched as its own subprocess (`iidsim.webapp.runner`), not called in-process.
This isn't just isolation-for-its-own-sake: `Simulation.__init__` reads
`iidsim.network.stations_list` / `blocksections_list` **by reference** and mutates them in
place over the course of a run (track occupancy, block-section queues -- see
[restructure-notes.md](restructure-notes.md)). A second run in the same interpreter would
inherit the first run's leftover state. A fresh process per run sidesteps that the same way
running the `iidsim` CLI twice from a shell already does. A single background worker thread
processes queued runs one at a time, so output files never collide and the server stays
responsive to log polling while a run is in progress. Each run's outputs land under
`output_files_webapp/<run_id>/`.

## What the UI shows

- **Log** — the run's stdout, streamed live via polling (`GET /api/runs/<id>?since=N`).
- **Visualize** — a canvas time-distance chart (station distance on Y, time on X) built from
  the run's animator JSON, scrubbable and playable, with passenger/goods filters, a train-id
  search that highlights matching trains, and hover tooltips. This is the same per-train
  route data written to `*_animator.json` (see [outputs.md](outputs.md)), just rendered
  interactively instead of consumed by an external animator.
- **Schedule** — a searchable list of every train with its full stop-by-stop simulated
  schedule (station, line, platform, arrival, departure).
- **Files** — download links for the Excel report, the time-distance chart PDF, and the
  animator JSON.

## Not included

Deviation stats (simulated vs planned/actual) live in the Excel report's extra sheet but
aren't surfaced in the UI itself -- the Visualize/Schedule tabs are built directly from the
animator JSON, which only carries the simulated schedule. Download the Excel report for
deviation numbers, or treat this as a follow-up if it's needed regularly.
