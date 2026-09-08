# Segment redesign — design doc

> **Status: done.** All three steps below are implemented and verified. This document
> records the design discussion and verification, the same way
> [event-manager-design.md](event-manager-design.md) does for that (larger, earlier)
> redesign.

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
- `conn_base()`'s own internal west/east sort, and `block_sec.__init__`'s naming sort —
  deliberately **not** touched. Both are canonical *key/naming* conventions (what a
  segment or block section is called), not travel-direction decisions, and `Segment`'s
  own construction depends on that naming already existing — changing it would be
  circular, and a much larger, unrelated blast radius than what this redesign is about.

## 3. The three steps

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

Built once per run in `SimulationState.__init__`, as `self.segments_by_pair`, alongside
the existing `self.blsec_by_pair`.

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

## 4. Verification

- **Adjacency assumption checked directly**: `direction_of_travel()` requires its two
  stations to be adjacent (share a real `Segment`). Verified for every consecutive
  station pair in every train's own schedule, across every dataset in
  `iidsim.schedules` — zero mismatches, so no `KeyError` risk in practice.
- **Full test suite** after every step (34/34 at completion, including
  `tests/test_segment.py` and the byte-identical golden Excel comparison).
- **Manual before/after diffs** (`git stash` the step's change, run, `git stash pop`, run
  again, compare) of the complete pickled `total_schedule`, on real multi-day corridors
  not covered by the golden test — `krdl_ktv` after step 1, `krdl_ktv` again after step
  2, and `krdl_ktv` / `sprd_vzm` / `ktv_psa` after step 3 (the riskiest step, given three
  real corridors). Byte-identical every time.

## 5. What's still open

- **`blsec_id()`, `outgoing_blsec_name()`, and `check_next_blse_stn_occupancy()` still
  build their candidate lists by hand** (`self.blsec_by_pair.get(base, [])` plus an
  inline direction filter) rather than calling `Segment.lines_for_direction()`, even
  though that method exists specifically to replace that pattern. Consolidating those
  three call sites onto it is a natural next step, lower-risk than step 3 (pure
  candidate-list construction, not direction determination), not done here because it
  wasn't asked for as part of this pass.
- The precomputed **"block section sequence per train"** idea discussed alongside this
  redesign (resolving a train's whole route to `(Segment, direction)` pairs before the
  simulation starts, so `blsec_id()` only has to resolve *which specific line* at event
  time, not *which segment/direction*) is not implemented. `Segment`/`direction_of_travel`
  are the pieces such a precomputation would be built from, but the precomputation itself
  — and the input-format questions around it (does one train's route ever cross more
  than one branch? what happens at setup time if a hop has no matching segment?) — is
  separate, unstarted work.
