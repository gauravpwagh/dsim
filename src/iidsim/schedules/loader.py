import json
from pathlib import Path

import pandas as pd

from iidsim.domain import train

_RAW_DIR = Path(__file__).parent / "raw"


def available_corridors() -> list[str]:
    """Names usable with load_trains(), e.g. 'p_g_sprd_vzm_2days'."""
    return sorted(p.stem for p in _RAW_DIR.glob("*.json"))


def _to_ts(v):
    return None if v is None else pd.Timestamp(v)


def _to_sched(raw: dict) -> dict:
    return {stn: [_to_ts(a), _to_ts(d)] for stn, (a, d) in raw.items()}


def load_trains(corridor: str) -> list[train]:
    """Build the list of `train` objects for a corridor, e.g. load_trains('p_g_sprd_vzm_2days').

    Equivalent to the old `from input_train_data_updated_after_goods_gen.p_g_sprd_vzm_2days
    import trains`, but data-driven instead of a hardcoded source-code import -- pick the
    corridor at runtime (CLI arg / config) rather than by editing an import statement.
    """
    path = _RAW_DIR / f"{corridor}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"no schedule named {corridor!r}; available: {available_corridors()}"
        )
    with open(path) as f:
        rows = json.load(f)
    return [
        train(
            row["train_id"],
            row["tr_type"],
            _to_sched(row["schedule"]),
            row["origin"],
            row["destination"],
            row["max_speed"],
            row["instance_index"],
            _to_sched(row["real_schedule"]),
        )
        for row in rows
    ]
