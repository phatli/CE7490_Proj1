from time import time
from collections import defaultdict
from utils.container import Container
from utils.application import Application
from utils.function import Function
from utils.hybrid_histogram_policy_worker import HybridHistogramPolicyWorker
from utils.fix_keep_alive_policy_worker import FixKeepAlivePolicyWorker

class Simulator(object):
    def __init__(self,app_list, config):
        self.clock = 0
        self.app_list = app_list
        self.container_dict = self.build_container(app_list)
        self.config = config
        
    def get_clock(self):
        return self.clock
    
    def load_trace(self):
        #TODO: trace -> function invoc schedule 
        pass
    
    def read_app_list(self):
        #TODO: load functions to make apps
        pass
    
    def pick_policy_worker(self, policy_name):
        if policy_name == 'hybrid_histogram':
            return HybridHistogramPolicyWorker(self.config)
        if policy_name == 'fix_keep_alive':
            return FixKeepAlivePolicyWorker(self.config)
        
    def build_container(self,app_list, policy_name='hybrid_histogram'):
        container_dict = defaultdict(Application)
        for app in app_list:
            policy_worker = self.pick_policy_worker(policy_name)
            container = Container(app, app.app_id, policy_worker)
            container_dict[app.app_id] = container
        return container_dict
        
    def simulate(self):
        while True:
            for app in self.app_list:
                #check if there is a function invocation in app at current time clock
                #compare the clock with the function's invocation schedule
                is_invoc_now, invoc_func_id = app.is_invoc(self.clock)
                if is_invoc_now:
                    container = self.container_dict[app.app_id]
                    #check if the container is idle, if not, drop this invocation
                    if container.is_idle():
                         container.invoc_event(invoc_func_id)
                         #idle time = last excution end time - new execution start time
                         idle_time = container.get_idle_time()
                         # if use fix keep alive policy, the prewarm window is 0
                         pre_warm_window, keep_alive_window = container.policy_worker.run_policy(idle_time)
                         # if use fix keep alive policy, the prewarm window is 0
                         container.set_prewarm_window(pre_warm_window)
                         container.set_keep_alive_window(keep_alive_window)
            # tik tok global time clock
            self.tik_tok()
            for container in self.container_dict.values():
                container.tik_tok()
                         
    def tik_tok(self):
        time.sleep(2)
        self.clock += 1
        
        