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
"""


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
