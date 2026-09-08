# Domain model

> **File paths below reflect the pre-restructure layout.** As of the Aug 2026 package
> restructure, this content now lives under `src/iidsim/` — see
> [restructure-notes.md](restructure-notes.md) for the full old-path -> new-path mapping.
> The descriptions of *what* each piece does and *why* are still accurate; only *where*
> changed.

The physical network and rolling stock are modeled as plain Python classes. `Station` and
`block_sec`'s internal *state* is kept deliberately simple (lists/dicts as ad-hoc structs)
so the simulation engine can mutate it cheaply during the event loop — but as of
[event-manager-design.md](event-manager-design.md) stages 2-4, these classes also own real
*decisions* (which line to assign, whether a block section is ready to release a train,
queue priority, autoblock sequencing, sibling redirect), not just state. See each class's
section below for what moved.

## `trains.py` — the `train` class

Represents one scheduled train run.

```python
train(id, tr_type, tr_schedule, origin, destination, max_speed, instance_index, tr_real_schedule=None)
```

- `train_id` — e.g. `'18447'` (passenger) or `'G6'` (goods).
- `tr_type` — `'p'` (passenger) or `'g'` (goods) — drives priority rules throughout the
  simulation.
- `tr_schedule` — dict `{station: [planned_arrival, planned_departure]}`, the timetable as
  originally planned.
- `tr_sched_act` — a deep copy of `tr_schedule`, mutated in place as the simulation runs;
  despite the name ("act" = historical naming, not "actual"), this holds the **simulated**
  timetable.
- `tr_real_schedule` — optional dict of real-world recorded arrival/departure times for
  this train (used to compare simulated vs. real-world performance).
- `instance_index` — disambiguates multiple runs of the same `train_id` (e.g. up/down
  workings on different days); the simulation keys everything by
  `f'{train_id}_{instance_index}'`.
- `calc_train_statistics()` — computes per-train punctuality statistics (average/overall
  earliness, tardiness, absolute deviation) by comparing `tr_schedule` against
  `tr_sched_act`.

## `stations.py` — station objects and connections

`create_station_class(station_name, longitude, station_config)` builds a lightweight
per-station object (via a locally-defined class, one instance per call) with:

- `tracks` — dict of station lines/platforms, each entry
  `[occupied_flag, platform_number, occ_start, occ_end, cumulative_occupied_time, occupying_train_id]`.
  A `platform_number` of `0` means the line has no passenger platform (goods/loop line
  only).
- `connections` — dict of `{block_section_line_key: [status, direction, occupying_train]}`,
  filled later by `populate_connections()`, describing which block sections physically
  connect to which station line.
- Methods to set/clear track occupancy (`set_occupancy_arr`, `set_occupancy_dep`,
  `set_occupancy_updt`) and connection occupancy (`set_occ_conn_in`/`set_occ_conn_out`),
  and `is_occupied(track_name)`.
- `assign_line(train, t_ind, next_event_tr_id, len_sched, sched_act, blsec_t, prev_station,
  blsec_id_fn, conn_exists_fn)` — **decides** which of this station's tracks a just-arrived
  train should occupy (platform-required first pass for halting passenger trains, a
  relaxed fallback pass if every platformed line is occupied), and the connection key(s)
  linking it to the block section on either side. Moved here from the engine's
  `stn_line_assign` ([event-manager-design.md](event-manager-design.md) stage 2);
  `blsec_id_fn`/`conn_exists_fn` are the simulation's own bound methods, injected rather
  than duplicated since they need network-wide block-section lookups this class doesn't
  own.

`populate_connections(blocksections_list, station_dict, stations_list)` is called **once**,
after all stations and block sections for a network are built, to wire each station's
`connections` dict from the block sections that touch it. Every `*_data.py` board file
relies on this shared function instead of duplicating the wiring logic.

## `blocksections.py` — the `block_sec` class

A block section is the track segment between two adjacent stations that only one train
(or a queued sequence of trains) can occupy at a time.

