from time import time
from collections import defaultdict
from utils.container import Container
from utils.application import Application
from utils.function import Function


class Simulator(object):
    def __init__(self,app_list, container_list, config):
        self.clock = 0
        self.app_list = app_list
        self.container_dict = self.build_container(app_list)
        self.config = config
        
    def get_clock(self):
        return self.clock
    
    def load_trace(self):
        pass
    
    def read_app_list(self):
        pass
    
        
    def build_container(self,app_list):
        container_dict = defaultdict(Application)
        for app in app_list:
            container = Container(app, app.app_id)
            container_dict[app.app_id] = container
        return container_dict
        
    def simulate(self):
        while True:
            for app in self.app_list:
                is_invoc, invoc_func_id = app.is_invoc(self.clock)
                if is_invoc:
                    container = self.container_dict[app.app_id]
                    if container.is_idle():
                         container.invoc_event(invoc_func_id)
                         idle_time = container.get_idle_time()
                         ##TODO: use idle time and histogram to calculate the prewarm window and keep alive window
                        #  pre_warm_window = xxx
                        #  cantainer.set_prewarm_window(xxx)
                        #  container.set_keep_alive_window(xxx)
            # tik tok
            self.tik_tok()
            for container in self.container_dict.values():
                container.tik_tok()
                         
    def tik_tok(self):
        time.sleep(2)
        self.clock += 1
        
        