class Config(object):
    def __init__(self, path):
        self.some_param = 1
        self.idle_time_uper_bound = 200
        self.min_invoc_count = 20
        self.max_oob_count = 10
        self.idle_time_cv_thres = 2
        self.prewarm_window_ratio = 0.85
        self.keep_alive_window_ratio = 0.15
    def yaml_loader(self, path):
        pass