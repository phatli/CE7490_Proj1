# from simfaas.ServerlessSimulator import ServerlessSimulator as Sim
import pandas as pd
import math
import os
import json
from os.path import exists, join
from os import makedirs
from .hybrid_histogram_policy_worker import ROOT_DIR
from multiprocessing import Pool


class faasSimulator:
    def __init__(self, data_dir, worker_args):
        self.least_invoc_num = 15
        self.save_vis_hist = False
        self.worker_args = worker_args
        if not "json" in data_dir:
            self.dataset_name = data_dir.split('/')[-1]
            self.apps_dict, self.total_step = self.__loadTrace(data_dir)
        else:
            self.dataset_name = data_dir.split('/')[-1].split('.')[0]
            with open(data_dir, 'rb') as f:
                self.apps_dict = json.load(f)
                self.total_step = 14 * 60 * 24
        self.__cleanBadTrace()
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

    def __cleanBadTrace(self):
        print(f"Cleaning incomplete traces & traces  with too little invoc...")
        func_2b_removed = []
        app_2b_removed = []
        for app_id, funcs in self.apps_dict.items():
            invoc_count = 0
            for func_id, func in funcs.items():
                if not "invoc" in func.keys():
                    func_2b_removed.append([app_id, func_id])
                else:
                    invoc_count += 1
            if invoc_count <= self.least_invoc_num:
                app_2b_removed.append(app_id)

        for app_id, func_id in func_2b_removed:
            self.apps_dict[app_id].pop(func_id)
        for app_id in app_2b_removed:
            self.apps_dict.pop(app_id)

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

        chunk_size = len(self.apps_lst) // 5
        with Pool(5) as p:
            p.map(self.run_sim_app_lst, [self.apps_lst[i:i + chunk_size]
                  for i in range(0, len(self.apps_lst), chunk_size)])

        # self.run_sim_app_lst(self.apps_lst)

    def run_sim_app_lst(self, apps_lst):
        output_dir = join(
            ROOT_DIR, "results", f"{self.worker_args[0].get_name(self.worker_args[1])}")
        if not exists(output_dir):
            makedirs(output_dir)
        for i, app in enumerate(apps_lst):
            hasRun = False
            for _, _, files in os.walk(output_dir+"/"):
                if f"{app.app_id}.json" in files:
                    hasRun = True
            if hasRun: continue

            for t in range(self.total_step):
                print(
                    f"Simulating step {t}/{self.total_step} in {i}/{len(apps_lst)} app", end="\r")
                app.step(
                    self.invoc_lsts[t][app.app_id] if app.app_id in self.invoc_lsts[t].keys() else [])
                if t == self.total_step-1 and self.save_vis_hist:
                    app.policy_worker.vis_histogram(
                        app.policy_worker.in_bound_idle_time_lists)
                if "HybridHistogramPolicy" in app.policy_worker.get_name(app.policy_worker.config):
                    if app.policy_worker.is_arima_triggered:
                        break
            result = app.get_record()
            if "HybridHistogramPolicy" in app.policy_worker.get_name(app.policy_worker.config):
                if app.policy_worker.is_hist_triggered:
                    output_file_dir = join(output_dir, "hist")
                elif app.policy_worker.is_arima_triggered:
                    output_file_dir = join(output_dir, "arima")
                else:
                    output_file_dir = join(output_dir, "fix")
            else:
                output_file_dir = output_dir

            if not exists(output_file_dir):
                os.makedirs(output_file_dir)

            with open(join(output_file_dir, f"{app.app_id}.json"), 'w') as f:
                json.dump(result, f)

        print("")


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
        self.pre_funcs_invoc(invocs_lst)
        isIdle = self.funcs_step()
        if self.run_state and isIdle:
            # must record exec_state before it was change
            self.run_state_record.append(self.step_time)
            self.end_exec()  # change run_state
        elif invocs_lst:
            self.run_state = True

        self.win_state.step()
        self.record_state()
        self.step_time += 1

    def end_exec(self):
        """App change from running to not running
        """
        # invoc end, start counting IT
        self.run_state = False

        # At the end of execution, need to change to pre-warm state
        self.win_state.enter_prewarm()
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

    def pre_funcs_invoc(self, invocs_lst):
        """Manage windows state and interate with policy worker if funcs invocated

        Args:
            invocs_lst (_type_): list of invocations.
        """
        if invocs_lst:
            if not self.run_state:
                if not self.get_env_state():
                    self.coldstart_record.append(self.step_time)
                else:
                    self.warm_state_record.append(self.step_time)
                # Load env
                self.win_state.stop_and_reset()  # Stop and reset envWatcher until execution ended
                if len(self.releases_record) > 0:
                    self.win_state.prewarm_win, self.win_state.keep_alive_win = self.policy_worker.run_policy(
                        self.step_time - self.releases_record[-1])
            else:
                self.warmstart_record.append(self.step_time)

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
        self.prewarm_win_state_record = []
        self.keeplive_win_state_record = []

    def record_state(self):
        if self.get_env_state():
            self.warm_state_record.append(self.step_time)
        if self.win_state.enable:
            if self.win_state.state:
                self.keeplive_win_state_record.append(self.step_time)
            else:
                self.prewarm_win_state_record.append(self.step_time)

    def get_record(self):
        return {
            "release": self.releases_record,
            "coldstart": self.coldstart_record,
            "warmstart": self.warmstart_record,
            "warm_state": self.warm_state_record,
            "run_state": self.run_state_record,
            "prewarm_win": sepConsNums(self.prewarm_win_state_record),
            "keeplive_win": sepConsNums(self.keeplive_win_state_record),
            "policy_record": self.policy_worker.get_record()
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
        self.count = self.exec_time
        self.state = True

    def step(self):
        if self.state:
            if self.count == 0:
                self.count = self.exec_time
                self.state = False
                return
            self.count -= 1


class windowState:
    def __init__(self, prewarm_win, keep_alive_win):
        self.state = False  # False: prewarm, True: keep_alive
        self.prewarm_win = prewarm_win
        self.keep_alive_win = keep_alive_win
        self.count = self.prewarm_win
        self.enable = False

    def step(self):
        if self.enable:
            if self.count == 0:
                if self.state == 0:
                    self.enter_keep_alive()
                else:
                    self.enable = False

            self.count -= 1

    def stop_and_reset(self):
        self.enable = False
        self.count = self.prewarm_win
        self.state = False

    def enter_prewarm(self):
        self.count = self.prewarm_win
        self.state = False
        self.enable = True

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


def sepConsNums(list_of_numbers):
    list_of_lists = []
    for i in range(len(list_of_numbers)):
        if i == 0:
            list_of_lists.append([list_of_numbers[i]])
        else:
            if list_of_numbers[i] == list_of_numbers[i-1] + 1:
                if i == len(list_of_numbers) - 1:
                    list_of_lists[-1].append(list_of_numbers[i])
                else:
                    continue

            else:
                list_of_lists[-1].append(list_of_numbers[i-1])
                list_of_lists.append([list_of_numbers[i]])
    return list_of_lists


def main():
    faasSimulator("data/azurefunctions-dataset2019.json", None)
    # sepConsNums([1,3,4,5,6,7,8,15,16])


if __name__ == '__main__':
    main()
