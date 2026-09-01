import pandas as pd

class train():
    def __init__(self,train_id, tr_type, tr_schedule, origin, destination, max_speed, instance_index, tr_real_schedule=None):
        self.train_id = train_id #unique train ID
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
    

    def calc_train_statistics(self): #method for computing statistics at individual train level
        total_deviation = pd.Timedelta(0)
        total_earliness = pd.Timedelta(0)
        total_tardiness = pd.Timedelta(0)
        destination_tardiness = pd.Timedelta(0)
        destination_earliness = pd.Timedelta(0)
        station_count = len(self.tr_schedule)

        for station_name in self.tr_sched_act:
            deviation = self.tr_schedule[station_name][0] - self.tr_sched_act[station_name][0]
            deviation_minutes = deviation.total_seconds() / 60 # convert timedelta to minutes
            total_deviation += abs(deviation)
            total_earliness += max(pd.Timedelta(0), deviation)
            total_tardiness += max(pd.Timedelta(0), -1*deviation)
        arrival_actual = self.tr_sched_act[self.tr_destination][0]
        arrival_planned = self.tr_schedule[self.tr_destination][0]
        destination_tardiness = max(pd.Timedelta(0), arrival_actual - arrival_planned)
        destination_earliness = max(pd.Timedelta(0), arrival_planned - arrival_actual)

        avg_deviation = total_deviation/station_count
        avg_earliness = total_earliness/station_count
        avg_tardiness = total_tardiness/station_count

        return {'overall tardiness': destination_tardiness, 'overall earlyness': destination_earliness, 'Average deviation': avg_deviation, 'Average earlyness': avg_earliness, 'Average tardiness': avg_tardiness}

