"""Regression tests for engine branches that tests/test_engine_smoke.py doesn't reach:
autoblock headway sequencing, the goods-train starvation override, and the
station-line platform-assignment fallback pass. See tests/scenarios.py for how each
synthetic scenario is constructed, and docs/restructure-notes.md for why this coverage
matters before attempting any further decomposition of the engine.

Sibling block-section redirect (find_free_sibling_blsec) is a known gap: it requires a
train to be re-queued on a section that stays busy while its sibling happens to become
free at exactly the right moment, which proved difficult to force deterministically by
hand-crafted timing (see the git history for what was tried). Not covered here.
"""
from iidsim.engine import run_simulation

from .scenarios import (
    build_autoblock_scenario,
    build_platform_fallback_scenario,
    build_starvation_scenario,
)


def _run(name, trains, capsys, **kwargs):
    result = run_simulation(
        corridor_dataset=name,
        network_section="psa_ktv",
        trains_override=trains,
        output_dir=str(kwargs.pop("output_dir")),
        autoblock_stations=kwargs.pop("autoblock_stations", ()),
        use_halt_deviation=False,
        use_speed_randomness=False,
        **kwargs,
    )
    captured = capsys.readouterr()
    return result, captured.out


def test_autoblock_headway_sequencing(tmp_path, capsys):
    _, out = _run(
        "scn_autoblock", build_autoblock_scenario(), capsys,
        output_dir=tmp_path, autoblock_stations=("smlg", "kvls"),
    )
    assert "time taken by last train to cover 3.6km safe distance is" in out, (
        "second train through the autoblock section never hit the headway/safe-distance "
        "branch -- it should follow the first train closely enough to trigger it"
    )


def test_goods_starvation_override(tmp_path, capsys):
    _, out = _run(
        "scn_starvation", build_starvation_scenario(), capsys,
        output_dir=tmp_path, goods_max_priority_wait_hours=0.02,
    )
    assert "-> overriding passenger priority, departing now" in out, (
        "goods train was never starved long enough to trigger the priority override"
    )


def test_platform_assignment_fallback(tmp_path, capsys):
    result, _ = _run(
        "scn_platform", build_platform_fallback_scenario(), capsys,
        output_dir=tmp_path,
    )
    platforms = []
    for data in result["total_schedule"].values():
        sim = data["simulated"]
        for entry in sim[1:-1:3]:
            if len(entry) > 1 and entry[0] == "scmn":
                platforms.append(entry[2])

    assert len(platforms) == 5, f"expected 5 scmn stops, got {platforms}"
    assert 0 in platforms, (
        "no train was forced onto a platformless line -- the 4 platformed lines at scmn "
        "should have been exhausted by the other halting trains"
    )
