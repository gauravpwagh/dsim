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
import os
import sys

import pandas as pd

from iidsim.engine import run_simulation

# Matches the deviation threshold the engine's own Excel report already uses
# (max_allowed_deviation in Simulation.run(), src/iidsim/engine/run.py) so
# "on time" means the same thing here as it does in that report.
ON_TIME_THRESHOLD_MIN = 5


def _compute_performance_stats(trains):
    """Per-train punctuality stats, derived entirely from train.calc_train_statistics()
    (src/iidsim/domain/train.py) -- the same computation the engine already runs
    and prints per train at the end of every simulation, just never surfaced
    anywhere structured. Read-only over already-finished train objects, so this
    needs no engine changes and can't affect the simulation itself."""
    per_train = []
    for tr in trains:
        stats = tr.calc_train_statistics()
        tardiness_min = stats["overall tardiness"].total_seconds() / 60
        earliness_min = stats["overall earlyness"].total_seconds() / 60
        planned_arr = tr.tr_schedule[tr.tr_destination][0]
        simulated_arr = tr.tr_sched_act[tr.tr_destination][0]
        delay_min = round(tardiness_min - earliness_min, 1)  # signed: +late, -early
        per_train.append({
            "train_id": f"{tr.train_id}_{tr.instance_index}",
            "train_type": tr.tr_type,
            "origin": tr.tr_origin,
            "destination": tr.tr_destination,
            "planned_arrival": planned_arr.strftime("%Y-%m-%d %H:%M:%S") if planned_arr is not None else None,
            "simulated_arrival": simulated_arr.strftime("%Y-%m-%d %H:%M:%S") if simulated_arr is not None else None,
            "delay_min": delay_min,
            "avg_deviation_min": round(stats["Average deviation"].total_seconds() / 60, 1),
            "on_time": abs(delay_min) <= ON_TIME_THRESHOLD_MIN,
        })

    def avg(vals):
        vals = [v for v in vals if v is not None]
        return round(sum(vals) / len(vals), 1) if vals else None

    passenger = [t for t in per_train if t["train_type"] == "p"]
    goods = [t for t in per_train if t["train_type"] == "g"]
    summary = {
        "total_trains": len(per_train),
        "on_time_threshold_min": ON_TIME_THRESHOLD_MIN,
        "on_time_pct": round(100 * sum(t["on_time"] for t in per_train) / len(per_train), 1) if per_train else None,
        "passenger_avg_delay_min": avg([t["delay_min"] for t in passenger]),
        "goods_avg_delay_min": avg([t["delay_min"] for t in goods]),
        "worst_delay": max(per_train, key=lambda t: t["delay_min"]) if per_train else None,
    }
    return {"trains": per_train, "summary": summary}


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
        stats_filename = os.path.join(config["output_dir"], "performance_stats.json")
        with open(stats_filename, "w") as f:
            json.dump(_compute_performance_stats(result["trains"]), f)
        manifest = {
            "ok": True,
            "excel_filename": result["excel_filename"],
            "chart_filename": result["chart_filename"],
            "animator_filename": result["animator_filename"],
            "stats_filename": stats_filename,
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
