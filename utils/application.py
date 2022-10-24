from utils.function import Function

class Application(object):
    def __init__(self, app_id, app_name, app_memory, start_time, duration, cold_start_time):
        self.app_id = app_id
        self.app_name = app_name
        self.app_memory = app_memory
        self.app_start_time = start_time
        self.app_duration = duration
        self.cold_start_time = cold_start_time
        self.functions = []
    def invocation(self, func_id, func_name, func_memory, start_time, duration):
        return Function(func_id, func_name, func_memory, start_time, duration)
