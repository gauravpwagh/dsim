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
    def __init__(self, name, lines):
        """name: the base station-pair string (e.g. 'krdl_bchl'), matching what
        ResolveMixin.conn_base() computes for this pair.
        lines: the block_sec objects sharing that base, in their original
        blocksections_list order (dn1/up1/mid1/mid2, whichever exist).
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
        self.name = name
        self.stn_west = lines[0].stn_west
        self.stn_east = lines[0].stn_east
        self.length = lines[0].length
        self.lines = list(lines)

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
