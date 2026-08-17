# One-off migration scripts

Used once during the Aug 2026 src/ package restructure (see
[docs/restructure-notes.md](../docs/restructure-notes.md)) to convert the original
top-level `.py` data/engine files into the new package layout, and later to split the
lifted engine into `src/iidsim/engine/{state,resolve,priority,randomness,events,run}.py`.
Kept for provenance -- showing exactly how `src/iidsim/data/raw/*.json`,
`src/iidsim/schedules/raw/*.json`, and the engine module split were derived.

- `01_convert_reference_data.py`, `02_convert_schedules.py` -- converted the original
  top-level data `.py` files to JSON.
- `03_build_engine.py` -- lifted the original `final_sim_sj_4aug.py` script into one
  `run_simulation()` function (module-level `global` -> nested-function `nonlocal`).
- `04_split_engine.py` -- split that lifted function into the class-based
  `state`/`resolve`/`priority`/`randomness`/`events`/`run` files, using each nested
  function's compiled `co_freevars` (from Python's own compiler, not guesswork) to
  safely rewrite shared-state references to `self.X`. See restructure-notes.md for the
  bugs this caught (comprehension-scope shadowing, parameter/attribute name collisions)
  and how the result was verified.

**Not meant to be re-run**: each script imports the specific original modules it was
converting (e.g. `import halt_deviation_fits`, `import stations_longitude`,
`import iidsim.engine.simulate`), which no longer exist at those paths now that the
restructure is complete.
