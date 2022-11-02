import os 
import sys

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import matplotlib
# matplotlib.rcParams['font.sans-serif'] = ['SimHei'] # For Chinese characters
# matplotlib.rcParams['axes.unicode_minus'] = False #For plus and minus signs

# Fix Keep Alive Window Policy
class FixKeepAliveWindowPolicyWorker(object):
    def __init__(self, config):
        self.keep_alive_window = config.fix_keep_alive_window_size
        self.prewarm_window = 0
    
    def run_policy(self, idle_time):
        return 0, self.keep_alive_window

    @staticmethod
    def get_name(config):
        return f"FixKeepAliveWindowPolicy_{config.fix_keep_alive_window_size}"

