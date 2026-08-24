"""Stages 0-1 of docs/event-manager-design.md: a lazy-deletion min-heap replacing
build_event_list() + the linear min-scan in Simulation.run() (events.py / run.py),
plus an O(1) staleness-check cache (stage 1) so a pop never has to rescan a train's
schedule. resource_update_event() itself is untouched -- this only changes HOW the
next event is picked, not what happens once it's picked.

use_event_manager=True is the Simulation()/run_simulation() default; pass False for
the original build_event_list() path if ever needed. See tests/test_event_manager.py
for the side-by-side verification this was checked against before being trusted.
"""
import heapq

import pandas as pd

SENTINEL = pd.Timestamp('2100-06-01 22:50:00')


class EventManager:
    """Owns the heap and the push/pop/staleness logic. Knows nothing about platform
    assignment, priority rules, or queue internals -- it only ever asks "what is this
    train's current earliest pending (time, type)," mirroring build_event_list()'s
    per-train scan (events.py:18) but for one train at a time instead of all of them.
    """

    def __init__(self, sched_act, train_ids):
        """sched_act: Simulation's self.sched_act dict (flat per-train schedule lists,
        mutated in place elsewhere in the engine -- this class reads it, never owns it).
        train_ids: train-instance-ids in a fixed order, becoming the heap tie-break key
        -- reproduces today's "first train in dict/build order wins on an exact-timestamp
        tie" behavior exactly, since Python heap/tuple comparison falls through to this
        key whenever two trains' times are equal.
        """
        self._sched_act = sched_act
        self._order_index = {tr_id: i for i, tr_id in enumerate(train_ids)}
        self._heap = []
        # Stage 1: the last (time, type) known to be current for each train, kept in
        # sync by _push_current() -- every call site that can change a train's
        # schedule already calls notify_updated() for it (see run.py's
        # refresh_candidates, verified exhaustively against every self.sched_updt()
        # call site), so this dict is always accurate between events, not just
        # "usually right." Lets pop_next() validate a popped entry with an O(1)
        # lookup instead of rescanning that train's whole schedule -- see
        # docs/event-manager-design.md section 5 for why this matters on long
        # (multi-day) simulation horizons.
        self._current = {}
        for tr_id in train_ids:
            self._push_current(tr_id)

    def next_pending(self, tr_id):
        """(time, type) of tr_id's earliest still-pending event, or None if that train's
        schedule is fully consumed (every entry sentineled). type is 'a' (arrival) if the
        entry immediately before the timestamp in the flat schedule is a station-name
        string, else 'd' (departure) -- same inference build_event_list() uses."""
        sched = self._sched_act[tr_id]
        pending = [v for v in sched if not isinstance(v, str) and v < SENTINEL]
        if not pending:
            return None
        t = min(pending)
        idx = sched.index(t)
        event_type = 'a' if isinstance(sched[idx - 1], str) else 'd'
        return (t, event_type)

    def _push_current(self, tr_id):
        pending = self.next_pending(tr_id)
        self._current[tr_id] = pending
        if pending is not None:
            t, event_type = pending
            heapq.heappush(self._heap, (t, self._order_index[tr_id], tr_id, event_type))

    def notify_updated(self, tr_id):
        """Call after anything that may have revised tr_id's schedule. Pushes a fresh
        entry; any earlier entry for this train already in the heap is left in place to
        go stale and be discarded (lazy deletion -- see docs/event-manager-design.md
        section 4) rather than searched-for and removed."""
        self._push_current(tr_id)

    def pop_next(self):
        """Pop and return (time, type, train_id) for the next event, silently discarding
        any stale entries along the way. Returns None once every train's schedule is
        exhausted (mirrors run()'s loop-termination expectations: callers should treat
        None the same as build_event_list() returning nothing selectable)."""
        while self._heap:
            t, _, tr_id, event_type = heapq.heappop(self._heap)
            if self._current.get(tr_id) == (t, event_type):
                return (t, event_type, tr_id)
        return None
