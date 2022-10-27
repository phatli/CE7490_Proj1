import random
class Function(object):
    def __init__(self, func_id, func_name, start_time, duration):
        self.func_id = func_id
        self.func_name = func_name
        self.func_start_time = start_time
        self.func_duration = duration
    def calculate_next_invocation(self, curr_time):
        idle_time = random.randint(0, 100)
        return curr_time + idle_time
    def calculate_end_time(self):
        return self.func_start_time + self.func_duration
    def __str__(self):
        return "Function: " + self.func_name + " start time: " + str(self.func_start_time) + " end time: " + str(self.func_start_time + self.func_duration)
    def __repr__(self):
        return self.__str__()

        