```python
block_sec(dir, stn_start, stn_end, length, conns, stations_list)
```

- `dir_mvmt` — `'dn'` (west→east), `'up'` (east→west), or `'mid'` (bidirectional, single
  physical line shared by both directions) — each combined with an instance suffix, e.g.
  `dn1`, `up1`, `mid1`, `mid2` (for station pairs with more than one parallel physical
  line).
- Naming convention: `STNWEST_STNEAST_DIRSUFFIX`, where west/east is decided by comparing
  station `longitude` (lower = west). E.g. `'krdl_bchl_dn1'`. This is a naming/key
  convention only, as of [segment-redesign.md](segment-redesign.md) — the engine no
  longer uses longitude to decide which way a train is actually travelling; see
  `Segment` below.
- `occ_ind` / `occ_start` / `occ_end` / `occ_train` — current occupancy state; `2100-06-01`
  sentinel timestamps mean "not currently set".
- `blsec_queue` — a flat list of trains waiting for this section, stored as repeating
  6-element groups `[event_tr_id, train_id, tr_type, schedule_index, occ_start, occ_end]`.
- `autoblsec_list` / `autoblsec_queue` — separate bookkeeping used for **autoblock**
  sections (see below), where occupancy isn't binary but based on maintaining a minimum
  time/distance gap between successive trains.
- `train_occ_start/_end/_updt`, `queue_add/_remove/_updt`, and the autoblock equivalents
  mutate this state as the event loop processes arrivals/departures.
- Four decision methods moved here from the engine
  ([event-manager-design.md](event-manager-design.md) stages 3-4), each taking whatever
  external collaborators it needs (train, station, other bound methods) as explicit
  parameters rather than reading ambient simulation state:
  - `ready_to_depart(...)` — the single/double-line departure-readiness check (pure
    read-only, no state mutated).
  - `update_queue_priority(...)` — reorders `blsec_queue` so passenger trains precede
    goods trains, shifting the bumped goods trains' schedules/occupancy accordingly.
  - `process_autoblock_departure(...)` — autoblock (moving-block signalling) sequencing:
    whether a train can depart onto this section now or must wait for headway/
    safe-distance clearance behind the last train through.
  - `find_free_sibling(blsec_lookup, ...)` — a free parallel section (same station pair,
    different direction suffix) this train could redirect onto if `self` is occupied or
    queued.

## `segment.py` — the `Segment` class

A `Segment` is the station-pair track segment itself — as opposed to `block_sec`, which
is one specific physical *line* on that segment (`dn1`, `up1`, or a shared `mid1`/
`mid2`). Added in [segment-redesign.md](segment-redesign.md) to give the station-pair
grouping (previously only an implicit naming convention, then an anonymous engine-level
index, `blsec_by_pair`) a real, named identity.

```python
Segment(name, lines, stn_up=None, stn_down=None)
```

- `name` — the base station-pair string (e.g. `'krdl_bchl'`), matching what
  `ResolveMixin.conn_base()` computes for that pair.
- `lines` — the `block_sec` objects sharing that base, in `blocksections_list` order.
- `stn_west` / `stn_east` / `length` — physical facts common to every line on this
  segment (verified identical across lines before trusting them), taken from the lines
  rather than recomputed.
- `stn_up` / `stn_down` — this segment's endpoints in **branch-order** terms: `stn_up` is
  the one closer to the reference ("headquarters") end of whichever branch this pair
  belongs to, from `network.routes.branch_order()`. Deliberately independent of
  `stn_west`/`stn_east` above, which are longitude-derived and carry no up/down meaning
  of their own. `None`/`None` if no branch covers this pair (doesn't happen for any of
  the 92 real segments today, but `direction_of_travel()` refuses to guess rather than
  raising here).
- `direction_of_travel(from_stn, to_stn)` — `'dn'` if travelling `from_stn -> to_stn`
  matches this segment's branch order, `'up'` if reversed; raises if the order is unknown
  or the two stations aren't this segment's own endpoints.
