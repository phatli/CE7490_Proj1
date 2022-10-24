class Config(object):
    def __init__(self, path):
        self.some_param = 1
        self.idle_time_uper_bound = 100
        self.min_invoc_count = 100
        self.max_oob_count = 10
        self.idle_time_cv_thres = 2
    def yaml_loader(self, path):
        pass