# EventManager & domain-object redesign — design doc

> **Status: stage 0 implemented, verified, and now the default.** See
> [restructure-notes.md](restructure-notes.md) for the engine split this builds on, and
> [efficiency-review.md](efficiency-review.md) for the event-selection cost this was
> originally motivated by.
>
> `src/iidsim/engine/event_manager.py`. `run_simulation(..., use_event_manager=False)`
> falls back to the original `build_event_list()` path if ever needed.
> Verified via `tests/test_event_manager.py`: byte-identical `total_schedule` against the
> existing `build_event_list()` path across the three synthetic branch-coverage scenarios,
> a new tie-break scenario (two trains sharing an identical origin timestamp), and
> `p_g_sprd_vzm_2days` with randomness on (also re-checked against the existing golden
> Excel file). Manually verified against `p_g_krdl_ktv_2days` (52 trains) too: identical
> `total_schedule`, and -- with `resource_update_event()` completely untouched --
> wall-clock dropped from 69.5s to 51.0s (~27% faster) on that run alone. Stages 1-4 are
> still just proposed.

## 1. Motivation

Two separate problems, one restructure:

1. **Event selection is O(trains x stops) per event.** `build_event_list()`
   ([events.py:18](../src/iidsim/engine/events.py)) rescans every train's entire remaining
   schedule, every single event, to find the global next event -- regardless of how many
   trains actually changed since the last event (usually one, occasionally a few via
   queue/autoblock fan-out). For the largest corridor (338 trains, ~30 stops, ~20,000
   events) that's on the order of 2x10^8 comparisons spent purely on "what happens next."
2. **The domain objects are anemic.** `Station` (`DynamicStation`), `BlockSection`
   (`block_sec`), and `Train` already exist as classes with encapsulated *state*
   (`tracks`, `blsec_queue`, `tr_sched_act`, ...) but almost no encapsulated *behavior*.
   Nearly all decision-making -- platform assignment, queue priority, single/double-line
   resolution -- lives in `Simulation.resource_update_event()`
   ([run.py:25](../src/iidsim/engine/run.py)), a ~700-line method kept deliberately
   unsplit specifically because it's unsafe to split blindly. That method reaches directly
   into the objects' internals (`self.stns_event[0].tracks[stn_line][3]`,
   `self.blsec_t.blsec_queue[i:i+6]`) instead of asking the objects to act on their own
   state. This is *why* it resists splitting -- not inherent domain complexity, but that
   nothing currently owns its own decisions.

Fixing (1) alone doesn't require touching (2) at all -- they're separable, and the staged
plan below treats them that way, doing (1) first as a low-risk, self-contained win before
attempting any of (2).

## 2. Current ownership, precisely

| Object | File | Owns (state) | Reaches in from outside for (behavior) |
|---|---|---|---|
| `Station` (`DynamicStation`) | `domain/station.py` | `tracks`, `connections` | Which line to assign (`stn_line_assign`, `resolve.py:317`), platform fallback |
| `BlockSection` (`block_sec`) | `domain/block_section.py` | `blsec_queue`, `autoblsec_list`, `occ_ind` | Priority ordering (`update_blsec_queue_priority`, `priority.py:151`), single/double-line resolution, sibling redirect (`find_free_sibling_blsec`, `resolve.py:194`) |
| `Train` | `domain/train.py` | `tr_schedule`, `tr_sched_act`, `calc_tr_stats()` | Its own "what's next" -- that's tracked separately, in `Simulation.sched_act[train_id]`, a flat list the train doesn't own |

A concrete illustration of the coupling problem: `stn_line_assign` (the platform-assignment
logic) doesn't just read `Station.tracks` -- it also reads `self.stns_event`, `self.blsec_t`,
`self.sched_act`, and `self.tr_next_event`, all of which are *transient per-event state* set
fresh by `resource_update_event()` on every call, not explicit parameters. Moving this to a
`Station` method isn't a cut-and-paste -- the implicit `self.X` reads need to become explicit
arguments first (`assign_line(train, prev_station, next_station, blsec_dir_in, blsec_dir_out)`
instead of relying on ambient simulation state). Every stage below that moves logic out of
`resource_update_event()` involves this same translation step, and it's the main source of
risk -- not the logic itself, but correctly identifying everything a method implicitly reads.

## 3. Proposed architecture

```
EventManager (new)
    - owns the heap and the push/pop/staleness logic
    - drives the loop: pop -> dispatch to the relevant object -> collect schedule
      changes those objects request -> push the resulting heap entries
    - knows nothing about platform assignment, priority rules, or queue internals

Train
    + next_pending_event() -> (time, type)      <- doubles as the heap's staleness check
    + advance_to(time, type)                     <- replaces external sched_act mutation

Station
    + assign_line(train, prev_stn, next_stn, ...) -> line_id   <- absorbs stn_line_assign
    + release_line(train, time)

BlockSection
    + request_entry(train, time) -> granted | queued            <- absorbs queue_add/remove
    + release(time) -> [trains now unblocked]                    + priority ordering
```

