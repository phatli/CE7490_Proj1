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
            self.idle_time_uper_bound = config.get('idle_time_uper_bound',None)
            self.min_invoc_count = config.get('min_invoc_count',None)
            self.max_oob_count = config.get('max_oob_count',None)
            self.idle_time_cv_thres = config.get('idle_time_cv_thres',None)
            self.prewarm_window_ratio = config.get('prewarm_window_ratio',None)
            self.keep_alive_window_ratio = config.get('keep_alive_window_ratio',None)
            self.fix_keep_alive_window_size = config.get('fix_keep_alive_window_size',None)