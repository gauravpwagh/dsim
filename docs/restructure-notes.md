# Package restructure notes (Aug 2026)

This documents the move from a flat directory of top-level scripts to a proper
`src/iidsim/` package, what changed, how it was verified, and — importantly — what was
deliberately **not** done and why.

## What changed: old path -> new path

| Old | New |
|---|---|
| `trains.py` | `src/iidsim/domain/train.py` |
| `stations.py` | `src/iidsim/domain/station.py` |
| `blocksections.py` | `src/iidsim/domain/block_section.py` |
| `network/*_stations_data.py` + `*_blocksections_data.py` | `src/iidsim/network/boards/{krdl_vzm,krpu_ktv,psa_scmn}.py` (each pair merged into one file) |
| `network/__init__.py` | `src/iidsim/network/__init__.py` |
| `network/list_stations_in_order.py` (non-executable reference) | `docs/reference/station_order_reference.py` |
| `station_routes.py` | `src/iidsim/network/routes.py` |
| `stations_longitude.py` | `src/iidsim/data/geography.py` (`station_longitudes()`) + `data/raw/station_longitudes.json` |
| `wat_block_section_distances.py` | `src/iidsim/data/geography.py` (`corridors()`, `block_section_distances()`) + `data/raw/corridors.json`, `block_section_distances.json` |
| `blocksection_times.py` | `src/iidsim/data/timing.py` (`avg_times()`) + `data/raw/blocksection_avg_times_minutes.json` |
| `blocksection_actual_times.py` | `src/iidsim/data/timing.py` (`crossing_time_distributions()`) + `data/raw/blocksection_crossing_time_distributions.json` |
| `blocksection_speeds_data.py` | `src/iidsim/data/timing.py` (`speeds()`) + `data/raw/blocksection_speeds.json` |
| `halt_deviation_fits.py` (5.5 MB / 225k lines of Python source) | `src/iidsim/data/halt_deviation.py` + `data/raw/halt_deviation_fits.json` (2.3 MB) |
| `input_train_data_updated_after_goods_gen/p_g_*.py` (train-object-literal source) | `src/iidsim/schedules/raw/*.json` + `src/iidsim/schedules/loader.py` (`load_trains(name)`) |
| `chart_logic3.py` | `src/iidsim/reporting/chart.py` |
| `data_extract.py` | `src/iidsim/reporting/extract.py` |
| `final_sim_sj_4aug.py` + `final_sim_sj_4aug.ipynb` (duplicate copies of the same ~2,900-line engine) | `src/iidsim/engine/{state,resolve,priority,randomness,events,run}.py` (`Simulation` class + `run_simulation()`, one copy) + `src/iidsim/cli.py` (`iidsim run`) + `notebooks/run_simulation.ipynb` (thin wrapper) |
| `2_find_goods_train_scheduling_final_7july.ipynb` | `notebooks/goods_scheduling.ipynb` (same logic, imports repointed at the new package) |

`excel_input_files_goods_sched_generation/`, `test_cases/`, `output_files_*/`, and
`animator_input_files/` are unchanged — they're data directories, not code.

The corridor/dataset selection that used to require editing a hardcoded import line in
`final_sim_sj_4aug.py` is now a CLI argument:

```bash
iidsim list-datasets
iidsim run --dataset p_g_sprd_vzm_2days --corridor sprd_vzm
```

or programmatically: `iidsim.engine.run_simulation(corridor_dataset="p_g_sprd_vzm_2days",
network_section="sprd_vzm")`.

## How the engine move was verified

Before touching anything, the repo was `git init`-ed and the original state committed as
a baseline (this repo had no version control before this restructure). The simulation was
then confirmed to be fully deterministic (fixed seeds): running the original script twice
produced byte-identical Excel cell values. That gave a golden output to diff against.

