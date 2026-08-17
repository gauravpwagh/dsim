"""Synthetic train scenarios built against the real network topology, each designed to
force one of the engine's harder-to-reach branches. See docs/restructure-notes.md and
docs/efficiency-review.md for why these matter: the engine is one large function with
several branches that are easy to silently break in a refactor and had zero test
coverage before this module. Each `build_*` function returns a list[iidsim.domain.train]
for use with `run_simulation(..., trains_override=...)`.

Timings here were arrived at empirically (see the git history / PR discussion for the
trial-and-error) -- the engine's block-section/queue/platform assignment depends on
several interacting factors (which station track a train lands on, which of several
parallel block sections it's offered, exact event-processing order at tied timestamps)
that aren't fully predictable by hand from the schedule alone.
"""
import pandas as pd
from pandas import Timestamp

from iidsim.domain import train

BASE = Timestamp("2025-04-01 08:00:00")


def build_autoblock_scenario():
    """Two passenger trains through smlg-kvls (autoblock territory in this scenario --
    pass it as autoblock_stations=('smlg', 'kvls') -- and the ONLY physical line between
    them, so both trains are forced onto the same block_sec object). The second train
    departs while the first is still in transit, which should trigger the
    headway/safe-distance calculation branch (not just the "section is empty" branch
    every first train through hits).
    """
    t1 = train("T1", "p", {
        "smlg": [BASE, BASE],
        "kvls": [BASE + pd.Timedelta(minutes=20), BASE + pd.Timedelta(minutes=20)],
    }, "smlg", "kvls", 80, 0)
    t2 = train("T2", "p", {
        "smlg": [BASE + pd.Timedelta(minutes=5), BASE + pd.Timedelta(minutes=5)],
        "kvls": [BASE + pd.Timedelta(minutes=25), BASE + pd.Timedelta(minutes=25)],
    }, "smlg", "kvls", 80, 1)
    return [t1, t2]


def build_starvation_scenario():
    """A goods train (kuk -> vzm -> nml) whose departure FROM vzm (its 2nd stop, not
    origin -- goods_delay_due_to_passenger only applies from the 2nd stop onward) keeps
    finding a passenger train genuinely halting at vzm on a connected line. With a tiny
    goods_max_priority_wait_hours, the starvation override should fire well before the
    goods train would otherwise depart.
    """
    goods = train("G1", "g", {
        "kuk": [BASE, BASE],
        "vzm": [BASE + pd.Timedelta(minutes=15), BASE + pd.Timedelta(minutes=16)],
        "nml": [BASE + pd.Timedelta(minutes=40), BASE + pd.Timedelta(minutes=40)],
    }, "kuk", "nml", 60, 0)

    passengers = []
    for i in range(8):
        arr = BASE + pd.Timedelta(minutes=14 + 1.5 * i)
        dep = arr + pd.Timedelta(minutes=3)
        end = dep + pd.Timedelta(minutes=12)
        passengers.append(train(f"P{i}", "p", {
            "vzm": [arr, dep],
            "nml": [end, end],
        }, "vzm", "nml", 80, i + 1))
    return [goods] + passengers


def build_platform_fallback_scenario():
    """Five halting passenger trains converging on scmn, which has only 4 platformed
    lines (s8-s11) and several platformless ones (s1-s7, s12). With overlapping dwell
    windows, the platformed lines should be exhausted, forcing at least one train onto a
    platformless line via stn_line_assign's relaxed fallback pass.
    """
    trains = []
    for i in range(5):
        dep_pdt = BASE - pd.Timedelta(minutes=10 - i)
        arr = BASE + pd.Timedelta(minutes=2 * i)
        dep = arr + pd.Timedelta(minutes=20)
        trains.append(train(f"P{i}", "p", {
            "pdt": [dep_pdt, dep_pdt],
            "scmn": [arr, dep],
        }, "pdt", "scmn", 80, i))
    return trains
