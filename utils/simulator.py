# from simfaas.ServerlessSimulator import ServerlessSimulator as Sim
import pandas as pd
import math
import os
import json
import pickle
from os.path import exists, join
from os import makedirs
from .hybrid_histogram_policy_worker import ROOT_DIR


class faasSimulator:
    def __init__(self, data_dir, worker_args):
        self.worker_args = worker_args
        if not "json" in data_dir:
            self.dataset_name = data_dir.split('/')[-1]
            self.apps_dict, self.total_step = self.__loadTrace(data_dir)
        else:
            self.dataset_name = data_dir.split('/')[-1].split('.')[0]
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

        return invoc_lsts

    def __registerAPP(self, apps_dict):
        apps_lst = []
        for i, app_id in enumerate(apps_dict.keys(), 1):
            print(f"Registering {i}/{len(apps_dict)} app", end="\r")
            app = fakeAPP(app_id, *self.worker_args)
            for func_id, func in apps_dict[app_id].items():
                app.register_func(func_id, math.ceil(
                    sum(func["Average"])/len(func["Average"])/60000))
            apps_lst.append(app)
        print("")
        return apps_lst

    def __len__(self):
        return self.total_step

    def run_sim(self):
        result = {}
        if not exists(join(ROOT_DIR, "results")):
            makedirs(join(ROOT_DIR, "results"))
        output_path = join(
            ROOT_DIR, "results", f"{self.worker_args[0].get_name(self.worker_args[1])}.json")
        for i, app in enumerate(self.apps_lst):
            for t in range(self.total_step):
                print(
                    f"Simulating step {t}/{self.total_step} in {i}/{len(self.apps_lst)} app", end="\r")
            # for app in self.apps_lst:
            #     app.step(
            #         self.invoc_lsts[t][app.app_id] if app.app_id in self.invoc_lsts[t].keys() else [])
                app.step(
                    self.invoc_lsts[t][app.app_id] if app.app_id in self.invoc_lsts[t].keys() else [])
                if t == self.total_step-1:
                    app.policy_worker.vis_histogram(
                        app.policy_worker.in_bound_idle_time_lists)
            result[app.app_id] = app.get_record()

        print("")
        with open(output_path, 'w') as f:
            json.dump(result, f)


class fakeAPP:
    def __init__(self, app_id, POLICY_WORKER_CLASS, worker_config):
        self.app_id = app_id
        self.win_state = windowState(240, 0)
        self.run_state = False  # app not running => false, running => true
        self.func_dict = {}
        self.policy_worker = POLICY_WORKER_CLASS(worker_config, app_id)
        self.step_time = 0
        self.init_record()

    def step(self, invocs_lst=[]):
        self.invoc_funcs(invocs_lst)
        isIdle = self.funcs_step()
        if self.run_state and not isIdle:
            self.end_exec()
        self.win_state.step()
        self.record_state()
        self.step_time += 1

    def end_exec(self):
        """App change from running to not running
        """
        # invoc end, start counting IT
        self.run_state = False

        # At the end of execution, need to change to pre-warm state
        self.win_state.start()
        # if prewarm_win is 0, then env_state will be updated to True in env_step()
        self.releases_record.append(self.step_time)

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
            if not self.get_env_state():
                self.coldstart_record.append(self.step_time)
                # Load env
                self.win_state.stop_and_reset()  # Stop and reset envWatcher until execution ended
                if len(self.releases_record) > 0:
                    self.prewarm_win, self.keep_alive_win = self.policy_worker.run_policy(
                        self.step_time - self.releases_record[-1])
            else:
                self.warm_state_record.append(self.step_time)

            self.run_state = True
            for func_id in invocs_lst:
                assert func_id in self.func_dict.keys(
                ), "Function ID not found, please register it first"
                self.func_dict[func_id].exec()

    def get_env_state(self):
        if self.win_state.enable:
            return self.win_state.state
        else:
            return self.run_state

    def register_func(self, func_id, exec_time):
        func = fakeFunc(func_id, exec_time)
        self.func_dict[func_id] = func

    def init_record(self):
        self.releases_record = []
        self.coldstart_record = []
        self.warmstart_record = []
        self.warm_state_record = []
        self.run_state_record = []
        self.win_state_record = []

    def record_state(self):
        if self.get_env_state():
            self.warm_state_record.append(self.step_time)
        if self.run_state:
            self.run_state_record.append(self.step_time)
        if self.win_state.state:
            self.win_state_record.append(self.step_time)

    def get_record(self):
        return {
            "release": self.releases_record,
            "coldstart": self.coldstart_record,
            "warmstart": self.warmstart_record,
            "warm_state": self.warm_state_record,
            "run_state": self.run_state_record,
            "win_state": self.win_state_record
        }


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
            if self.count == 0:
                self.count = self.exec_time
                self.state = False
            self.count -= 1


class windowState:
    def __init__(self, prewarm_win, keep_alive_win):
        self.state = False  # False: prewarm, True: keep_alive
        self.prewarm_win = prewarm_win
        self.keep_alive_win = keep_alive_win
        self.count = self.prewarm_win
        self.enable = True

    def step(self):
        if self.enable:
            while (self.count == 0):
                # Change from keep-alive to pre-warm
                self.enter_prewarm() if self.state else self.enter_keep_alive()

            self.count -= 1

    def stop_and_reset(self):
        self.enable = False
        self.count = self.prewarm_win
        self.state = False

    def start(self):
        self.enable = True

    def enter_prewarm(self):
        self.count = self.prewarm_win
        self.state = False

    def enter_keep_alive(self):
        self.count = self.keep_alive_win
        self.state = True


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
