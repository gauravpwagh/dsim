"""One-off migration script: convert the input_train_data_updated_after_goods_gen/p_g_*.py
train-object-literal files into JSON schedules under src/iidsim/schedules/raw/.
Preserves whatever slicing/filtering each source file's final `trains = [...]` line
applied (e.g. p_g_sprd_vzm_2days.py's `trains = trains[0:10]`), since that's the actual
active dataset each corridor currently runs with.
"""
import importlib.util
import json
import os
import sys
import types

SRC_DIR = "input_train_data_updated_after_goods_gen"
OUT_DIR = os.path.join("src", "iidsim", "schedules", "raw")
os.makedirs(OUT_DIR, exist_ok=True)

# The source files do `from trains import train` -- trains.py now lives at
# src/iidsim/domain/train.py. Shim the old top-level module name so these
# untouched source files still import correctly for this one-off conversion.
sys.path.insert(0, "src")
from iidsim.domain.train import train as _train_cls
_shim = types.ModuleType("trains")
_shim.train = _train_cls
sys.modules["trains"] = _shim


def ts(v):
    return None if v is None else v.isoformat()


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def train_to_dict(tr):
    return {
        "train_id": tr.train_id,
        "tr_type": tr.tr_type,
        "origin": tr.tr_origin,
        "destination": tr.tr_destination,
        "max_speed": tr.max_speed,
        "instance_index": tr.instance_index,
        "schedule": {stn: [ts(a), ts(d)] for stn, (a, d) in tr.tr_schedule.items()},
        "real_schedule": {stn: [ts(a), ts(d)] for stn, (a, d) in tr.tr_real_schedule.items()},
    }


for fname in sorted(os.listdir(SRC_DIR)):
    if not fname.endswith(".py"):
        continue
    corridor = fname[:-3]
    path = os.path.join(SRC_DIR, fname)
    mod = load_module(path, corridor)
    trains = [train_to_dict(t) for t in mod.trains]
    out_path = os.path.join(OUT_DIR, corridor + ".json")
    with open(out_path, "w") as f:
        json.dump(trains, f, indent=1)
    print(f"{corridor}: {len(trains)} trains -> {out_path}")

print("done")
