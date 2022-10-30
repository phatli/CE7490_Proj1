# from simfaas.ServerlessSimulator import ServerlessSimulator as Sim
import pandas as pd
import math
import os
import json
from os.path import exists
from os import makedirs


class faasSimulator:
    def __init__(self, data_dir, policy_worker):
        self.policy_worker = policy_worker
        if not "json" in data_dir:
            self.apps_dict, self.total_step = self.__loadTrace(data_dir)
        else:
            with open(data_dir, 'rb') as f:
                self.apps_dict = json.load(f)
                self.total_step = 14 * 60 * 24
        self.__cleanIncompleteTrace()
        assert self.__isCompleteTrace(
            self.apps_dict), "The apps_dict is not complete!"
        self.invoc_lsts = self.__getInvocLsts(self.apps_dict)
        self.apps_lst = self.__registerAPP(self.apps_dict)
        self.step = 1
        self.recorder = []

    def __loadTrace(self, data_dir):
        files = os.listdir(data_dir)
        invocation_files = [f for f in files if f[0] == 'i']
        invocation_files.sort()
        invoc_dfs = [pd.read_csv(data_dir+file)
                     for file in invocation_files]
        function_files = [f for f in files if f[0] == 'f']
        function_files.sort()
        func_dfs = [pd.read_csv(data_dir+file)
                    for file in function_files]
        apps_dict = {}
        total_step = len(invocation_files) * 60 * 24

        for i in range(len(func_dfs)):
            for _, row in func_dfs[i].iterrows():
                if not row["HashApp"] in apps_dict.keys():
                    apps_dict[row["HashApp"]] = {
                        row["HashFunction"]: {
                            "Average": [row["Average"]] * len(func_dfs)
                        }
                    }
                elif not row["HashFunction"] in apps_dict[row["HashApp"]].keys():
                    apps_dict[row["HashApp"]][row["HashFunction"]] = {
                        "Average": [row["Average"]] * len(func_dfs)
                    }
                else:
                    apps_dict[row["HashApp"]][row["HashFunction"]
                                              ]["Average"][i] = row["Average"]
        for i in range(len(invoc_dfs)):
            for j, row in invoc_dfs[i].iterrows():
                if not row["HashApp"] in apps_dict.keys():
                    continue
                if not row["HashFunction"] in apps_dict[row["HashApp"]].keys():
                    continue
                func_dict = apps_dict[row["HashApp"]][row["HashFunction"]]
                invoc_lst = row.tolist()[4:]
                if not "invoc" in func_dict.keys():
                    func_dict["invoc"] = [idx + i * 1440 for idx,
                                          x in enumerate(invoc_lst) if x == 1]
                else:
                    func_dict["invoc"] += [idx + i * 1440 for idx,
                                           x in enumerate(invoc_lst) if x == 1]
                if not "trigger" in func_dict.keys():
                    func_dict["trigger"] = [row["Trigger"]] * len(invoc_dfs)
                else:
                    func_dict["trigger"][i] = row["Trigger"]
        with open('data/azurefunctions-dataset2019.json', "w") as f:
            json.dump(apps_dict, f)
        # app_files = [f for f in files if f[0] == 'a']
        # app_files.sort()
        # app_dfs = [pd.read_csv(data_dir+file) for file in app_files]
        return apps_dict, total_step

    def __cleanIncompleteTrace(self):
        print(f"Cleaning incomplete traces.")
        func_2b_removed = []
        for app_id, funcs in self.apps_dict.items():
            for func_id, func in funcs.items():
                if not "invoc" in func.keys():
                    func_2b_removed.append([app_id, func_id])
        for app_id, func_id in func_2b_removed:
            self.apps_dict[app_id].pop(func_id)

    def __isCompleteTrace(self, apps_dict):
        print(f"Checking if trace is complete")
        for app_id, funcs in apps_dict.items():
            for func_id, func in funcs.items():
                if not "invoc" in func.keys():
                    return False
        return True

    def __getInvocLsts(self, apps_dict):
        invoc_lsts = [{} for _ in range(14 * 60 * 24)]
        for i, app_id in enumerate(apps_dict.keys()):
            print(
                f"Retrieving invocations list for {i}/{len(apps_dict)} app", end="\r")
            for func_id, func in apps_dict[app_id].items():
                for invoc_idx in func["invoc"]:
                    if not app_id in invoc_lsts[invoc_idx].keys():
                        invoc_lsts[invoc_idx][app_id] = [func_id]
                    else:
                        invoc_lsts[invoc_idx][app_id].append(func_id)
        print("")
        return invoc_lsts

    def __registerAPP(self, apps_dict):
        apps_lst = []
        for i, app_id in enumerate(apps_dict.keys(), 1):
            print(f"Registering {i}/{len(apps_dict)} app", end="\r")
            app = fakeAPP(app_id, self.policy_worker)
            for func_id, func in apps_dict[app_id].items():
                app.register_func(func_id, func["Average"])
            apps_lst.append(app)
        print("")
        return apps_lst

    def __len__(self):
        return self.total_step

    def run_sim(self):
        for t in range(self.total_step):
            print(f"Simulating step {t}/{self.total_step}")
            for app in self.apps_lst:
                app.step(
                    self.invoc_lsts[t][app.app_id] if app.app_id in self.invoc_lsts[t].keys() else [])