`EventManager.pop_next()`: pop the heap -> ask that train what kind of event this is ->
call `station.assign_line(...)` or `block_section.request_entry(...)` -> those calls return
whatever new times need scheduling -> `EventManager` pushes them. The manager coordinates
timing; it does not decide outcomes.

### Why `Train.next_pending_event()` is a genuine convergence, not two separate asks

The heap's staleness check (see [section 4](#4-event-selection-the-heap)) needs exactly
one thing: "what is train X's current earliest pending time and type, right now." That is
*also* the natural OO-correct definition of "a train's own next event." Implementing it
once, as a `Train` method, serves both goals -- there's no tension between the performance
motivation and the architecture motivation here, which is part of why this restructure is
worth doing together rather than picking one.

## 4. Event selection: the heap

(Full mechanics and worked traces were covered in conversation; summarized here for anyone
reading this doc without that context.)

Replace `build_event_list()` + linear min-scan with a `heapq`-based min-heap holding one
`(time, train_order_index, train_id, type)` tuple per train's next pending event.

- **Push**: append, then sift up -- compare with parent, swap if smaller, repeat. O(log n).
- **Pop**: the minimum is always at the root (no search needed) -- remove it, move the last
  element to the root, sift down against children. O(log n).
- **Tie-break**: `train_order_index` is a fixed integer assigned once (each train's index in
  the original train list). Python compares tuples element-wise, so ties on `time` fall
  through to this index automatically -- exactly reproducing today's tie-break rule (first
  train in dataset/dict-insertion order wins), with no custom comparison code needed.
- **Lazy deletion**: one event's processing can revise *other* trains' schedules too (queue
  release, autoblock list updates touch multiple trains at once) -- so a plain heap doesn't
  work, since finding-and-removing an arbitrary element is itself O(n). Instead: push a new
  entry for any train whose time changed, and leave the old entry in place. On pop, check
  the popped entry against that train's *current* authoritative next-pending time
  (`Train.next_pending_event()`); if it doesn't match, discard and pop again. Stale entries
  cost one extra O(log n) pop-and-discard each -- never wrong results.

**Expected payoff** (event selection only, largest corridor): current approach ~2x10^8
comparisons total; heap approach ~10^6. **Measured** (`p_g_krdl_ktv_2days`, 52 trains):
69.5s -> 51.0s wall-clock, ~27% faster, with `resource_update_event()` completely
untouched -- so event selection was already a meaningfully larger share of runtime than
the "profile first" caveat below assumed. This does *not* speed up `resource_update_event()`
itself -- if that function dominates runtime on an even larger corridor, this stage helps
less than 27%. **Profile before committing to the full plan** (stages 1-4).

## 5. Scalability

Three runtime axes, plus one that isn't about runtime at all.

**Train count.** Current per-event cost is O(trains x stops); since event count also scales
with trains x stops, total event-selection cost over a run is roughly O(trains^2 x stops^2)
-- quadratic in train count. Double the trains, roughly quadruple this cost. The heap's
O(log trains) per pop/push brings this down to roughly O(trains x stops x log(trains)) --
10x more trains adds `log2(3380) - log2(338) ~= 3.3` more comparisons per operation, not a
10x multiplier. This is the main reason to do stage 0 at all: the current design gets
quadratically worse as the network/timetable grows (e.g. routine `p_g_network_2days` runs,
342 trains on the full merged network), while the heap-based one grows barely faster than
linearly.

**Simulation horizon.** Easy to miss, and arguably the worse coupling today:
`build_event_list()`'s per-train filter scans that train's *entire* remaining schedule, so a
7-day simulation costs more per rescan than a 2-day one, on top of already happening more
often -- this is where the `stops^2` term above comes from. The heap's staleness check, as
originally sketched, still costs O(stops) per pop (it rescans one train's remaining list to
confirm the popped entry is current) -- much better than rescanning *all* trains, but still
coupled to horizon length. **Addressed in stage 1 below**: cache each train's current
next-pending `(time, type)` in a dict, updated in O(1) by `advance_to()` whenever it
changes, so the staleness check becomes a lookup instead of a rescan -- fully decoupling
event selection from horizon length.

**Memory / allocation churn.** `build_event_list()` allocates a fresh O(trains x stops)-sized
list on *every event*. At scale that's real GC pressure, not just CPU comparisons. The heap
holds a bounded O(trains)-sized structure that persists for the whole run (plus a handful of
transient stale duplicates) -- no repeated large-list construction.

**Codebase scalability (not runtime).** The domain-object decomposition (stages 2-4) doesn't
reduce any Big-O -- `Station.assign_line()` does the same work `stn_line_assign()` does
today. Its payoff is that new priority rules and edge cases get a natural, isolated home
instead of all landing in the same 700-line method, and can be tested in isolation instead
of only via full-simulation runs. That's a project-scalability argument, not a performance
one, and it's the actual case for doing stages 2-4 at all.

