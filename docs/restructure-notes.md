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
| `final_sim_sj_4aug.py` + `final_sim_sj_4aug.ipynb` (duplicate copies of the same ~2,900-line engine) | `src/iidsim/engine/simulate.py` (`run_simulation()`, one copy) + `src/iidsim/cli.py` (`iidsim run`) + `notebooks/run_simulation.ipynb` (thin wrapper) |
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

## Why the engine is one large function, not six small modules

The original proposal (and the one approved) called for splitting the engine into
`engine/{state,events,resolve,priority,randomness,run}.py`. That was **not** done, and the
reason is worth being explicit about rather than silently skipping it.

Nearly every helper function in the old script reads and writes a shared set of
"current simulation state" names — `sched`, `sched_act`, `stns_event`, `blsec_t`,
`tr_next_event`, `next_event_type`, `next_event_tr_id`, `t`, `total_schedule`, and a few
more — via Python's `global` statement, since they all lived in one module. Splitting
these into separate files requires either:

- **Passing an explicit state object between modules** (the originally-envisioned
  approach) — but several of these exact names (`t`, `sched_act`, `stn_line_occ_name`,
  ...) are *also* reused as ordinary local parameter names in other, unrelated functions
  in the same file (e.g. `goods_delay_due_to_passenger(sched_act, t, t_ind,
  next_event_tr_id)` takes `t` and `sched_act` as plain parameters that shadow the
  "global" ones of the same name). A blind, automated find/replace of these names to
  `state.X` would silently corrupt those unrelated local parameters too — confirmed by
  inspection, not hypothetical. Doing this correctly requires an AST-aware tool that
  tracks per-function variable scope, which is a substantially larger undertaking than a
  text-based refactor.
- **A comprehensive regression-test suite** exercising every branch (autoblock sequencing,
  the goods-train starvation override, sibling block-section redirection, the
  platform-assignment fallback pass, speed-randomness queue propagation, ...) to catch any
  behavioral drift from a manual decomposition. `tests/test_engine_smoke.py` is a start
  (one corridor, output-diffed against a golden file) but doesn't exercise those specific
  branches — see "Recommended follow-ups" below.

Given that, the engine was instead **lifted, not decomposed**: the entire script body
(unchanged logic) now lives inside one function, `run_simulation()`, with every helper
function nested inside it instead of at module level. This is a scope-only transformation
verified to be behavior-preserving:

- Each nested function's `global X` became `nonlocal X` — same read/write semantics,
  now targeting `run_simulation`'s local scope instead of the module's.
- Parameter-name shadowing (the `t`/`sched_act` issue above) is unaffected by this move,
  because Python's scoping resolves a local parameter the same way whether the enclosing
  scope is a module or an enclosing function.
- Three names (`stn_line_occ_name`, `previous_train_type`, `prev_blsec_obj`) were never
  assigned at the old script's true top level — only inside nested functions via
  `global`. Python's `nonlocal` requires the name to already exist as a local of some
  enclosing function, so these three got an explicit `= None` pre-initialization added
  near the top of `run_simulation` (verified empirically that this is required and
  sufficient before applying it to the real file).
- The transformation was applied mechanically by a script
  (`migrations/03_build_engine.py`, kept for reference) operating on exact, pre-identified
  line numbers, rather than by hand-retyping ~2,800 lines — this removes
  transcription-error risk as a category, leaving only the specific surgical edits
  (documented above) to review.

This still delivers real value: the engine is now importable, callable multiple times with
different corridors/seeds in one process, parameterized instead of edited-by-hand, and no
longer duplicated between a `.py` and a `.ipynb`. It does not yet deliver the finer-grained
module boundaries (`resolve.py`, `priority.py`, etc.) that would make individual pieces of
the conflict-resolution logic independently unit-testable.

## Recommended follow-ups (not done here)

1. **Extend the regression-test suite** before attempting any further decomposition of
   `run_simulation`. `tests/test_engine_smoke.py` only covers one corridor's overall
   output; add one golden-output test per corridor, plus targeted tests that force each of
   the tricky branches (autoblock headway sequencing, goods-starvation override, sibling
   redirect, platform fallback) using small synthetic train sets designed to hit them.
2. **Then** decompose `run_simulation` into smaller modules, ideally with an AST-aware
   refactoring tool (or very carefully, function-by-function, running the regression suite
   after each extraction) — `state.py` (a proper class instead of a bag of nonlocals),
   `resolve.py` (block-section/platform assignment), `priority.py` (passenger/goods
   ordering), `randomness.py` (already fairly self-contained), `run.py` (the loop).
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
   `migrations/02_convert_schedules.py`, `migrations/03_build_engine.py`) once
   this restructure is reviewed and merged — they're provenance for *how* the JSON/engine
   were derived, not something meant to be re-run (their source `.py` files no longer
   exist at the paths they read from).
