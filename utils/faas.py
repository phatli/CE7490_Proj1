from utils.hybrid_histogram_policy_worker import HybridHistogramPolicyWorker
from utils.config import Config
from utils.application import Application

import time
import threading

class FunctionasServiceWorker(object):
    def __init__(self, config):
        function_list = []
        function_list.append(Function(1, "function1", 1, 1, 1))
        self.app = Application(1, "app1", 128, 0, 20, 20, function_list)
        self.hybrid_histogram_policy_worker = HybridHistogramPolicyWorker(config)
    
    def service_worker(self):
        app_worker = threading.timer(self.app.app_duration, self.app.working)
        app_worker.start()
        
    def process_invocation(self, curr_time):
        pass
