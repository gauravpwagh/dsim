"""Station longitudes and per-corridor station order / segment distances.

Source: WAT_Infra_Data.xlsx (Station sheet MANLONGITUDE column; Block Section sheet
MANINTRDIST column), converted to JSON by scripts_migration_convert_data.py.
"""
import json
from functools import lru_cache
from pathlib import Path

_RAW_DIR = Path(__file__).parent / "raw"


def _unkey(segments: dict) -> dict:
    """'a|b' string keys (JSON can't hold tuple keys) -> (a, b) tuples."""
    return {tuple(k.split("|")): v for k, v in segments.items()}


@lru_cache(maxsize=1)
def station_longitudes() -> dict:
    """{station_code: longitude_float}"""
    with open(_RAW_DIR / "station_longitudes.json") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def corridors() -> dict:
    """{'krdl_ktv' | 'sprd_vzm' | 'psa_ktv': {'order': [...], 'segments': {(a, b): km}}}"""
    with open(_RAW_DIR / "corridors.json") as f:
        raw = json.load(f)
    return {
        name: {"order": data["order"], "segments": _unkey(data["segments"])}
        for name, data in raw.items()
    }


@lru_cache(maxsize=1)
def block_section_distances() -> dict:
    """{(station_a, station_b): distance_km} across all corridors combined."""
    with open(_RAW_DIR / "block_section_distances.json") as f:
        return _unkey(json.load(f))
