import pandas as pd

# VR: convention here is that block section name is always station-to-the-west_station-to-east _ direction-mvmnt+instancenum
# VR: for example, 'STNWEST_STNEAST_DN1' OR 'STNWEST_STNEAST_UP1' OR 'STNWEST_STNEAST_MID1'
# VR: west / east is identified by the longitude attribute of the station
# NOTE: stations_list is now passed in by the caller (no module-level import).
# Each *_data.py file owns its own station list and supplies it on construction,
# so production and test setups can coexist in the same Python session.
class block_sec():
    def __init__(self, dir, stn_start, stn_end, length, conns, stations_list):
        self.dir_mvmt = dir   # 'dn' = W->E, 'up' = E->W, 'mid' = bidirectional
        self.occ_ind = 0      # 0 if free, 1 if occupied

        stn1_obj = stn2_obj = None
        for j in stations_list:
            if   j.name == stn_start: stn1_obj = j
            elif j.name == stn_end:   stn2_obj = j
        if stn1_obj is None or stn2_obj is None:
            raise ValueError(
                f"block_sec({stn_start!r}, {stn_end!r}): one or both stations "
                f"not in the supplied stations_list"
            )

        # west = strictly lower longitude (defensive '>' instead of '>=':
        # equal longitudes among adjacent stations would indicate a data issue,
        # better to surface it than silently pick a side)
        if stn2_obj.longitude > stn1_obj.longitude:
            self.name = stn1_obj.name + '_' + stn2_obj.name + '_' + self.dir_mvmt
            self.stn_west, self.stn_east = stn1_obj, stn2_obj
        else: 
            self.name = stn2_obj.name + '_' + stn1_obj.name + '_' + self.dir_mvmt
            self.stn_west, self.stn_east = stn2_obj, stn1_obj

        self.stn_conns = {self.stn_west.name: [], self.stn_east.name: []}
        for k in conns[self.stn_west.name]:
            self.stn_conns[self.stn_west.name].append(self.name + '_' + k)
        for l in conns[self.stn_east.name]:
            self.stn_conns[self.stn_east.name].append(self.name + '_' + l)

        self.length = length
        self.occ_cum = 0.0  # cumulative occupancy in seconds (float avoids pd.Timedelta overflow)
        self.occ_start = pd.Timestamp("2100-06-01 22:50:00")
        self.occ_end = pd.Timestamp("2100-06-01 22:52:00")
        self.occ_train = ''
        self.blsec_queue = []  # 'next_event_tr_id', 'train_id', start/end times, etc.
        self.autoblsec_list = []
        self.autoblsec_queue = []

    def train_occ_start(self, occ_start, occ_end, train_name):
        self.occ_ind = 1
        self.occ_start = occ_start
        self.occ_end = occ_end
        self.occ_train = train_name

    def train_occ_end(self, t):
        self.occ_ind = 0
        sentinel = pd.Timestamp("2100-06-01 22:50:00")
        if self.occ_start < sentinel:
            self.occ_cum += (max(t, self.occ_end) - self.occ_start).total_seconds()
        self.occ_train = ''
        self.occ_start = pd.Timestamp("2100-06-01 22:50:00")
        self.occ_end = pd.Timestamp("2100-06-01 22:52:00")

    # useful when none of the station line is free; update occ_end time of the
    # blocksection accordingly and status.
    def train_occ_updt(self, occ_end, occ_status):
        self.occ_end = occ_end
        self.occ_ind = occ_status

    # when blocksection is occupied, add the train details to the queue list
    def queue_add(self, next_event_tr_id, next_event_train, tr_type, tr_index, occ_start, occ_end):
        self.blsec_queue.append(next_event_tr_id)
        self.blsec_queue.append(next_event_train)
        self.blsec_queue.append(tr_type)
        self.blsec_queue.append(tr_index)
        self.blsec_queue.append(occ_start)
        self.blsec_queue.append(occ_end)

    def queue_remove(self, dep_list):
        """Remove a complete 6-element train block from queue"""
        train_id_to_remove = dep_list[0]
        for i in range(0, len(self.blsec_queue), 6):
            if i < len(self.blsec_queue) and self.blsec_queue[i] == train_id_to_remove:
                del self.blsec_queue[i:i+6]
                return

    def queue_updt(self, new_occ_inc):
        for idx, j in enumerate(self.blsec_queue):
            if isinstance(j, pd.Timestamp):
                self.blsec_queue[idx] = j + new_occ_inc

    # autoblock-section helpers
    def autoblsecsection_trains(self, train):
        self.autoblsec_list.append(train)

    def autoblsecsection_trains_remove(self):
        self.autoblsec_list.pop(0)

    def autoblsecsection_trains_updt(self, new_occ_inc):
        for idx, j in enumerate(self.autoblsec_list):
            for i in range(3, len(j)):
                self.autoblsec_list[idx][i] = j[i] + new_occ_inc

    def ready_to_depart(self, count_curr_blsec, count_next_blsec, free_stn_lines, same_dir_stn_count, next_blsec_list, current_train_dir):
        """Whether a train waiting at the station may depart onto this block section
        right now, given single/double-line occupancy of this section and the
        candidate next one(s). Stage 3a of docs/event-manager-design.md -- translated
        line-for-line (not redesigned) from resource_update_event()'s departure branch
        in run.py: a pure read-only decision with no side effects on any object, which
        is what makes it a safe first piece of stage 3 to move (unlike the
        queue-priority-release and autoblock-sequencing logic, which mutate Station/
        Train/BlockSection state inline and are moved separately).

        count_curr_blsec / count_next_blsec: how many parallel lines (dn1/up1/mid1)
        exist for this section / the next one -- 1 means single line.
        next_blsec_list: [(block_sec, direction), ...] for the section(s) beyond the
        next station.
        """
        curr_is_single = count_curr_blsec == 1
        next_is_single = count_next_blsec == 1
        ready_to_dept = True
        if curr_is_single and next_is_single:
            print('both current and next block sections are single line')
            if free_stn_lines >= 2:
                ready_to_dept = True
            elif free_stn_lines == 1:
                print('one stn line is free block')
                blsec_obj, blsec_dir = next_blsec_list[0]
                print('next block section occupancy status is ', next_blsec_list[0])
                print('dir and block is', blsec_dir, current_train_dir, blsec_obj.occ_ind)
                if blsec_obj.occ_ind == 0:
                    ready_to_dept = True
                elif blsec_dir == current_train_dir and blsec_obj.occ_ind == 1:
                    ready_to_dept = True
                else:
                    ready_to_dept = False
            elif free_stn_lines == 0:
                if same_dir_stn_count == 0:
                    ready_to_dept = False
                else:
                    blsec_obj, blsec_dir = next_blsec_list[0]
                    if blsec_obj.occ_ind == 0:
                        ready_to_dept = True
                    elif blsec_dir == current_train_dir:
                        ready_to_dept = True
                    else:
                        ready_to_dept = False
        elif curr_is_single and (not next_is_single):
            print('current block section is single line and next block section is double line')
            if free_stn_lines >= 2:
                ready_to_dept = True
            elif free_stn_lines == 1:
                free_blsec_count = sum((1 for b in next_blsec_list if b[0].occ_ind == 0))
                same_dir_blsec_count = sum((1 for b in next_blsec_list if b[1] == current_train_dir))
                if free_blsec_count == len(next_blsec_list):
                    ready_to_dept = True
                elif free_blsec_count >= 1 and same_dir_stn_count >= 1:
                    ready_to_dept = True
                elif same_dir_blsec_count >= 1:
                    ready_to_dept = True
                else:
                    print('the only free station line is occupied by an oncoming train and both lines of the next block section are occupied by oncoming trains, so we need to wait at the station')
                    ready_to_dept = False
            elif free_stn_lines == 0 and same_dir_stn_count == 0:
                print('all station lines are occupied by opposing trains, so we need to wait at the station')
                ready_to_dept = False
            elif free_stn_lines == 0 and same_dir_stn_count >= 1:
                same_dir_blsec_count = sum((1 for b in next_blsec_list if b[1] == current_train_dir))
                if same_dir_blsec_count >= 1:
                    ready_to_dept = True
                else:
                    print('all station lines are occupied by opposing trains, but at least one train has same direction as given train and both lines of the next block section are occupied by oncoming trains, so we need to wait at the station')
                    ready_to_dept = False
        elif not curr_is_single and next_is_single:
            print('current block section is double line and next block section is single line')
            if free_stn_lines >= 2:
                ready_to_dept = True
            elif free_stn_lines == 1:
                blsec_obj, blsec_dir = next_blsec_list[0]
                if blsec_obj.occ_ind == 0:
                    ready_to_dept = True
                elif blsec_dir == current_train_dir:
                    ready_to_dept = True
                else:
                    print('the only free station line is occupied by an oncoming train and the next block section is single line occupied by an oncoming train, so we need to wait at the station')
                    ready_to_dept = False
            elif free_stn_lines == 0:
                if same_dir_stn_count == 0:
                    print('all station lines are occupied by opposing trains, so we need to wait at the station')
                    ready_to_dept = False
                else:
                    blsec_obj, blsec_dir = next_blsec_list[0]
                    if blsec_obj.occ_ind == 0:
                        ready_to_dept = True
                    elif blsec_dir == current_train_dir:
                        ready_to_dept = True
                    else:
                        print('the only free station line is occupied by an oncoming train and the next block section is single line occupied by an oncoming train, so we need to wait at the station')
                        ready_to_dept = False
        elif ready_to_dept is False:
            pass  # unreachable given ready_to_dept starts True and no prior branch
            # in this if/elif chain can set it False before this point is reached --
            # preserved exactly as in the original rather than "fixed," since this is a
            # translation, not a behavior change. The final `else` below is what
            # actually handles the double/double (not curr_is_single, not next_is_single)
            # case, via the same latent fallthrough the original had.
        else:
            ready_to_dept = True
            print('single line block section case is not found ready to depart True')
        return ready_to_dept
