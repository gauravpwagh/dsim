"""One-off migration script: dump the large auto-generated .py data modules to JSON
under src/iidsim/data/raw/. Run once from the repo root, then delete/archive.
Not part of the package -- this is a build-time conversion tool, not runtime code.
"""
import json
import os

import pandas as pd

OUT = os.path.join("src", "iidsim", "data", "raw")
os.makedirs(OUT, exist_ok=True)


def dump(name, obj):
    path = os.path.join(OUT, name)
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, sort_keys=True)
    print(f"wrote {path} ({os.path.getsize(path)} bytes)")


# ---- stations_longitude.py ----
import stations_longitude as sl
dump("station_longitudes.json", sl.station_longitudes)

# ---- wat_block_section_distances.py ----
import wat_block_section_distances as wd


def segs_to_json(segs):
    # dict keyed by (a, b) tuple -> "a|b" string key
    return {f"{a}|{b}": v for (a, b), v in segs.items()}


dump("corridors.json", {
    "krdl_ktv": {"order": wd.krdl_ktv, "segments": segs_to_json(wd.krdl_ktv_segments)},
    "sprd_vzm": {"order": wd.sprd_vzm, "segments": segs_to_json(wd.sprd_vzm_segments)},
    "psa_ktv": {"order": wd.psa_ktv, "segments": segs_to_json(wd.psa_ktv_segments)},
})
dump("block_section_distances.json", segs_to_json(wd.block_section_distances))

# ---- blocksection_times.py (single average Timedelta per section) ----
import blocksection_times as bt


def timedelta_dict_to_json(d):
    return {direc: {k: v.total_seconds() / 60.0 for k, v in inner.items()}
            for direc, inner in d.items()}


dump("blocksection_avg_times_minutes.json", {
    "g": timedelta_dict_to_json(bt.g_times),
    "p": timedelta_dict_to_json(bt.p_times),
})

# ---- blocksection_actual_times.py (distributional: values/weights) ----
import blocksection_actual_times as bat
dump("blocksection_crossing_time_distributions.json", {
    "g": bat.g_times,
    "p": bat.p_times,
})

# ---- blocksection_speeds_data.py ----
import blocksection_speeds_data as bsd
dump("blocksection_speeds.json", {
    "g": bsd.g_speeds,
    "p": bsd.p_speeds,
})

# ---- halt_deviation_fits.py (huge: per-station distribution fits) ----
import halt_deviation_fits as hdf


def fits_to_json(fits):
    out = {}
    for stn, fit in fits.items():
        fit = dict(fit)
        if "params" in fit:
            fit["params"] = list(fit["params"])
        out[stn] = fit
    return out


dump("halt_deviation_fits.json", {
    "g": fits_to_json(hdf.halt_dev_fits_g),
    "p": fits_to_json(hdf.halt_dev_fits_p),
    "station_max_g": hdf.station_max_g,
    "station_max_p": hdf.station_max_p,
})

print("done")
