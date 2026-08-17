# One-off migration scripts

Used once during the Aug 2026 src/ package restructure (see
[docs/restructure-notes.md](../docs/restructure-notes.md)) to convert the original
top-level `.py` data/engine files into the new package layout. Kept for provenance --
showing exactly how `src/iidsim/data/raw/*.json`, `src/iidsim/schedules/raw/*.json`, and
`src/iidsim/engine/simulate.py` were derived from the originals.

**Not meant to be re-run**: each script imports the specific original top-level modules
it was converting (e.g. `import halt_deviation_fits`, `import stations_longitude`),
which no longer exist at those paths now that the restructure is complete.
