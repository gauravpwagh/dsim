"""Flask app: a local web UI for launching iidsim runs and observing them.

Each run executes in its own subprocess (see runner.py for why) via a single
background worker thread that processes a queue -- one run at a time. This keeps
resource use bounded and avoids output-file collisions; it also means the
long-running simulation never blocks Flask's own request thread, so the frontend
can poll for live log output and completion status.
"""
import json
import queue
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path

from flask import Flask, Response, jsonify, request, send_file, send_from_directory

from iidsim.data import geography
from iidsim.schedules import available_corridors

NETWORK_SECTIONS = ["psa_ktv", "sprd_vzm", "krdl_ktv"]
MAX_LOG_LINES_PER_POLL = 3000
_STATIC_DIR = Path(__file__).parent / "static"

RUNS: dict[str, dict] = {}
_RUNS_LOCK = threading.Lock()
_QUEUE: "queue.Queue[str]" = queue.Queue()


def _new_run(config: dict) -> dict:
    run_id = uuid.uuid4().hex[:12]
    output_dir = Path.cwd() / "output_files_webapp" / run_id
    return {
        "id": run_id,
        "config": config,
        "output_dir": output_dir,
        "state": "queued",
        "log": [],
        "created_at": time.time(),
        "started_at": None,
        "finished_at": None,
        "returncode": None,
        "result": None,
        "error": None,
    }


def _worker():
    while True:
        run_id = _QUEUE.get()
        with _RUNS_LOCK:
            run = RUNS[run_id]
            run["state"] = "running"
            run["started_at"] = time.time()
        _execute(run)
        _QUEUE.task_done()


