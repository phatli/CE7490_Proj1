import random
from collections import defaultdict
from utils.function import Function
class Application(object):
    def __init__(self, app_id, app_name, function_dict):
        self.app_id = app_id
        self.app_name = app_name
        self.function_dict = function_dict # k-v: function id-function
        self.app_memory = sum([func.func_memory for func_id, func in self.function_dict.items()])
        
    def is_invoc(self, curr_time):
        for func in self.function_list:
            if func.is_invoc(curr_time):
                return True, func.id
        return False, None
    
    def get_func_excu_duration(self, func_id):
        return self.function_dict[func_id].func_excu_duration
        
    def __str__(self):
        return "Application: " + self.app_name + " start time: " + str(self.app_start_time) + " end time: " + str(self.app_start_time + self.app_duration)
    
    def __repr__(self):
        return self.__str__()

        