**What this doesn't fix.** `resource_update_event()`'s own per-event cost is untouched at
every stage -- same work, same constant factor. Print-statement volume is already documented
as the dominant real-world wall-clock cost on large corridors
([efficiency-review.md](efficiency-review.md)), and this plan does nothing about it -- a real
wall-clock win at current scale likely needs both changes together, which is part of why
profiling comes before committing to the full plan (section 4). `blsec_id()`'s own linear
scan over `blocksections_list` is a *separate* scalability axis (network size, not train
count) that this plan doesn't address at all.

**Net assessment:** at today's scale (<=338 trains, 1-2 day windows) event selection is a
real but not dominant cost -- this restructure improves headroom rather than fixing an
active bottleneck. It becomes necessary, not optional, the moment train count, network size,
or simulation horizon grows meaningfully beyond what's run today.

## 6. Staged migration plan

Ordered safest-first. Each stage: extend tests first, move code, diff full run output
across a few real corridors before trusting it -- the same discipline that caught the
comprehension-scope `t`-clobbering bug during the original engine split
(see [restructure-notes.md](restructure-notes.md)).

| Stage | Change | Risk | Verification |
|---|---|---|---|
| **0** | **Done, opt-in.** `EventManager` + heap; `resource_update_event()` untouched (black box) | Low -- pure event-selection swap, no decision logic touched | Verified: `tests/test_event_manager.py` (4 scenarios incl. tie-break, all pass) + manual `sprd_vzm`/`krdl_ktv` diffs (identical `total_schedule`, golden Excel still matches) |
| **1** | `Train.next_pending_event()` / `advance_to()` replace external `sched_act` list mutation. Includes an O(1) next-pending-time cache (dict, keyed by train id), updated inside `advance_to()` -- see [Scalability](#5-scalability) for why this decouples event selection from schedule/horizon length | Low -- data-ownership move, not a decision move | Same diff suite as stage 0, plus a long-horizon scenario (multi-day) to confirm the cache stays consistent with the underlying schedule |
| **2** | `Station.assign_line()` / `release_line()` absorb `stn_line_assign` | Medium -- not flagged as one of the fragile workaround areas, but touches platform-fallback logic | Diff suite + re-run `test_platform_assignment_fallback` (already covers this exact branch) |
| **3** | `BlockSection.request_entry()` / `release()` absorb queue priority, single/double-line resolution, autoblock sequencing | **High** -- this is precisely the "intricate, comment-documented workaround" code flagged throughout this project's history | Diff suite + `test_autoblock_headway_sequencing` + `test_goods_starvation_override` must pass before *and* after; new tests for any branch not yet covered |
| **4** | Attempt sibling-redirect coverage (`find_free_sibling_blsec`), now unit-testable against a bare `BlockSection` with a synthetic queue instead of needing a full-network timing coincidence | Exploratory -- may or may not close the gap; not a prerequisite for stages 0-3 | New unit tests only; this is additive, not a behavior change |

Stages 2-3 are where the "implicit `self.X` -> explicit parameters" translation from
section 2 has to happen carefully. Recommend doing stage 3 as its own isolated review pass,
not bundled with anything else, given the risk level.

## 7. Non-goals

- No change to simulation *semantics* or output values at any stage -- every stage is
  verified as behavior-preserving via output diff before being considered done.
- Excel/chart/animator-JSON generation (`Simulation.run()`'s reporting tail,
  `iidsim.reporting`) is untouched by this plan.
- `resource_update_event()`'s print-statement volume is a separate, already-documented
  concern ([efficiency-review.md](efficiency-review.md)) and out of scope here.
- Not a rewrite -- each stage must be independently shippable and independently revertable.

## 8. Open risks

- **Sibling-redirect gap**: already undocumented/uncovered before this plan
  ([tests/test_branch_coverage.py](../tests/test_branch_coverage.py) docstring). Stage 4
  might close it; if it doesn't, that's an acceptable outcome -- it's no worse than today.
- **Single/double-line workaround logic**: the highest-risk single piece of the whole
  engine, per its own comments. Stage 3 should not proceed without the branch-coverage
  tests passing first, and probably needs additional synthetic scenarios beyond what
  exists today.
- **Implicit-state translation errors**: the most likely real bug source at every stage
  from 2 onward -- missing one of the ambient `self.X` reads a method relies on when
  converting it to explicit parameters. Mitigated by the diff-based verification, not by
  code review alone (the original engine split found its bug via output diffing, not
  inspection).

## 9. Success criteria

- Every stage: byte-identical Excel output (`tests/test_engine_smoke.py`'s golden-file
  comparison) and identical branch-coverage test results, before and after.
- Stage 0: measurable reduction in event-selection cost (profile before/after, not just
  Big-O estimation).
- Stage 1: the next-pending cache's O(1) lookups agree with a full rescan on every event, for
  at least one multi-day scenario, before the rescan fallback is removed.
- Stages 2+: the extracted logic becomes independently unit-testable against a bare
  `Station`/`BlockSection` object, without needing a full `run_simulation()` call --
  itself a concrete, checkable sign the extraction was done at the right seam.
