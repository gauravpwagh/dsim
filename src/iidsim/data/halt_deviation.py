"""Per-station halt-time deviation distribution fits, used to inject realistic dwell
randomness (USE_HALT_DEVIATION). Fit from real WAT movement data; see
docs/data-files.md for the fit format ('mixture' vs 'empirical').
"""
import json
from functools import lru_cache
from pathlib import Path

_RAW_DIR = Path(__file__).parent / "raw"


def _retuple_params(fits: dict) -> dict:
    out = {}
    for stn, fit in fits.items():
        fit = dict(fit)
        if "params" in fit:
            fit["params"] = tuple(fit["params"])
        out[stn] = fit
    return out


@lru_cache(maxsize=1)
def _load() -> dict:
    with open(_RAW_DIR / "halt_deviation_fits.json") as f:
        return json.load(f)


@lru_cache(maxsize=2)  # only ever called with 'g' or 'p' -- read-only, never mutated by callers
def fits_for(train_type: str) -> dict:
    """train_type: 'g' or 'p' (case-insensitive) -> {STATION: fit_dict}"""
    return _retuple_params(_load()[train_type.lower()])


def station_max_for(train_type: str) -> dict:
    """train_type: 'g' or 'p' -> {STATION: observed_max_deviation_minutes}"""
    key = "station_max_g" if train_type.lower() == "g" else "station_max_p"
    return _load()[key]
