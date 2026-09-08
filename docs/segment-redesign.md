# Segment redesign — design doc

> **Status: done.** All six steps below are implemented and verified. This document
> records the design discussion and verification, the same way
> [event-manager-design.md](event-manager-design.md) does for that (larger, earlier)
> redesign. **Section 5** records a later follow-up that unified two orderings steps
> 1-6 had deliberately kept independent (`stn_west`/`stn_east` naming vs. `stn_up`/
> `stn_down` direction) — read it alongside the rest; several statements below (most
> visibly in section 2's `conn_base()` bullet, and step 2's "deliberately independent
> of `stn_west`/`stn_east`") describe the pre-unification design and are superseded
> there.

## 1. Motivation

`krdl_bchl_dn1` and `krdl_bchl_up1` have always been two independent top-level
`block_sec` objects, tied together only by a naming convention (`{west}_{east}_{dirsuffix}`)
that other code has to reverse-engineer by string-splitting whenever it needs "the other
lines for this station pair" (`BlockSection.find_free_sibling`'s
`'_'.join(self.name.split('_')[:-1])`, or the engine's own `blsec_by_pair` index added
in a prior pass). That's backwards from how a block section actually works physically: a
station pair has *one* segment of track, which may carry more than one physical line
(`dn1`/`up1`, and sometimes a shared `mid1`/`mid2`) — the segment is the real unit, the
lines are a property of it, not independent top-level things that happen to share a name
prefix.

Separately, the engine's notion of travel direction (`'up'`/`'dn'`) has always come from
comparing two stations' geographic `longitude` — a proxy for the real convention (up =
toward a reference/"headquarters" end, down = away from it), not the convention itself.
It happens to agree with longitude in this network today, but there was no way to state
the real convention directly, and no way to source it from anything other than the
`station_longitudes` reference data.

Both problems point at the same fix: give the station-pair grouping a real identity
(`Segment`), and let that identity carry the domain's actual up/down convention
(derived from how branches are listed from their reference end), independent of the
longitude-based naming `block_sec` objects already have.

A third problem, found while building `Segment` (step 1's `__init__` validation exists
specifically because of it): the raw board data itself is where `stn_west`/`stn_east`/
`length` actually get duplicated in the first place. `network/boards/*.py` declared each
physical line as an independent `block_sec(dir, stn_a, stn_b, length, conns,
stations_list)` call, repeating `stn_a`/`stn_b`/`length` by hand on every line sharing a
pair (`krdl_bchl_dn1` and `krdl_bchl_up1` each separately writing out `'krdl'`, `'bchl'`,
`9.14`). Nothing prevented those copies from drifting apart — a `Segment` built from them
could only detect disagreement after the fact, not prevent it. Step 4 below is the actual
fix for that, not just a check for it.

## 2. What already existed (and what didn't need to change)

- `block_sec` objects, their names, `dir_mvmt`, occupancy/queue state, and the
  longitude-based `stn_west`/`stn_east` naming they compute in their own constructor —
  unchanged throughout. Every existing consumer of a `block_sec` (`blocksections_list`
  iteration, `Station.connections` keys, the animator JSON, every test that builds a
  synthetic `block_sec`) keeps working exactly as before.
- `blsec_by_pair` / `blsec_by_station` (`SimulationState`, added in a prior pass) — the
  station-pair and single-station indexes that replaced `blsec_id()`'s full-network
  linear scans. `Segment` is built *from* `blsec_by_pair`'s grouping, not instead of it;
  see [efficiency-review.md](efficiency-review.md) recommendation #2.
