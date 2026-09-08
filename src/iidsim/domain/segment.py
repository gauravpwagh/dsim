"""The station-pair segment between two adjacent stations (e.g. 'krdl_bchl') --
groups the one or more parallel physical lines (block_sec objects, e.g. dn1/up1/
mid1) that connect them, and holds the physical facts shared by all of them (the
two station endpoints in up/down terms, the distance) that today are duplicated
identically on every line object sharing that pair.

Segment is a pure grouping/addressing layer with NO mutable simulation state of
its own -- occupancy, queueing, and autoblock bookkeeping stay exclusively on the
individual line (block_sec) objects, unchanged. dn1 and up1 can be simultaneously
occupied by two different trains going opposite directions on separate physical
tracks; that must never become a segment-level fact.

Verified (not assumed) before writing this: every line sharing a base name in the
real merged network has identical stn_up/stn_down/length -- see the check run
before this file was added. If that ever stopped holding for some future board
data, Segment's __init__ raises rather than silently picking one line's values.

`Segment.new()`/`add_line()` (see docs/segment-redesign.md) go further: instead of
just *checking* that lines agree, they make disagreement structurally impossible.
Raw board data (network/boards/*.py) declares a segment's shared facts -- the two
stations, the length -- exactly once via `Segment.new(...)`, and every physical
line for that pair is then built via `.add_line(dir_mvmt, conns)`, which always
reuses that same segment's own stn_up/stn_down/length rather than taking them as
separate, independently-typo-able arguments the way the old direct
`block_sec(dir, stn_a, stn_b, length, conns, stations_list)` calls did (repeating
stn_a/stn_b/length once per line sharing a pair). __init__'s validation above is
still in place -- it's just no longer something to hope holds; for any segment
built via new()/add_line() it is unconditionally true by construction.

Identity (stn_up/stn_down) and direction-of-travel used to be two independent
orderings -- stn_west/stn_east (from station longitude, for naming) and
stn_up/stn_down (from branch order, for direction_of_travel()) -- that happened
to agree on all 92 real segments rather than being guaranteed to. Unified onto
one ordering (sort_up_down() in block_section.py: branch order primarily,
longitude fallback for a pair outside the registered network) as the final step
of docs/segment-redesign.md: stn_up/stn_down is now what a segment/line is
*called* as well as which way is "down". See sort_up_down()'s own docstring for
why the fallback still exists and when (never, for real data) it's actually used.
"""

from .block_section import block_sec, sort_up_down


class Segment:
    def __init__(self, name, lines):
        """name: the base station-pair string (e.g. 'krdl_bchl'), matching what
        ResolveMixin.conn_base() computes for this pair.
        lines: the block_sec objects sharing that base, in their original
        blocksections_list order (dn1/up1/mid1/mid2, whichever exist).
        stn_up/stn_down (station objects) and length are taken directly from
        the lines themselves (validated to agree across all of them) -- there
        is exactly one ordering now, sourced by each line's own construction
        (block_sec.stn_up/stn_down, via sort_up_down()), not a second,
        independently-suppliable one a caller could make disagree with it.
        """
        if not lines:
            raise ValueError(f"Segment({name!r}): no lines given")
        lengths = {l.length for l in lines}
        ups = {l.stn_up.name for l in lines}
        downs = {l.stn_down.name for l in lines}
        if len(lengths) > 1 or len(ups) > 1 or len(downs) > 1:
            raise ValueError(
                f"Segment({name!r}): lines disagree on endpoints/length -- "
                f"lengths={lengths} ups={ups} downs={downs}"
            )
        self.name = name
        self.stn_up = lines[0].stn_up
        self.stn_down = lines[0].stn_down
        self.length = lines[0].length
        self.lines = list(lines)

    @classmethod
    def new(cls, stn_a, stn_b, length, stations_list):
        """Declare a new segment for this station pair -- the raw-input entry
        point board/network files use exactly once per station pair, instead
        of repeating (stn_a, stn_b, length) on every individual physical
        line's block_sec(...) call the way they used to. Returns an empty
        Segment; call add_line() once per physical line this pair actually
        has (dn1, up1, mid1, ...).

        stn_a / stn_b: station *names* (str) -- order doesn't matter here any
        more than it does for conn_base(). stations_list: searched for
        stn_a/stn_b by name, same convention block_sec.__init__ itself uses.

        stn_up/stn_down are determined via sort_up_down() -- the exact same
        function block_sec.__init__ uses (via add_line() below), not a second,
        independently-written determination -- so add_line()'s resulting
        lines can never disagree with this segment about which station is
        which.
        """
        try:
            stn_a_obj = next(s for s in stations_list if s.name == stn_a)
            stn_b_obj = next(s for s in stations_list if s.name == stn_b)
        except StopIteration:
            raise ValueError(
                f"Segment.new({stn_a!r}, {stn_b!r}): one or both stations not in the supplied stations_list"
            )
        stn_up, stn_down = sort_up_down(stn_a_obj, stn_b_obj)
        seg = object.__new__(cls)
        seg.name = f'{stn_up.name}_{stn_down.name}'
        seg.stn_up = stn_up
        seg.stn_down = stn_down
        seg.length = length
        seg.lines = []
        return seg

    def add_line(self, dir_mvmt, conns):
        """Construct and register one physical line (block_sec) for this
        segment, reusing this segment's own already-fixed stn_up/stn_down/
        length instead of taking them as separate arguments the way a direct
        block_sec(...) call would -- see docs/segment-redesign.md. Returns
        the new block_sec, same as calling block_sec(...) directly would.
        """
        line = block_sec(dir_mvmt, self.stn_up.name, self.stn_down.name, self.length, conns, [self.stn_up, self.stn_down])
        self.lines.append(line)
        return line

    def direction_of_travel(self, from_stn, to_stn):
        """'dn' if travelling from_stn -> to_stn follows this segment's
        up/down order (from_stn is the up-end), 'up' if reversed. Raises if
        from_stn/to_stn aren't this segment's own two stations -- never
        guesses. from_stn/to_stn are station *names* (str); stn_up/stn_down
        are station objects, hence the .name comparisons below.
        """
        if {from_stn, to_stn} != {self.stn_up.name, self.stn_down.name}:
            raise ValueError(
                f"Segment({self.name!r}): {from_stn!r}/{to_stn!r} aren't this segment's endpoints "
                f"({self.stn_up.name!r}/{self.stn_down.name!r})"
            )
        return 'dn' if from_stn == self.stn_up.name else 'up'

    def lines_for_direction(self, direction=None):
        """Lines usable by a train travelling `direction` ('up' or 'dn'):
        same-direction lines plus bidirectional ('mid') ones -- the same filter
        blsec_id() already applies inline against a flat candidate list today.
        direction=None returns every line for this segment, unfiltered.
        """
        if direction is None:
            return list(self.lines)
        return [l for l in self.lines if l.dir_mvmt[0:2] == direction or l.dir_mvmt[0:3] == 'mid']

    def __repr__(self):
        return f"Segment({self.name!r}, lines={[l.name for l in self.lines]!r})"
