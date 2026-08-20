"""Subprocess entry point: `python -u -m iidsim.webapp.runner <config.json> <result.json>`.

Runs one simulation in its own fresh process and writes a small result manifest.
A fresh process per run matters here, not just for isolation-in-principle: the
engine's Simulation reads iidsim.network.stations_list / blocksections_list by
reference (not a copy) and mutates them in place (track occupancy, block-section
queues) over the course of a run -- see docs/restructure-notes.md. A second run in
the same interpreter would inherit the first run's leftover occupancy/queue state.
Spawning a fresh process per run sidesteps that entirely, the same way invoking the
`iidsim` CLI twice from a shell already does.
"""
import json
import sys

import pandas as pd

from iidsim.engine import run_simulation


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    config_path, result_path = argv

    with open(config_path) as f:
        config = json.load(f)

    if config.get("start_dt_manual"):
        config["start_dt_manual"] = pd.Timestamp(config["start_dt_manual"])
    config["autoblock_stations"] = tuple(config.get("autoblock_stations", ()))

    try:
        result = run_simulation(**config)
        manifest = {
            "ok": True,
            "excel_filename": result["excel_filename"],
            "chart_filename": result["chart_filename"],
            "animator_filename": result["animator_filename"],
        }
    except Exception as exc:  # noqa: BLE001 -- reported to the UI, not swallowed
        import traceback

        manifest = {
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
            "traceback": traceback.format_exc(),
        }

    with open(result_path, "w") as f:
        json.dump(manifest, f)

    if not manifest["ok"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
