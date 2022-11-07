# CE7490_Proj1
- [CE7490_Proj1](#ce7490_proj1)
  - [Setup](#setup)
  - [Datasets](#datasets)
  - [Run simulator](#run-simulator)

This is a repository for the CE7490 Project 1 Serverless Computing.

## Setup

```bash
conda create -n ce7490 python=3.9
conda activate ce7490
pip install pmdarima
```
Or use docker
```bash
docker-compose up -d
```
## Datasets
Download traces [Azure/AzurePublicDataset](https://github.com/Azure/AzurePublicDataset) under `./data/`.

## Run simulator

```
python simulate.py --policy hybrid
```
Then results of each application would be generated in `results/`.
Each generated `json` file is named by application id. It consists of timestamps of 
- when app released from executaion to idle
- coldstarts
- warmstarts
- when environment is loaded to memory
- when application is executing
- when it is in pre-warming window
- when it is in keep-alive window