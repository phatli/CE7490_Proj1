import os
import sys

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
plt.rcParams['figure.figsize'] = (20, 3)

class AzureDataLoader(object):
    def __init__(self, path="data/"):
        self.data_path = path
        self.data = pd.read_csv(self.data_path)
        
        print(f"Data path: {self.data_path}")

        files = os.listdir(self.data_path)
        function_files = [f for f in files if f[0] == 'f']
        invocation_files = [f for f in files if f[0] == 'i']
        app_files = [f for f in files if f[0] == 'a']

        print(f"Funtion files: \n {function_files}")
        print(f"Invocation files: \n {invocation_files}")
        print(f"App files: \n {app_files}")
        
        func_dfs = [pd.read_csv(self.data_path+file) for file in function_files]
        invoc_dfs = [pd.read_csv(self.data_path+file) for file in invocation_files]
        app_dfs = [pd.read_csv(self.data_path+file) for file in app_files]

        self.func_df = pd.concat(func_dfs)
        self.invoc_df = pd.concat(invoc_dfs)
        self.app_df = pd.concat(app_dfs)

        print(f"Functions: {len(self.func_df)}")
        print(f"Invocations: {len(self.invoc_df)}")
        print(f"Apps: {len(self.app_df)}")