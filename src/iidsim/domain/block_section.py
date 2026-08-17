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
