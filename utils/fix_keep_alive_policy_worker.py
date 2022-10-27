import os 
import sys

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['SimHei'] # For Chinese characters
matplotlib.rcParams['axes.unicode_minus'] = False #For plus and minus signs

# Fix Keep Alive Window Policy
class FixKeepAliveWindowPolicyWorker(object):
    def __init__(self, fix_keep_alive_window_size=20):
        self.keep_alive_window = fix_keep_alive_window_size
        self.prewarm_window = 0
    
    def process_invocation(self, curr_time):
        return self.prewarm_window, self.keep_alive_window

