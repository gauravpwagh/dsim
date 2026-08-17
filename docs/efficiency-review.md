# Compute / time / memory efficiency review

> Written when the engine was still one file, `src/iidsim/engine/simulate.py`. It was
> later split into `engine/{state,resolve,priority,randomness,events,run}.py` (see
> [restructure-notes.md](restructure-notes.md)) — the specific line references below
> predate that split, but the findings and fixes described are unaffected by it (the
> split was a pure scope/location change, not a logic change).

Reviewed `src/iidsim/engine/simulate.py` (the hot path — everything runs through this once
per event) plus the domain and reporting layers. Findings are split into what was fixed
and verified against `tests/test_engine_smoke.py` (byte-identical Excel output to the
pre-existing golden run), and what's recommended but not attempted here because it needs
more test coverage first — consistent with the caution in
[restructure-notes.md](restructure-notes.md) about this engine having essentially no
regression coverage for its trickier branches.

## Fixed and verified

1. **O(n) linear scans over `trains` replaced with O(1) dict lookups.** Several
   spots — resolving which train occupies a station line, which train is on the
   previous/next block section, and the main loop's per-event train lookup — did
   `for t in trains: if t.train_id == x: ...` or `next(tr for tr in trains if ...)` scans.
   For the largest corridor (338 trains), each of these was a full pass over the train
   list, repeated multiple times per event. Added `trains_by_id` (built with `setdefault`
   to preserve the original first-match-wins semantics for the documented case where a
   train_id repeats across instances) and `trains_by_instance_id` (keyed exactly like
   `sched_act`, since `next_event_tr_id` is already `f"{train_id}_{instance_index}"`).
2. **Eliminated 3 redundant `event_list.index(next_event_time)` calls per event.** The
   main loop computed the same index four separate times (each an O(len(event_list))
   scan) to pull four adjacent values out of the flat event list. Computed once, reused.
3. **Removed dead code and a redundant O(trains x rows) pass in the Excel-sheet
   builder.** A `df_sorted` value was computed and immediately discarded before being
   unconditionally overwritten two lines later. Separately, a manual per-train-ID filter
   pass that pre-interleaved rows had no effect on the final output (a later groupby-based
   re-sort already re-groups and reorders everything, and preserves each train's row order
   either way) — collapsed to a single `pd.concat`.
4. **Replaced `copy.deepcopy` with structural copies where the leaf values are
   immutable.** `train.tr_sched_act` and the engine's `sched_act`/`given_sched` are
   dicts of lists containing only `str`/`pandas.Timestamp` — both immutable, so
   `copy.deepcopy`'s recursive traversal and memo-tracking buys nothing over a plain
   per-list rebuild, which is considerably cheaper.
5. **Cached `halt_deviation.fits_for()`.** It reprocessed (tuple-converting `params` for)
   all ~100-122 station fit entries on every call; now cached since the result is never
   mutated by callers.
6. **Skip loading halt-deviation/speed-randomness reference data entirely when those
   features are disabled.** `run_simulation(..., use_halt_deviation=False,
   use_speed_randomness=False)` was still unconditionally deserializing and reprocessing
   `halt_deviation_fits.json` (2+ MB) and the crossing-time-distribution JSON every call,
   even though the functions that consume them (`add_halt_randomness`,
   `add_speed_randomness`) already check the flag and return before ever touching that
   data. Verified the disabled path still runs end-to-end correctly (zero-deviation output,
   as expected).
7. **Fixed the blocking `plt.show()`** found while debugging the restructure (see
   restructure-notes.md) — turned an indefinite hang into a millisecond `savefig`+`close`.
8. Removed two now-dead `import copy` statements (one was already unused before this
   review; `block_section.py` never called anything from it).

## Recommended, not implemented here

These need either a broader regression suite (to safely verify no behavioral drift on the
trickier branches — autoblock, starvation override, sibling redirect) or touch
chart-rendering output that the current smoke test doesn't check pixel/vector-for-vector:

1. **Event selection via a priority queue instead of full-rebuild-and-rescan.**
   `build_event_list()` re-scans every train's entire schedule list on every single event
   to find the next one (`min()` over a freshly filtered copy), which is roughly
   O(trains x stops) per event rather than O(log n) with a heap. This is the single
   biggest remaining algorithmic cost, but replacing it changes the tie-breaking mechanics
   when multiple events share an exact timestamp — needs care and test coverage before
   touching it.
2. **`blsec_id()` and a few related functions still linear-scan `blocksections_list`**
   with string-prefix matching (`.startswith()`) rather than using the existing
   `blsec_lookup` dict or a station-pair-keyed index. Not changed because `blsec_id`'s
   candidate-selection logic (direction filtering, tie-breaking between parallel
   dn1/up1/mid1 sections) is exactly the kind of intricate, comment-documented-workaround
   code this project's own notes already flag as too risky to touch without a fuller test
   suite first.
3. **`reporting/extract.py` uses `df.iterrows()`** in both `filter_df_by_date_window` and
   `get_formatted_data_from_df` — a well-known pandas anti-pattern (row-by-row Python
   objects with type-coercion overhead instead of vectorized operations). Lower priority
   than the engine fixes since it only runs once per simulation run, not once per event,
   but would matter more for larger corridors' chart generation.
4. **`chart.py`'s label-placement algorithm is O(trains² x stops)** in the worst case
   (each train's label searches all previously-placed labels for the least-crowded spot).
   Only affects PDF chart generation time, not simulation correctness; fixing properly
   would need a spatial index (grid bucket or KD-tree) rather than a one-line change.
5. **Debug print volume.** Already discussed in restructure-notes.md's follow-ups —
   deliberately not automated (`print(a, b, c)` -> `logging.debug(...)` isn't a safe blind
   substitution because of `%`-style argument semantics) but real: on the largest corridor,
   printing dominates wall-clock time far more than any of the above compute costs.

## Memory note

`blsec_queue`/`autoblsec_list` store entries as flat lists in repeating 6-element groups
rather than a list of small objects/namedtuples. This looks like a readability wart, but
it's actually the more memory-frugal representation at this scale (no per-object header
overhead) — left as-is; the queues involved are small (bounded by how many trains can
contend for one block section at once), so this isn't a real cost either way.
