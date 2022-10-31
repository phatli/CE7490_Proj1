#!/usr/bin/env python
from utils import faasSimulator, Config, HybridHistogramPolicyWorker, FixKeepAliveWindowPolicyWorker


def main():
    config = Config("histogram-config.yaml")
    data_dir = "data/azurefunctions-dataset2019.json"
    worker_args = (HybridHistogramPolicyWorker, config)
    sim = faasSimulator(data_dir, worker_args)


if __name__ == '__main__':
    main()
