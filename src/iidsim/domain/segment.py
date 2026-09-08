"""The station-pair segment between two adjacent stations (e.g. 'krdl_bchl') --
groups the one or more parallel physical lines (block_sec objects, e.g. dn1/up1/
mid1) that connect them, and holds the physical facts shared by all of them (the
two station endpoints, the distance) that today are duplicated identically on
every line object sharing that pair.

Segment is a pure grouping/addressing layer with NO mutable simulation state of
its own -- occupancy, queueing, and autoblock bookkeeping stay exclusively on the
individual line (block_sec) objects, unchanged. dn1 and up1 can be simultaneously
occupied by two different trains going opposite directions on separate physical
tracks; that must never become a segment-level fact.

Verified (not assumed) before writing this: every line sharing a base name in the
real merged network has identical stn_west/stn_east/length -- see the check run
before this file was added. If that ever stopped holding for some future board
data, Segment's __init__ raises rather than silently picking one line's values.

`Segment.new()`/`add_line()` (see docs/segment-redesign.md) go further: instead of
just *checking* that lines agree, they make disagreement structurally impossible.
Raw board data (network/boards/*.py) declares a segment's shared facts -- the two
stations, the length -- exactly once via `Segment.new(...)`, and every physical
line for that pair is then built via `.add_line(dir_mvmt, conns)`, which always
reuses that same segment's own stn_west/stn_east/length rather than taking them as
separate, independently-typo-able arguments the way the old direct
`block_sec(dir, stn_a, stn_b, length, conns, stations_list)` calls did (repeating
stn_a/stn_b/length once per line sharing a pair). __init__'s validation above is
still in place -- it's just no longer something to hope holds; for any segment
built via new()/add_line() it is unconditionally true by construction.
"""

from .block_section import block_sec, sort_west_east
# iidsim.network.routes.branch_order is imported lazily, inside new() below, not
# here at module level -- see new()'s docstring for why.


class Segment:
    def __init__(self, name, lines, stn_up=None, stn_down=None):
        """name: the base station-pair string (e.g. 'krdl_bchl'), matching what
        ResolveMixin.conn_base() computes for this pair.
        lines: the block_sec objects sharing that base, in their original
        blocksections_list order (dn1/up1/mid1/mid2, whichever exist).
        stn_up / stn_down: this segment's endpoint station *names* (str) in
        branch-order terms -- stn_up is the one closer to the reference
        ("headquarters") end, per iidsim.network.routes.branch_order().
        Deliberately independent of stn_west/stn_east below, which are
        longitude-derived and carry no up/down meaning. None/None if this pair
        isn't covered by any known branch order -- direction_of_travel() raises
        rather than guessing in that case.
        """
        if not lines:
            raise ValueError(f"Segment({name!r}): no lines given")
        lengths = {l.length for l in lines}
        wests = {l.stn_west.name for l in lines}
        easts = {l.stn_east.name for l in lines}
        if len(lengths) > 1 or len(wests) > 1 or len(easts) > 1:
            raise ValueError(
                f"Segment({name!r}): lines disagree on endpoints/length -- "
                f"lengths={lengths} wests={wests} easts={easts}"
            )
        west_name, east_name = next(iter(wests)), next(iter(easts))
        if (stn_up is None) != (stn_down is None):
            raise ValueError(f"Segment({name!r}): stn_up and stn_down must be given together or not at all")
        if stn_up is not None and {stn_up, stn_down} != {west_name, east_name}:
            raise ValueError(
                f"Segment({name!r}): stn_up/stn_down ({stn_up!r}/{stn_down!r}) "
                f"aren't this segment's own two stations ({west_name!r}/{east_name!r})"
            )
        self.name = name
        self.stn_west = lines[0].stn_west
        self.stn_east = lines[0].stn_east
        self.length = lines[0].length
        self.lines = list(lines)
        self.stn_up = stn_up
        self.stn_down = stn_down

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

        West/east are determined via sort_west_east() -- the exact same
        function (and tie-break) block_sec.__init__ uses, not a second,
        independently-written comparison -- so add_line()'s resulting lines
        can never disagree with this segment about which station is which,
        even in the edge case of two adjacent stations sharing a longitude.

        branch_order() is imported here, lazily, rather than at module level:
        iidsim.network's own __init__.py imports Segment from iidsim.domain (to
        call new()/add_line() while building the network), so a module-level
        `from iidsim.network.routes import branch_order` here would make
        iidsim.domain and iidsim.network import each other -- fine if
        iidsim.network happens to be imported first (its own __init__.py
        importing iidsim.domain then completes iidsim.domain's init in full
        before returning), but a real ImportError if iidsim.domain is imported
        first (iidsim.network's own from iidsim.domain import ... then hits
        iidsim.domain mid-initialization, before Segment is defined). Deferring
        the import to here avoids the module-level half of that cycle entirely:
        by the time new() is actually called, it's always from within a board
        file, which is always reached via iidsim.network's own __init__.py --
        so iidsim.network is already present in sys.modules (if partially
        initialized) by then, and this import just pulls in the leaf routes
        submodule rather than re-triggering a fresh package init.
        """
        from iidsim.network.routes import branch_order
        try:
            stn_a_obj = next(s for s in stations_list if s.name == stn_a)
            stn_b_obj = next(s for s in stations_list if s.name == stn_b)
        except StopIteration:
            raise ValueError(
                f"Segment.new({stn_a!r}, {stn_b!r}): one or both stations not in the supplied stations_list"
            )
        stn_west, stn_east = sort_west_east(stn_a_obj, stn_b_obj)
        name = f'{stn_west.name}_{stn_east.name}'
        up_down = branch_order().get(frozenset((stn_west.name, stn_east.name)))
        stn_up, stn_down = up_down if up_down is not None else (None, None)
        seg = object.__new__(cls)
        seg.name = name
        seg.stn_west = stn_west
        seg.stn_east = stn_east
        seg.length = length
        seg.lines = []
        seg.stn_up = stn_up
        seg.stn_down = stn_down
        return seg

    def add_line(self, dir_mvmt, conns):
        """Construct and register one physical line (block_sec) for this
        segment, reusing this segment's own already-fixed stn_west/stn_east/
        length instead of taking them as separate arguments the way a direct
        block_sec(...) call would -- see docs/segment-redesign.md. Returns
        the new block_sec, same as calling block_sec(...) directly would.
        """
        line = block_sec(dir_mvmt, self.stn_west.name, self.stn_east.name, self.length, conns, [self.stn_west, self.stn_east])
        self.lines.append(line)
        return line

    def direction_of_travel(self, from_stn, to_stn):
        """'dn' if travelling from_stn -> to_stn follows this segment's
        branch-order (from_stn is the up-end), 'up' if reversed. Raises if this
        segment's up/down endpoints are unknown, or if from_stn/to_stn aren't
        this segment's own two stations -- never guesses.
        """
        if self.stn_up is None:
            raise ValueError(f"Segment({self.name!r}): no known branch order for this pair")
        if {from_stn, to_stn} != {self.stn_up, self.stn_down}:
            raise ValueError(
                f"Segment({self.name!r}): {from_stn!r}/{to_stn!r} aren't this segment's endpoints "
                f"({self.stn_up!r}/{self.stn_down!r})"
            )
        return 'dn' if from_stn == self.stn_up else 'up'

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
