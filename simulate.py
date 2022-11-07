#!/usr/bin/env python
from utils import faasSimulator, Config, HybridHistogramPolicyWorker, FixKeepAliveWindowPolicyWorker
import argparse
from os.path import join

policy_dict = {
    "fix": {"yaml_name": "fix-keep-alive-config.yaml", "policy": FixKeepAliveWindowPolicyWorker},
    "hybrid": {"yaml_name": "histogram-config.yaml", "policy": HybridHistogramPolicyWorker}
}


def main(data_dir, policy_name):
    config = Config(policy_dict[policy_name]["yaml_name"])
    worker_args = (policy_dict[policy_name]["policy"], config)
    sim = faasSimulator(data_dir, worker_args)
    sim.run_sim()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='A simulation of the FaaS system')
    parser.add_argument('--dataset', type=str, default=join('data',
                        'azurefunctions-dataset2019'), help='dataset path')
    parser.add_argument('--policy', type=str, default='hybrid',
                        help='Dataset name', choices=['fix', 'hybrid'])
    opt = parser.parse_args()
    main(opt)