def _execute(run: dict):
    output_dir: Path = run["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)
    config_path = output_dir / "config.json"
    result_path = output_dir / "result.json"

    full_config = dict(run["config"], output_dir=str(output_dir))
    with open(config_path, "w") as f:
        json.dump(full_config, f)

    proc = subprocess.Popen(
        [sys.executable, "-u", "-m", "iidsim.webapp.runner", str(config_path), str(result_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    for line in proc.stdout:
        with _RUNS_LOCK:
            run["log"].append(line.rstrip("\n"))
    returncode = proc.wait()

    with _RUNS_LOCK:
        run["returncode"] = returncode
        run["finished_at"] = time.time()
        manifest = None
        if result_path.exists():
            with open(result_path) as f:
                manifest = json.load(f)
        if manifest and manifest.get("ok"):
            run["state"] = "done"
            run["result"] = manifest
        else:
            run["state"] = "error"
            run["error"] = (manifest or {}).get("error", f"runner exited with code {returncode}")


def create_app():
    app = Flask(__name__, static_folder=None)
    threading.Thread(target=_worker, daemon=True).start()

    @app.get("/")
    def index():
        return send_from_directory(_STATIC_DIR, "index.html")

    @app.get("/static/<path:filename>")
    def static_files(filename):
        return send_from_directory(_STATIC_DIR, filename)

    @app.get("/api/meta")
    def meta():
        return jsonify({"datasets": available_corridors(), "corridors": NETWORK_SECTIONS})

    @app.get("/api/network/<corridor>")
    def network(corridor):
        corridors = geography.corridors()
        if corridor not in corridors:
            return jsonify({"error": f"unknown corridor {corridor!r}"}), 404
        data = corridors[corridor]
        segments = [[a, b, km] for (a, b), km in data["segments"].items()]
        return jsonify({"order": data["order"], "segments": segments})

    @app.post("/api/runs")
    def create_run():
        body = request.get_json(force=True)
        corridor_dataset = body.get("corridor_dataset")
        network_section = body.get("network_section")
        if corridor_dataset not in available_corridors():
            return jsonify({"error": f"unknown dataset {corridor_dataset!r}"}), 400
        if network_section not in NETWORK_SECTIONS:
            return jsonify({"error": f"unknown corridor {network_section!r}"}), 400

        config = {
            "corridor_dataset": corridor_dataset,
            "network_section": network_section,
            "start_dt_mode": body.get("start_dt_mode", "planned"),
            "start_dt_manual": body.get("start_dt_manual"),
            "start_dt_buffer_minutes": body.get("start_dt_buffer_minutes", 10),
            "chart_duration_hrs": body.get("chart_duration_hrs", 23),
            "headway_distance": body.get("headway_distance", 3.6),
            "goods_max_priority_wait_hours": body.get("goods_max_priority_wait_hours", 20),
            "autoblock_stations": body.get("autoblock_stations", ["alm", "kuk", "vzm"]),
            "use_halt_deviation": body.get("use_halt_deviation", True),
            "use_speed_randomness": body.get("use_speed_randomness", True),
            "halt_deviation_seed": body.get("halt_deviation_seed", 1234),
            "speed_randomness_seed": body.get("speed_randomness_seed", 1234),
        }
        if config["start_dt_mode"] == "manual" and not config["start_dt_manual"]:
            return jsonify({"error": "start_dt_manual is required when start_dt_mode is 'manual'"}), 400

        run = _new_run(config)
        with _RUNS_LOCK:
            RUNS[run["id"]] = run
        _QUEUE.put(run["id"])
        return jsonify({"run_id": run["id"]}), 201

    @app.get("/api/runs")
    def list_runs():
        with _RUNS_LOCK:
            rows = [_summary(r) for r in RUNS.values()]
        rows.sort(key=lambda r: r["created_at"], reverse=True)
        return jsonify(rows)

    @app.get("/api/runs/<run_id>")
    def get_run(run_id):
        run = RUNS.get(run_id)
        if run is None:
            return jsonify({"error": "not found"}), 404
        since = request.args.get("since", type=int, default=0)
        with _RUNS_LOCK:
            summary = _summary(run)
            slice_ = run["log"][since:]
            # A run can produce hundreds of thousands of lines; returning the
            # whole backlog in one response (e.g. when a UI first opens an
            # already-finished run's Log tab) is what makes it feel slow to
            # load. Cap it to the most recent lines and report how many were
            # skipped -- log_total still reflects the true count so the next
            # poll's `since` stays correct.
            omitted = max(0, len(slice_) - MAX_LOG_LINES_PER_POLL)
            summary["log"] = slice_[-MAX_LOG_LINES_PER_POLL:]
            summary["log_omitted"] = omitted
            summary["log_total"] = len(run["log"])
        return jsonify(summary)

    @app.get("/api/runs/<run_id>/log.txt")
    def full_log(run_id):
        run = RUNS.get(run_id)
        if run is None:
            return jsonify({"error": "not found"}), 404
        with _RUNS_LOCK:
            text = "\n".join(run["log"])
        return Response(text, mimetype="text/plain")

    @app.get("/api/runs/<run_id>/files/<kind>")
    def download(run_id, kind):
        run = RUNS.get(run_id)
        if run is None or run["result"] is None:
            return jsonify({"error": "not found"}), 404
        key = {
            "excel": "excel_filename", "chart": "chart_filename",
            "animator": "animator_filename", "stats": "stats_filename",
        }.get(kind)
        if key is None:
            return jsonify({"error": f"unknown file kind {kind!r}"}), 400
        path = Path(run["result"][key])
        if not path.exists():
            return jsonify({"error": "file no longer exists"}), 404
        as_attachment = kind not in ("animator", "stats")
        return send_file(path.resolve(), as_attachment=as_attachment)

    return app


def _summary(run: dict) -> dict:
    return {
        "id": run["id"],
        "config": run["config"],
        "state": run["state"],
        "created_at": run["created_at"],
        "started_at": run["started_at"],
        "finished_at": run["finished_at"],
        "returncode": run["returncode"],
        "error": run["error"],
        "has_result": run["result"] is not None,
    }
