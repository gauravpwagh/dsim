"""Block-section crossing-time and speed reference data.

Two representations of crossing time exist, kept separate because the engine uses
them differently:
  - avg_times(): one average Timedelta per section/direction -- used by the goods
    schedule generator when slotting a train into free capacity.
  - crossing_time_distributions(): the full observed-frequency distribution per
    section/direction -- used by the simulator for weighted-random sampling
    (USE_SPEED_RANDOMNESS).
"""
import json
from functools import lru_cache
from pathlib import Path

import pandas as pd

_RAW_DIR = Path(__file__).parent / "raw"


@lru_cache(maxsize=1)
def avg_times() -> dict:
    """{'g' | 'p': {'up' | 'dn': {'STN1-STN2': pandas.Timedelta}}}"""
    with open(_RAW_DIR / "blocksection_avg_times_minutes.json") as f:
        raw = json.load(f)
    return {
        tr_type: {
            direc: {k: pd.Timedelta(minutes=v) for k, v in inner.items()}
            for direc, inner in by_dir.items()
        }
        for tr_type, by_dir in raw.items()
    }


@lru_cache(maxsize=1)
def crossing_time_distributions() -> dict:
    """{'g' | 'p': {'up' | 'dn': {'STN1-STN2': {'values': [...], 'weights': [...]}}}}"""
    with open(_RAW_DIR / "blocksection_crossing_time_distributions.json") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def speeds() -> dict:
    """{'g' | 'p': {'up' | 'dn': {'STN1-STN2': speed_kmh}}}"""
    with open(_RAW_DIR / "blocksection_speeds.json") as f:
        return json.load(f)
