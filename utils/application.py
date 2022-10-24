import random
from utils.function import Function

# class Application(object):
#     def __init__(self, app_id, app_name, app_memory, start_time, duration, cold_start_time):
#         self.app_id = app_id
#         self.app_name = app_name
#         self.app_memory = app_memory
#         self.app_start_time = start_time
#         self.app_duration = duration
#         self.cold_start_time = cold_start_time
#         self.functions = []
#         func = Function(func_id, func_name, func_memory, start_time, duration)
#         self.functions.append(func)
#     def next_invocation(self):
#         return self.functions[0].calculate_next_invocation(self.app_start_time)
class Application(object):
    def __init__(self, app_id, app_name, app_memory, start_time, cold_start_time, duration, function_list):
        self.app_id = app_id
        self.app_name = app_name
        self.app_memory = app_memory
        self.app_start_time = start_time
        self.app_duration = duration
        self.cold_start_time = cold_start_time
        self.function_list = function_list
        
    def next_invocation(self):
        next_invoc_time = self.function_list[0].calculate_next_invocation(self.app_start_time)
        return next_invoc_time
    
    def invocation_queue(self, curr_time):
        invocation_queue = []
        for func in self.function_list:
            invocation_queue.append(func.calculate_next_invocation(curr_time))
        return invocation_queue
    
    def working(self):
        print("Application: " + self.app_name + " is working")
        
    def __str__(self):
        return "Application: " + self.app_name + " start time: " + str(self.app_start_time) + " end time: " + str(self.app_start_time + self.app_duration)
    
    def __repr__(self):
        return self.__str__()

        

