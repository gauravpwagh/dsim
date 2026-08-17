import pandas as pd

class train():
    def __init__(self,id, tr_type, tr_schedule, origin, destination, max_speed, instance_index, tr_real_schedule=None):
        self.train_id = id #unique train ID
        #self.train_dir = dir #direction of movement: 0 for down, 1 for up
        self.tr_type = tr_type #'p' for passenger, 'g' for goods
        self.tr_schedule = tr_schedule # dictionary
        self.tr_origin = origin #origin station
        self.tr_destination = destination #destination station
        # self.tr_sched_act holds the simulated timetable, updated during the simulation run (name is historical, not real-world "actual" data)
        # a structural copy (not copy.deepcopy) is enough and considerably cheaper: the
        # leaf values are pandas Timestamps, which are immutable, so there's nothing
        # under them that a shallow-per-level rebuild would fail to isolate.
        self.tr_sched_act = {station: list(times) for station, times in self.tr_schedule.items()}
        self.tr_real_schedule = tr_real_schedule if tr_real_schedule is not None else {} # real-world recorded arrival/departure times, sourced from movement data
        self.max_speed = max_speed
        self.instance_index = instance_index
    

    def calc_tr_stats(self): #method for computing statistics at individual train level
        dev_sched = pd.Timedelta(0) 
        earlyness = pd.Timedelta(0) 
        tardiness = pd.Timedelta(0) 
        sched_tardiness = pd.Timedelta(0)  
        sched_earlyness = pd.Timedelta(0) 
        n_sched = len(self.tr_schedule) 

        for j in self.tr_sched_act: 
            dev = self.tr_schedule[j][0] - self.tr_sched_act[j][0]
            dev_minutes = dev.total_seconds() / 60 # convert timedelta to minutes 
            dev_sched += abs(dev) 
            earlyness += max(pd.Timedelta(0), dev)
            tardiness += max(pd.Timedelta(0), -1*dev)
        arrival_actual = self.tr_sched_act[self.tr_destination][0]
        arrival_planned = self.tr_schedule[self.tr_destination][0]
        sched_tardiness = max(pd.Timedelta(0), arrival_actual - arrival_planned)
        sched_earlyness = max(pd.Timedelta(0), arrival_planned - arrival_actual)
        
        avg_dev_sched = dev_sched/n_sched
        avg_earlyness = earlyness/n_sched 
        avg_tardiness = tardiness/n_sched

        return {'overall tardiness': sched_tardiness, 'overall earlyness': sched_earlyness, 'Average deviation': avg_dev_sched, 'Average earlyness': avg_earlyness, 'Average tardiness': avg_tardiness}