- `network/routes.py`'s per-branch station-sequence lists (`KRDL_TO_KRPU`,
  `KRPU_TO_KTV`, ...) — previously unused/dead reference data (see
  [domain-model.md](domain-model.md)'s `station_routes.py` section) turned out to be
  *exactly* the "sequence of stations from headquarters, per branch" input this redesign
  needed, and became load-bearing rather than being replaced.
- `conn_base()`'s own internal west/east sort — deliberately **not** touched. It's a
  canonical *key/naming* convention (what a segment or block section is called), not a
  travel-direction decision, and `Segment`'s own construction depends on that naming
  already existing — changing it would be circular, and a much larger, unrelated blast
  radius than what this redesign is about. `block_sec.__init__`'s own west/east naming
  logic is likewise untouched *in behavior* — it was only extracted into a standalone
  `sort_west_east()` function (step 4) so `Segment.new()` could reuse the exact same
  comparison rather than risk a second, independently-written one disagreeing with it in
  an edge case; this was a pure refactor, verified via the full test suite before
  proceeding, not a behavior change.

## 3. The six steps

### Step 1 — `Segment`: a named object over the existing grouping

`iidsim.domain.Segment` (`src/iidsim/domain/segment.py`) wraps the `block_sec` line
objects sharing one station pair (`blsec_by_pair[base]`), and holds the physical facts
common to all of them — `stn_west`, `stn_east`, `length` — which were previously
duplicated identically on every line object for lack of anywhere else to live. Verified
empirically before writing this, not assumed: across all 92 real segments, every line
sharing a base agrees on endpoints and length; `Segment.__init__` raises if it ever
doesn't.

`Segment` owns **no mutable simulation state** — occupancy and queueing stay on the line
objects (`dn1`/`up1` can be simultaneously occupied by two different trains; that must
never become a segment-level fact). `Segment.lines_for_direction(direction)` mirrors the
direction-compatible filter `blsec_id()` already applied inline.

Originally built once *per run*, in `SimulationState.__init__`, as `self.segments_by_pair`,
alongside the existing `self.blsec_by_pair` — step 5 below moved this to once *ever*, at
network-import time.

### Step 2 — `stn_up` / `stn_down`: direction from branch order, not longitude

`network/routes.py` gained `BASE_SEGMENTS` (the 8 existing per-branch lists, now
registered in one place) and `branch_order()`: `{{stn_a, stn_b}: (stn_up, stn_down)}`,
derived by walking consecutive pairs in each branch — the station listed earlier (closer
to the branch's reference end) is `up`, the next one is `down`. Raises on a genuine
conflict between two branches rather than picking one silently.

Checked directly against the real data before trusting it, not assumed:

- All **92/92** real network segments get a known branch order, including both
  hand-built inter-board bridge segments (`mvw_ktv`, `gtlm_vzm`) — these turned out to
  already be present in `routes.py`'s station sequences, so no gap-filling was needed.
- **Zero** directional conflicts between branches.
- Cross-checked against the existing longitude-based convention across all 92 segments:
  **100% agreement** (`stn_west == stn_up` and `stn_east == stn_down` everywhere in this
  network). This was the key result that made step 3 low-risk: migrating direction
  determination onto branch order couldn't change any outcome for the current data.

`Segment` gained optional `stn_up`/`stn_down` (validated to actually be the segment's own
two stations) and `direction_of_travel(from_stn, to_stn)`, returning `'dn'`/`'up'` or
raising rather than guessing if the order is unknown or the stations aren't this
segment's endpoints.

### Step 3 — migrating the engine off longitude

Every genuine "which way is this train going" computation in the engine — as opposed to
naming/keying, which stayed on longitude — now goes through a new
`Simulation.direction_of_travel(stn_a, stn_b)` (`resolve.py`), which delegates to the
relevant `Segment`. Found by grepping every `station_longitudes[...]` / `.longitude` use
across the engine before starting, not assumed to be a short list: **10 call sites**
across `resolve.py` (`blsec_id`'s `train_dir`, `outgoing_blsec_name`'s `wanted`,
`train_direction()`'s return value), `priority.py` (`get_prev_blsec_obj`'s `wanted`), and
`run.py` (`_queue_dir`, `current_train_dir`, and five identical `_expected_dir`
sanity-check assertions inside `resource_update_event`).

Each substitution preserves the exact prior output type and value (a string where the
original produced a string, an int 0/1 where the original produced 0/1) rather than
"fixing" anything about how that value is used downstream. A couple of sites turned out
to have an internal 0/1 labelling that looks inverted relative to the `'up'`/`'dn'`
string convention used elsewhere (e.g. `train_direction()` returning 1 feeds into what's
labelled `up_dir_stn_count`, not `dn_dir_stn_count`) — that inconsistency, whether
original design intent or a long-standing quirk, was left completely alone; only the
*source* of each value changed, never its downstream meaning.

### Step 4 — raw board data: declare each segment once, not per line

`Segment.new(stn_a, stn_b, length, stations_list)` (a classmethod, bypassing `__init__`'s
"lines required" check via `object.__new__`) declares a segment's shared facts exactly
once and returns it empty; `add_line(dir_mvmt, conns)` then constructs one physical line,
always reusing that same segment's own already-fixed `stn_west`/`stn_east`/`length`
rather than taking them as separate arguments. West/east comes from the new
`sort_west_east()` (extracted from `block_sec.__init__`, see above) — the same function,
not a second implementation — so `add_line()`'s lines can never disagree with the segment
that made them, even for two adjacent stations sharing an exact longitude (the one edge
case where independently re-deriving the same comparison twice, with arguments in a
different order, isn't guaranteed to agree).

`network/boards/{krdl_vzm,krpu_ktv,psa_scmn}.py` were rewritten to use this — every
station pair now gets one `Segment.new(...)` and one `.add_line(...)` per physical line,
e.g.:

```python
_seg_krdl_bchl = Segment.new('krdl', 'bchl', 9.14, stations_list)
krdl_bchl_dn1 = _seg_krdl_bchl.add_line('dn1', {...})
krdl_bchl_up1 = _seg_krdl_bchl.add_line('up1', {...})
```

`network/__init__.py`'s 4 hand-built inter-board bridge lines (`mvw_ktv_dn1`/`up1`,
`gtlm_vzm_dn1`/`up1`) were converted the same way, by hand (small enough not to need
scripting).

**Not hand-edited.** 174 executable `block_sec(...)` calls across the three board files
(101 in `krdl_vzm.py`, 29 in `krpu_ktv.py`, 44 in `psa_scmn.py`), given the volume and
the stakes of transcribing real railway distances/connections by hand, were rewritten by
a script (kept in the session scratchpad, not committed to the repo): parse each file's
AST, group `block_sec(...)` call nodes by station pair, and regenerate only those
specific lines in place — preserving every comment, blank line, and unrelated statement
untouched, and extracting each call's `conns` dict via `ast.get_source_segment` (its
exact original source text, never re-serialized) so there was no opportunity for a
manual-transcription-style error to creep in during the rewrite itself. 5 further
`block_sec(...)` calls exist only as disabled reference comments (1 in `krdl_vzm.py`, 4
in `krpu_ktv.py`) and were deliberately left untouched, still text, not executed either
way.

### Step 5 — stop re-deriving `Segment` objects on every `Simulation()` call

Step 4 fixed the raw data, but `state.py` didn't know that yet — `SimulationState.__init__`
still re-grouped `blocksections_list` into `blsec_by_pair` and reconstructed *fresh*
`Segment` objects (with a fresh `routes.branch_order()` lookup for `stn_up`/`stn_down`)
on every single `Simulation()` call, throwing away the grouping the board files had
already built correctly once, at import time, via `Segment.new()`/`add_line()`.

Each board file now also exports `segments_by_pair` (`{base_name: Segment}`), built by
registering every `Segment.new(...)` result as it's created — one extra line
(`segments_by_pair[_seg_X.name] = _seg_X`) right after each declaration, added by a
second, much smaller targeted script (the files were already in step 4's exact syntactic
shape by this point, so a simple line-pattern match was enough — no AST needed this
time). `network/__init__.py` merges the three boards' `segments_by_pair` dicts plus the
two inter-board bridges' segments into one, once, checking directly for station-pair key
collisions across boards first (none exist — verified, not assumed) rather than risking
a silent dict-overwrite. `state.py` then just does `self.segments_by_pair =
_network.segments_by_pair` — no re-grouping, no reconstruction, no re-validation.

`Segment.__init__`'s endpoint/length check isn't dead code from this — it still runs
exactly once per line, inside `add_line()`, at board-import time; `Simulation()` calls
after that just reuse the same, already-validated objects.

**A new, different check, and what it found.** `network/__init__.py` also gained a
one-time cross-check: `segments_by_pair`'s lines and `blocksections_list` should be the
exact same set of `block_sec` objects, just grouped two different ways — not a
value-agreement check (structurally guaranteed by step 4), but a check that the merge in
step 5 didn't *omit* or *duplicate* anything. It immediately found a real, pre-existing
bug unrelated to this whole redesign: `krdl_vzm.py`'s `vbl_dnv` segment declares three
lines (`dn1`/`up1`/`mid1`), but `blocksections_list` only ever included `dn1`/`up1` —
`mid1` has been built and silently unused this whole time. Confirmed not introduced by
this session (step 4's structural-equivalence check already proved `blocksections_list`
is byte-for-byte unchanged from before). Discussed with the user rather than resolved
unilaterally either way — left exactly as found, with the new check explicitly exempting
`vbl_dnv_mid1` by name (`network/__init__.py`'s `_KNOWN_ORPHANED_LINES`) so it doesn't
mask a *different* future omission.

`self.blsec_by_pair` deliberately stays sourced from `blocksections_list`, not from
`segments_by_pair`'s lines — switching it would have silently started including the
orphaned `vbl_dnv_mid1` in real candidate resolution (`blsec_id()`, etc.), a genuine
behavior change this step does not make. (Step 6 below trims the orphan out of
`segments_by_pair`'s lines entirely, which makes this particular concern moot in
practice — but `blsec_by_pair` was left exactly as this step put it, not revisited.)

### Step 6 — consolidating candidate-list construction onto `lines_for_direction()`

The last item from this document's own "what's still open" list (see below, previously):
`blsec_id()`, `outgoing_blsec_name()`, and `check_next_blse_stn_occupancy()` still built
their station-pair candidate lists by hand — `self.blsec_by_pair.get(base, [])` plus,
where direction mattered, an inline "same-direction-or-mid" filter — duplicating exactly
what `Segment.lines_for_direction()` exists to do. All three now call it (or `.lines`
directly where no filtering was needed) instead. `outgoing_blsec_name()`'s two-pass
priority loop (prefer an exact-direction line, fall back to a `mid` one) is unaffected —
narrowing its candidate list to `lines_for_direction(wanted)` first is behaviorally
identical to filtering nothing, since a line matching neither loop's condition could
never have been selected anyway.

`get_prev_blsec_obj()` (`priority.py`) was deliberately left alone: it excludes `mid`
lines entirely (no "or `dir_mvmt.startswith('mid')`" fallback), unlike
`lines_for_direction()`'s semantics — not a safe drop-in there, and not part of what was
asked.

**This resurfaced the `vbl_dnv_mid1` discrepancy in a new way.** `Segment.lines` (unlike
`blsec_by_pair`, still sourced from `blocksections_list`) included the orphaned line, so
`lines_for_direction()` would have started surfacing it as a live candidate again —
silently reintroducing the exact behavior change step 5 deliberately avoided. Fixed at
the source instead of working around it at each call site: `network/__init__.py` now
strips `_KNOWN_ORPHANED_LINES` out of every `Segment`'s `.lines` right after the existing
cross-check identifies them, so `segments_by_pair`'s lines and `blocksections_list` agree
exactly everywhere, permanently — without touching the raw board data, `blocksections_list`
itself, or revisiting the "leave it as-is" decision on `vbl_dnv_mid1` from before.

## 4. Verification

- **Adjacency assumption checked directly**: `direction_of_travel()` requires its two
  stations to be adjacent (share a real `Segment`). Verified for every consecutive
  station pair in every train's own schedule, across every dataset in
  `iidsim.schedules` — zero mismatches, so no `KeyError` risk in practice.
- **Structural equivalence, for step 4 specifically**: before trusting any rewritten
  board file, the OLD and NEW versions were loaded in isolated namespaces in the same
  process and every resulting `block_sec`'s name, `dir_mvmt`, `length`, `stn_west`/
  `stn_east`, `stn_conns`, and `blocksections_list` order were compared directly —
  exact match for all three boards, before the file replaced the original on disk.
- **Full test suite** after every step (42/42 at completion, including
  `tests/test_segment.py` and the byte-identical golden Excel comparison).
- **Manual before/after diffs** (`git stash` the step's change, run, `git stash pop`, run
  again, compare) of the complete pickled `total_schedule`, on real multi-day corridors
  not covered by the golden test — `krdl_ktv` after step 1, `krdl_ktv` again after step
  2, `krdl_ktv` / `sprd_vzm` / `ktv_psa` after steps 3, 4, 5, and 6 each. Byte-identical
  every time. Between them these three corridors' trains cross every one of the three
  rewritten boards and both hand-edited inter-board bridges (`krdl_ktv`'s route ends via
  `mvw` → `ktv`; `sprd_vzm`'s ends via `gtlm` → `vzm`), so steps 4-6's changes are
  exercised by real train movements on every file they touched, not just re-loaded and
  left unused.
- **`blsec_by_pair` vs. `segments_by_pair` divergence checked directly, for step 5**:
  confirmed in a real `Simulation` instance that `blsec_by_pair['vbl_dnv']` still excludes
  the orphaned `mid1` line (matching pre-step-5 behavior exactly) while
  `segments_by_pair['vbl_dnv'].lines` included it at the time (an accurate record of what
  was actually built) — the deliberate asymmetry described in step 5 above, confirmed
  rather than assumed correct. (Step 6 later trimmed `segments_by_pair`'s copy too, so
  this specific asymmetry no longer exists — see step 6.)

## 5. Later unification: `stn_west`/`stn_east` merged into `stn_up`/`stn_down`

Steps 1-5 above deliberately kept two independently-sourced orderings of the same
station pair: `stn_west`/`stn_east` (longitude, for naming — what a segment/line is
*called*) and `stn_up`/`stn_down` (branch order, for `direction_of_travel()` — which
way a train is actually going). That split was itself the point at the time: naming
had to keep working for every station pair (including ones with no branch-order
coverage), while direction needed the real railway convention, not a proxy for it.

Once step 2's check confirmed 100% agreement between the two orderings across all 92
real segments, the split stopped earning its complexity — two call sites
(`sort_west_east()` for naming, `branch_order()` for direction) computing what was, in
practice, always the same answer, with naming as the one that could never fail (always
had a longitude to fall back on) and direction as the one that raised if branch order
was missing. Asked directly whether `stn_up`/`stn_down` should also just *be* the
naming convention; the answer was yes.

**What changed:**

- `sort_west_east()` (in `block_section.py`) is now `sort_up_down()` — the sole
  ordering function used for identity, naming, *and* direction. It tries
  `network.routes.branch_order()` first; only for a pair outside the registered
  network does it fall back to longitude (verified: never actually triggered for any
  of the 92 real segments — branch order covers all of them, same as step 2 found).
- `block_sec` and `Segment` no longer have separate `stn_west`/`stn_east` and
  `stn_up`/`stn_down` attributes — just `stn_up`/`stn_down`. Naming
  (`STNUP_STNDOWN_DIRSUFFIX`) and `direction_of_travel()` now read from the exact same
  two attributes, so they can never again silently diverge the way independently
  re-deriving the same comparison twice always risks.
- `Segment(name, lines)` no longer takes separate `stn_up=`/`stn_down=` arguments —
  they're derived from `lines[0]` (which already carries them), same as `stn_west`/
  `stn_east` always were. `Segment.new()`/`add_line()` are otherwise unchanged in
  shape, just sourcing `stn_up`/`stn_down` from `sort_up_down()` instead of `stn_west`/
  `stn_east` from `sort_west_east()` plus a separate `branch_order()` lookup.
- `resolve.py`'s `conn_base()` — described in section 2 above as "deliberately not
  touched" during steps 1-6 because changing it would be circular with `Segment`'s own
  construction — now calls `sort_up_down()` directly, the same function `block_sec`/
  `Segment` naming uses, rather than its own independent west/east comparison. This
  closes the exact class of discrepancy the rest of this redesign exists to eliminate:
  before this change, `conn_base()` and `block_sec.__init__` computed a segment's name
  via two separately-written longitude comparisons that happened to agree, not one
  comparison both relied on.

**Design choice: kept the longitude fallback rather than hard-failing.** A stricter
reading of "naming now depends on branch order" would make `sort_up_down()` raise for
any pair with no branch-order coverage, matching `direction_of_travel()`'s existing
behavior. Not done, because it would break every synthetic-station test fixture
(`tests/test_segment.py`, `tests/test_sibling_redirect.py` build fake stations like
`"A"`/`"B"` with no real branch coverage) for no real-network benefit — branch order
already covers all 92 real segments, so the fallback path is dead code in production,
kept alive only for tests that don't need real branch coverage to make their point.

**Verification, same methodology as every step above:**

- Full test suite: 48/48 passed.
- Both import orders (`import iidsim.domain` first, `import iidsim.network` first) —
  `sort_up_down()`'s lazy `branch_order` import follows the exact pattern `Segment.new()`
  already used for the same reason (see step 4/section 3's discussion of the
  `iidsim.domain`/`iidsim.network` import cycle).
- **Structural proof zero block-section names actually changed**: saved the sorted list
  of all 177 real `block_sec.name` values after the change, `git stash`'d the change,
  saved the same list before it, `git stash pop`'d, diffed — identical. Expected, since
  step 2 already proved 100% agreement between the two orderings; this confirms that
  proof still holds after merging them.
- **`total_schedule` byte-identical before/after**, same three real corridors used
  throughout this document (`krdl_ktv`, `sprd_vzm`, `psa_ktv`).

## 6. What's still open

- The precomputed **"block section sequence per train"** idea discussed alongside this
  redesign (resolving a train's whole route to `(Segment, direction)` pairs before the
  simulation starts, so `blsec_id()` only has to resolve *which specific line* at event
  time, not *which segment/direction*) is not implemented. `Segment`/`direction_of_travel`
  are the pieces such a precomputation would be built from, but the precomputation itself
  — and the input-format questions around it (does one train's route ever cross more
  than one branch? what happens at setup time if a hop has no matching segment?) — is
  separate, unstarted work.
