import random
class Function(object):
    def __init__(self, func_id, func_name, function_memory, invoc_schedule, duration):
        self.func_id = func_id
        self.func_name = func_name
        self.func_mem = function_memory
        self.func_excu_duration = duration
        self.invoc_schedule = invoc_schedule
        
    def is_invoc(self, curr_time):
        if curr_time in self.invoc_schedule:
            return True
        else:
            return False
    
    def __str__(self):
        return "Function: " + self.func_name + " start time: " + str(self.func_start_time) + " end time: " + str(self.func_start_time + self.func_duration)
    
    def __repr__(self):
        return self.__str__()

        