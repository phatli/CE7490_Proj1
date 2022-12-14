from os import makedirs, pardir
from os.path import exists, join, abspath, dirname
from pmdarima.arima import auto_arima
import pmdarima as pm
from pmdarima import model_selection

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt

ROOT_DIR = abspath(
    join(dirname(__file__), pardir))


# One Histogram for one application

class HybridHistogramPolicyWorker(object):
    def __init__(self, config, app_id, vis_dir=join(ROOT_DIR, "results/vis_hist")):
        self.config = config
        self.bins_num = 20
        self.keep_alive_window = 10
        self.prewarm_window = 0
        self.oob_count = 0
        self.invoc_count = 0
        self.app_id = app_id
        self.vis_dir = vis_dir
        self.it_cv = 0
        self.is_hist_triggered = False
        self.is_arima_triggered = False

        self.hist_range = self.config.idle_time_uper_bound - 0

        # Keep a list of in bound idle times to make distribution
        self.in_bound_idle_time_lists = []

        # For calculating the app's IT
        # self.current_timestamp = 0
        self.previous_time = 0

    def run_policy(self, idle_time):
        self.invoc_count += 1
        self.update_idle_time_list(idle_time)
        idle_time_hist, bins = self.update_idle_time_dist()
        # self.vis_histogram(self.in_bound_idle_time_lists)

        if self.is_too_many_oob_its(idle_time):
            self.is_arima_triggered = True
            # Use ARIMA
            self.prewarm_window, self.keep_alive_window = self.auto_arima_forcast()
        else:
            if self.is_enough_invocations() and self.is_pattern_representative(idle_time_hist):
                self.is_hist_triggered = True
                # Use histogram
                self.prewarm_window, self.keep_alive_window = self.histogram_forcast()
            else:
                # Standard keep alive strategy
                self.prewarm_window = 0
                self.keep_alive_window = self.hist_range

        return self.prewarm_window, self.keep_alive_window

    def update_idle_time_list(self, idle_time):
        self.in_bound_idle_time_lists.append(idle_time)

    def auto_arima_forcast(self):
        '''
        网址:http://alkaline-ml.com/pmdarima/modules/generated/pmdarima.arima.auto_arima.html?highlight=auto_arima
        auto_arima部分参数解析:
            1.start_p:p的起始值，自回归(“AR”)模型的阶数(或滞后时间的数量),必须是正整数
            2.start_q:q的初始值，移动平均(MA)模型的阶数。必须是正整数。
            3.max_p:p的最大值，必须是大于或等于start_p的正整数。
            4.max_q:q的最大值，必须是一个大于start_q的正整数
            5.seasonal:是否适合季节性ARIMA。默认是正确的。注意，如果season为真，而m == 1，则season将设置为False。
            6.stationary :时间序列是否平稳，d是否为零。
            6.information_criterion：信息准则用于选择最佳的ARIMA模型。(‘aic’，‘bic’，‘hqic’，‘oob’)之一
            7.alpha：检验水平的检验显著性，默认0.05
            8.test:如果stationary为假且d为None，用来检测平稳性的单位根检验的类型。默认为‘kpss’;可设置为adf
            9.n_jobs ：网格搜索中并行拟合的模型数(逐步=False)。默认值是1，但是-1可以用来表示“尽可能多”。
            10.suppress_warnings：statsmodel中可能会抛出许多警告。如果suppress_warnings为真，那么来自ARIMA的所有警告都将被压制
            11.error_action:如果由于某种原因无法匹配ARIMA，则可以控制错误处理行为。(warn,raise,ignore,trace)
            12.max_d:d的最大值，即非季节差异的最大数量。必须是大于或等于d的正整数。
            13.trace:是否打印适合的状态。如果值为False，则不会打印任何调试信息。值为真会打印一些
        '''

        # Fit the model
        arima = auto_arima(self.in_bound_idle_time_lists, start_p=0, start_q=0,
                           max_p=6, max_q=6, max_d=2,
                           seasonal=True,
                           d=1, D=1, trace=True,
                           error_action='ignore',
                           information_criterion='aic',
                           njob=-1,
                           suppress_warnings=True,
                           stepwise=True)
        arima.fit(self.in_bound_idle_time_lists)
        # Forecast
        idle_time_forecast = arima.predict(n_periods=1)
        prewarm_window = idle_time_forecast[0] * \
            self.config.prewarm_window_ratio  # 85%
        keep_alive_window = idle_time_forecast[0] * \
            self.config.keep_alive_window_ratio  # 15%
        return prewarm_window, keep_alive_window

    def update_idle_time_dist(self):
        # bins指定统计的区间个数
        # range是一个长度为2的元组，表示统计范围的最小值和最大值，默认值None，表示范围由数据的范围决定
        # weights为数组的每个元素指定了权值,histogram()会对区间中数组所对应的权值进行求和
        # density为True时，返回每个区间的概率密度为False，返回每个区间中元素的个数
        # create histogram from idle time list
        hist, bins = np.histogram(
            self.in_bound_idle_time_lists, bins=self.bins_num, range=(0, self.hist_range))
        return hist, bins

    def histogram_forcast(self):
        # prewarm window is head 5th percentile of IT distribution
        prewarm_window = int(np.percentile(self.in_bound_idle_time_lists, 5))
        # keep alive window is tail 99th percentile of IT distribution
        keep_alive_window = int(np.percentile(self.in_bound_idle_time_lists, 99))
        return prewarm_window, keep_alive_window

    def vis_histogram(self, data, title='App\'s Idle Time Distribution'):
        plt.clf()
        plt.hist(data, bins=self.bins_num, facecolor="blue",
                 edgecolor="black", alpha=0.7)
        plt.xlabel("Idle Time")
        plt.ylabel("Frequency")
        plt.title(title)
        plt.show()
        if not exists(self.vis_dir):
            makedirs(self.vis_dir)
        plt.savefig(f"{join(self.vis_dir,self.app_id)}.png")

    def caculate_idle_time_cv(self, hist_count):
        # calculate idle time coefficient of variation
        idle_time_cv = np.std(hist_count) / np.mean(hist_count)
        return idle_time_cv

    def is_pattern_representative(self, hist):
        self.it_cv = self.caculate_idle_time_cv(hist)
        if self.it_cv > self.config.idle_time_cv_thres:
            return True
        else:
            return False

    def is_too_many_oob_its(self, idle_time):
        oob_count = self.count_out_of_bounds_its(idle_time)
        if oob_count > self.config.max_oob_count:
            return True
        return False

    def count_out_of_bounds_its(self, idle_time):
        if idle_time > self.config.idle_time_uper_bound:
            self.oob_count += 1
        return self.oob_count

    def is_enough_invocations(self):
        if self.invoc_count > self.config.min_invoc_count:
            return True
        return False

    @staticmethod
    def get_name(config):
        return "HybridHistogramPolicy"
    
    def get_record(self):
        return {
            "idle_time": self.in_bound_idle_time_lists,
            "invoc_count": self.invoc_count,
            "oob_count": self.oob_count,
            "prewarm_win": self.prewarm_window,
            "keep_alive_win": self.keep_alive_window,
            "it_cv": self.it_cv,
            "is_hist_triggered": self.is_hist_triggered,
            "is_arima_triggered": self.is_arima_triggered
        }

    # def process_invocation(self, curr_time):
    #     idle_time = curr_time - self.previous_time
    #     self.previous_time = curr_time
    #     self.invoc_count += 1
    #     self.update_idle_time_list(idle_time)
    #     idle_time_hist, bins = self.update_idle_time_dist(idle_time)

    #     if self.is_too_many_oob_its(idle_time):
    #         # Use ARIMA
    #         self.prewarm_window, self.keep_alive_window = self.auto_arima_forcast()
    #     else:
    #         if self.is_enough_invocations() and self.is_pattern_representative(idle_time_hist, bins):
    #             # Use histogram
    #             self.prewarm_window, self.keep_alive_window = self.histogram_forcast(idle_time_hist)
    #         else:
    #             # Standard keep alive strategy
    #             self.prewarm_window = 0
    #             self.keep_alive_window = self.hist_range

    #     return self.prewarm_window, self.keep_alive_window