class fakeAPP:
    def __init__(self, app_id, policy_worker):
        self.app_id = app_id
        self.prewarm_win = 240
        self.keep_alive_win = 0
        self.run_state = False  # app not running => false, running => true
        self.env_state = False  # warm => true, true => false
        self.env_count = self.prewarm_win
        self.func_dict = {}
        self.policy_worker = policy_worker
        self.step_time = 0
        self.app_record = {}

    def step(self, invocs_lst=[]):
        self.invoc_funcs(invocs_lst)
        isIdle = self.funcs_step()
        if self.run_state and not isIdle:
            self.end_exec()
        self.env_step()
        self.step_time += 1

    def end_exec(self):
        """App change from running to not running
        """
        # invoc end, start counting IT
        self.run_state = False
        self.prewarm_win, self.keep_alive_win = self.policy_worker.process_invocation(
            self.step_time)

        # At the end of execution, need to change to pre-warm state
        self.env_count = self.prewarm_win
        # if prewarm_win is 0, then env_state will be updated to True in env_step()
        self.env_state = False

    def env_step(self):
        if self.env_count == 0:
            if self.env_state:
                # Change from keep-alive to pre-warm
                self.env_count = self.prewarm_win
                self.env_state = False
            else:
                self.env_count = self.keep_alive_win
                self.env_state = True
        self.env_count -= 1

    def funcs_step(self):
        """Run a step of all funcs

        Returns:
            isIdle(Bool): True if all funcs are idle.
        """
        isIdle = True
        for func in self.func_dict.values():
            func.step()  # step may update func.state
            isIdle = isIdle and not func.state  # make sure every func is off now
        return isIdle

    def invoc_funcs(self, invocs_lst):
        if invocs_lst:
            self.run_state = True
            self.env_state = True
            for func_id in invocs_lst:
                assert func_id in self.func_dic.keys(
                ), "Function ID not found, please register it first"
                self.func_dict[func_id].exec()

    def register_func(self, func_id, exec_time):
        func = fakeFunc(func_id, exec_time)
        self.func_dict[func_id] = func


class fakeFunc:
    def __init__(self, func_id, exec_time):
        """Genearte a fake function

        Args:
            func_id (str): Function ID, unique within each app.
            exec_time (int): Average executation time, step.
        """
        self.func_id = func_id
        self.exec_time = exec_time
        self.count = self.exec_time
        self.state = False  # True => execuating, False => Idle

    def exec(self):
        if self.state:
            self.count = self.exec_time
        else:
            self.state = True

    def step(self):
        if self.state:
            self.count -= 1
            if self.count == 0:
                self.count = self.exec_time
                self.state = False


def getAttrsFromObjects(list_of_objects, attr_name):
    """Get a list of attributes from a list of objects.

    Args:
        list_of_objects (List): List of instances of a SAME class
        attr_name (str): Attribute name

    Returns:
        [list]: List of instances' attributes
    """
    list_of_attr = []
    for object in list_of_objects:
        list_of_attr.append(getattr(object, attr_name))
    return list_of_attr


def main():
    faasSimulator("data/azurefunctions-dataset2019.json", None)


if __name__ == '__main__':
    main()