- `lines_for_direction(direction)` — this segment's lines compatible with `direction`
  (same-direction lines plus bidirectional `mid*` ones).

**Owns no mutable simulation state.** Occupancy and queueing (`occ_ind`, `blsec_queue`,
`autoblsec_list`, ...) stay entirely on the `block_sec` line objects — `dn1` and `up1`
can be simultaneously occupied by two different trains, which is the entire reason
double-track sections exist, so that can never become a segment-level fact. `Segment` is
built once per run (`SimulationState.segments_by_pair`), alongside the pre-existing
`blsec_by_pair` index it wraps.

`Simulation.direction_of_travel(stn_a, stn_b)` (`engine/resolve.py`) is the engine-facing
entry point most code actually calls — it looks up the right `Segment` via `conn_base()`
and delegates. This replaced 10 separate `station_longitudes[...]` comparisons across
`resolve.py`/`priority.py`/`run.py`; see
[segment-redesign.md](segment-redesign.md) for the full list and how it was verified.

## `network/` — assembling the physical graph

The network is authored as three independent "boards" (line segments), each with its own
`*_stations_data.py` (station objects + track dict) and `*_blocksections_data.py`
(`block_sec` objects connecting them):

- `krdl_vzm_stations_data.py` / `krdl_vzm_blocksections_data.py` — 55 stations, KRDL to
  VZM main line via KRPU.
- `krpu_ktv_stations_data.py` / `krpu_ktv_blocksections_data.py` — 19 stations, KRPU to
  KTV (the OEC line).
- `psa_scmn_stations_data.py` / `psa_scmn_blocksections_data.py` — 19 stations, PUN
  through VZM/KTV down to the port-area stations at SCMN.

`network/__init__.py` merges the three boards into one graph:

1. Merges each board's `station_dict` and de-duplicates `stations_list` by station name
   (junction stations like `ktv`, `vzm`, `krpu` appear in more than one board).
2. Concatenates all boards' `blocksections_list`s.
3. Manually adds the **inter-board link sections** that couldn't be built inside a single
   board because the far-end station lived in a different board: `mvw↔ktv` and
   `gtlm↔vzm` (each `dn1`/`up1`, built directly with `block_sec(...)`).
4. Calls `populate_connections(...)` once over the fully merged network so junction
   stations pick up cross-board connections too.

`network/list_stations_in_order.py` is a **reference/scratch file** — human-readable
ordered station-code lists per board/segment used while authoring the data files. It's not
imported anywhere except in a comment, and some of its list definitions
(`krdl_vzm_single_line_blsec`, etc.) reference block-section variable names that aren't
defined in that file, confirming it isn't meant to be executed as a module.

## `routes.py` (formerly described as `station_routes.py`)

Defines named station-code lists for each physical line segment (`KRDL_TO_KRPU`,
`KRPU_TO_KTV`, `SPRD_TO_VZM`, `VZM_TO_PSA`, etc., head-of-list = a branch's reference
end) and composes them into full origin→destination routes (`KRDL_KTV`, `VZM_PSA`,
`SPRD_KTV`, ...), each with its reverse automatically generated. All of these are
collected into one lookup dict, `BRANCH_LISTS['ORIGIN_DEST'] → [station codes in travel
order]` — a route-lookup utility for whatever code needs "the ordered station list
between A and B," a simpler, independent representation from the block-section graph in
`network/`.

**As of [segment-redesign.md](segment-redesign.md), these per-branch lists are also
load-bearing**, not just unused reference data: `BASE_SEGMENTS` (the 8 base lists,
collected into a registry) and `branch_order()` derive every `Segment`'s `stn_up`/
`stn_down` from them — the real source of the engine's travel-direction convention, now
that it no longer uses longitude for that purpose. `BRANCH_LISTS` itself (the composed,
full-route dict) remains unused by any other code.
