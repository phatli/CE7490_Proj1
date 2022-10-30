import yaml
class Config(object):
    def __init__(self, path):
        self.idle_time_uper_bound = 200
        self.min_invoc_count = 20
        self.max_oob_count = 10
        self.idle_time_cv_thres = 2
        self.prewarm_window_ratio = 0.85
        self.keep_alive_window_ratio = 0.15
        
        self.load_yaml(path)
        
    def load_yaml(self, path):
        with open(path, 'r') as f:
            config = yaml.safe_load(f)
            self.idle_time_uper_bound = config['idle_time_uper_bound']
            self.min_invoc_count = config['min_invoc_count']
            self.max_oob_count = config['max_oob_count']
            self.idle_time_cv_thres = config['idle_time_cv_thres']
            self.prewarm_window_ratio = config['prewarm_window_ratio']
            self.keep_alive_window_ratio = config['keep_alive_window_ratio']