After lifting the engine into `run_simulation()`, running the new package against the
same corridor/dataset reproduced the same per-train simulated schedules (verified against
the golden run's printed output for specific trains). This is now pinned as an automated
test, `tests/test_engine_smoke.py`, which runs `run_simulation()` for the sprd_vzm
corridor and asserts its Excel output is cell-identical to `tests/golden/
p_g_sprd_vzm_2days_golden.xlsx` (captured from two independent runs of the original,
pre-restructure script, confirmed byte-identical to each other first). It passes in ~6.5s.

Three real bugs were found and fixed along the way, all pre-existing in the original
script (not introduced by the restructure):

1. Several print statements and comments contained Unicode dashes/arrows (`→`, `—`, `–`,
   `🔥`) that crash on this environment's Windows console encoding (cp1252) — this is why
   the original script never actually reached its chart/JSON output steps in this
   environment; it always died on the first such print. Replaced with ASCII equivalents
   (`->`, `--`, `-`) throughout — text-only change, no logic touched.
2. `chart_logic3.py`'s `plot_railway_chart()` called `plt.show()` right after
   `plt.savefig()` — a leftover from interactive/notebook development. In a plain script
   run on a machine with a desktop session, matplotlib can select an interactive backend,
   and `plt.show()` then opens a GUI window and blocks indefinitely waiting for it to be
   closed, which never happens in an automated run. Combined with bug #1 always crashing
   the script *before* reaching this line, the original script had apparently never once
   run to completion in this environment — bug #1 masked bug #2 entirely. Diagnosed by
   noticing a run's process consumed only ~5s of CPU time across several minutes of
   wall-clock time (a blocked-on-I/O/window signature), then finding the line. Fixed by
   replacing `plt.show()` with `plt.close(fig)` — the figure is already saved to disk at
   that point; a script has no business trying to display it.
3. `chart_filename` was hardcoded slightly differently from `excel_filename`/`animator`
   for the sprd_vzm corridor (missing `_2days` — a copy-paste inconsistency, visible in
   the pre-restructure `output_files_9aug/` listing: `p_g_sprd_vzm_time_distance_chart.pdf`
   vs. `p_g_sprd_vzm_2days.xlsx`). The new version derives all three output filenames from
   `corridor_dataset` uniformly, so this is now consistent.

## The engine split: `engine/{state,resolve,priority,randomness,events,run}.py`

The engine went through two stages, in two separate passes of this restructure.

**Stage 1 (initial restructure)**: the original 2,900-line script was *lifted, not
decomposed* — every helper function nested inside one `run_simulation()` function,
verified behavior-preserving via a scope-only transformation (`global` -> `nonlocal`).
This alone was already a real improvement (importable, parameterized, no longer
duplicated between a `.py` and a `.ipynb`), but didn't yet split the engine into the
smaller files the original plan called for — doing that safely required solving a real
problem first, described next.

**Stage 2 (this pass)**: nearly every helper function reads and writes a shared set of
"current simulation state" names — `sched`, `sched_act`, `stns_event`, `blsec_t`,
`tr_next_event`, `t`, `total_schedule`, and more. Naively converting these to `state.X`
attribute access is dangerous: several of these exact names (`t`, `sched_act`,
`stn_line_occ_name`, ...) are *also* reused as ordinary local parameter names in other,
unrelated functions in the same file (e.g. `goods_delay_due_to_passenger(sched_act, t,
t_ind, next_event_tr_id)` takes `t` and `sched_act` as plain parameters). A blind
find/replace would corrupt those unrelated locals.

The fix: don't guess which names are "shared state" vs. "local" by inspection — ask
Python's own compiler. Every nested function is a closure, and a compiled function
object's `__code__.co_freevars` tells you *exactly* which outer-scope names that
specific function reads or writes, computed by CPython's real scoping rules. This is
ground truth, not a heuristic. `migrations/04_split_engine.py`:

1. Imports the (already-lifted, already-verified) engine and reads every nested
   function's `co_freevars`.
2. Parses the source with `ast`, and for each nested function, renames only the
   `ast.Name` references matching *that function's own* freevars into `self.<name>`
   (`ast.Attribute` nodes) — never touching an `ast.Attribute` that's already qualified,
   and never touching a name outside that function's specific freevar set.
3. Splits `run_simulation`'s own top-level body into `__init__` (config/setup) and
   `run()` (the event loop + reporting), since they're now separate methods with no
   shared local scope — anything assigned in one and read in the other needs explicit
   `self.X` seeding, handled generously (over-inclusion is harmless; under-inclusion is
   a loud `NameError`, never silent corruption).
4. Assembles everything as real `ast.ClassDef`/`ast.Module` trees (not string
   concatenation with manual indentation) across `state.py` (the `SimulationState`
   `__init__`), `resolve.py`, `priority.py`, `randomness.py`, `events.py` (mixin
   classes), and `run.py` (`Simulation`, combining all mixins via multiple inheritance,
   plus `resource_update_event` and `run()`).

**Bugs this process actually caught** (all fixed, all pre-existing quirks of moving code
between scopes rather than engine-logic bugs):

- Two of `run_simulation`'s own parameters (`headway_distance`, `autoblock_stations`)
  happened to share a name with something in the shared-state set, so a blind rename of
  the top-level body would have corrupted a parameter read into a self-attribute read of
  an unset attribute. Fixed by seeding `self.X = X` from the parameter *before* the
  (necessarily blind, since this body isn't a single already-scoped function) rename
  runs on that body.
- A third parameter, `chart_duration_hrs`, was used only in the `run()` half but never
  assigned to `self` at all — `__init__` and `run()` have no shared scope, so this would
  have been a `NameError`. Same fix, generalized: any parameter read anywhere in the
  `run()` half gets seeded.
- A tuple-unpacking assignment (`station_order, segments = ...`) wasn't caught by a
  first-pass "assignment target" scan that only looked for plain `ast.Name` targets —
  fixed by handling `ast.Tuple`/`ast.List` targets too.
- **The interesting one**: `blsec_id` has a real free variable `t` (the simulation
  clock) *and*, separately, two list comprehensions using `t` as their own loop variable
  (`[(b, t) for b, t in end_times if ...]` — nothing to do with the clock). Python 3
  comprehensions have their own scope, but a naive rename pass doesn't know that, and
  turned the comprehension's loop variable into `for _, self.t in end_times` — silently
  overwriting the simulation clock with a block-section sentinel value on every
  iteration. Caught because it broke two of the branch-coverage tests (autoblock,
  platform fallback) with a `ValueError` several events into the run — diagnosed by
  running the exact same scenario through the old (pre-split) and new engine side by
  side and diffing their full debug logs to find the first line they diverged on. Fixed
  by making the rename pass comprehension-scope-aware: for `ListComp`/`SetComp`/
  `DictComp`/`GeneratorExp` nodes, names bound by any of that comprehension's `for`
  clauses are excluded from renaming within its subtree.
- `total_schedule_to_json` has a real free variable `json` — but it comes from a
  redundant `import json` statement that lived inside the original `run_simulation`'s
  own body (shadowing the top-level module import of the same name), not genuine shared
  state. Excluded from the rename targets explicitly; every generated file already does
  its own top-level `import json`.

**Verification**: `tests/` (the golden-output smoke test plus the three targeted branch
tests — autoblock headway sequencing, goods-starvation override, platform-assignment
fallback) all pass against the split engine. Beyond that, the exact same synthetic
platform-fallback scenario (the one that first caught the comprehension-scope bug) was
run through both the pre-split and post-split engine with full debug output captured,
and diffed: after normalizing memory addresses printed in object reprs, the two logs are
identical for all ~1,450 lines except the (intentionally different) output filenames.

**resource_update_event stays one method.** At ~700 lines it's by far the largest single
piece, handling arrival/departure dispatch, headway/capacity checks, priority
resolution, and queue management together. It wasn't split further in this pass — unlike
the mechanical scope-rename above, breaking up its internal control flow is a genuine
logic-level decomposition, and the branch-coverage tests this pass added (autoblock,
starvation, platform fallback) are still a small fraction of its actual branches (sibling
redirect remains untested — see below; single-vs-double-line capacity check
permutations, speed-randomness queue propagation, and more aren't covered either). Worth
revisiting once coverage is broader.

## Recommended follow-ups (not done here)

1. **Extend the regression-test suite further** before attempting to split
   `resource_update_event` itself. `tests/` now covers 3 of the trickier branches
   (autoblock sequencing, goods-starvation override, platform fallback) plus one
   golden-output smoke test, but sibling block-section redirect
   (`find_free_sibling_blsec` actually returning a different section, not just staying
   queued) proved difficult to trigger deterministically by hand-crafted train timing —
   attempted extensively (see git history for what was tried) and left uncovered. The
   single-vs-double-line capacity-check permutations in `check_next_blse_stn_occupancy`
   and speed-randomness queue propagation are also untested. Add one golden-output test
   per corridor too, not just sprd_vzm.
2. **Then** consider decomposing `resource_update_event` itself (arrival handling /
   departure dispatch / queue management as separate methods) — the same
   `co_freevars`-based technique used for the file split would apply, but this time the
   *shape* of the code changes (not just where names resolve to), which is a materially
   different and riskier kind of edit.
3. **Replace `print()`-based debug output with `logging`.** This was considered here but
   deliberately not automated: `print()` calls in this file often pass several
   comma-separated arguments meant to be concatenated (`print('a', x, 'b', y)`), while
   `logging.debug(msg, *args)` treats extra arguments as `%`-style format substitutions —
   a blind `print(` → `logging.debug(` replacement across ~500 call sites would silently
   change output formatting (or crash) in ways that are hard to catch without executing
   every code path. Worth doing, but as its own careful pass, ideally after the
   regression-test suite exists to catch mistakes.
4. **`excel_input_files_goods_sched_generation/`, `test_cases/`, `output_files_*/`** are
   still plain data directories at the repo root — could move under `data/` for
   consistency once the regression suite makes rearranging paths lower-risk to verify.
5. Delete the one-off migration scripts (`migrations/01_convert_reference_data.py`,
   `migrations/02_convert_schedules.py`, `migrations/03_build_engine.py`,
   `migrations/04_split_engine.py`) once this restructure is reviewed and merged —
   they're provenance for *how* the JSON/engine were derived, not something meant to be
   re-run (`04_split_engine.py` specifically imports `simulate.py`, which no longer
   exists now that the split it produced has replaced it).
