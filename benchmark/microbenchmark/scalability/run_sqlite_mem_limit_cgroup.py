from collections import defaultdict
import sys
sys.path.append("../../macrobenchmark/")
sys.path.append("../../")

import os
import subprocess
from datetime import datetime
from process_sql import process_sql
from helpers import clear_cache
from time import sleep
import json
import pandas as pd

NOW = datetime.now().strftime("%Y%m%d-%H%M%S")
ROOT_DIR = os.path.realpath("../../../")
CURR_DIR = os.path.realpath(".")
SQL_FILE         = os.path.join(ROOT_DIR, "tpch/tpc_h_queries_filter_proj.sql")
OUT_FILE         = "queries.csv"
RUN_TYPE         = "dummy"
NUM_QUERIES      = 22
DB_NAME = "tpch/build/TPCH-{}.db"
SEC_DB_NAME = "tpch/build/TPCH-{}-fresh-enc.db"
MT_NAME = "tpch/build/merkle-tree-{}.bin"

# environment variables
KIND = sys.argv[1]
SCALE_FACTOR = float(sys.argv[2])

CURR_MEM_LIMIT = -1

def setup_exp():
    process_sql(SQL_FILE, OUT_FILE, RUN_TYPE, NUM_QUERIES)

    # generate the sqlite binary
    os.chdir(os.path.join(ROOT_DIR, "fresh-sqlite"))
    subprocess.run(["make", "storage-query"])
    os.chdir(CURR_DIR)

    # Create a cgroup to control memory resources
    print("Creating a cgroup")
    proc = subprocess.run(["sudo", "mkdir", "-p", "/sys/fs/cgroup/memory/sqlite_cgroup"])

def cleanup_exp():
    subprocess.run(["sudo", "rmdir", "/sys/fs/cgroup/memory/sqlite_cgroup"])

def setlimits():
    pid = os.getpid()
    # print("{}, {}".format(pid, CURR_MEM_LIMIT))
    subprocess.run(["sudo", "./setup_cgroups.sh", "{}".format(pid), "{}".format(CURR_MEM_LIMIT)])
    # subprocess.run(["cat", "/sys/fs/cgroup/memory/sqlite_cgroup/cgroup.procs"])
    # subprocess.run(["cat", "/sys/fs/cgroup/memory/sqlite_cgroup/memory.limit_in_bytes"])

def run_exp(stats, query, query_num):
    mt = None
    if int(SCALE_FACTOR) == SCALE_FACTOR:
        scale_factor = int(SCALE_FACTOR)
    else:
        scale_factor = SCALE_FACTOR
    if KIND == "secure":
        db = SEC_DB_NAME.format(scale_factor)
        mt = MT_NAME.format(scale_factor)
        pwd = "kun"
    else:
        db = DB_NAME.format(scale_factor)
        mt = MT_NAME.format(scale_factor)
        pwd = ""
    proc = subprocess.Popen([os.path.join(ROOT_DIR, "fresh-sqlite/storage-query"), os.path.join(ROOT_DIR, mt), os.path.join(ROOT_DIR, db), pwd, query], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, preexec_fn=setlimits)
    proc.wait()

    res = proc.stdout
    for line in res:
        stats["mem"].append(CURR_MEM_LIMIT)
        stats["kind"].append(KIND)
        stats["scale_factor"].append(scale_factor)
        stats["query"].append(query_num)
        try:
            print(line)
            data = json.loads(line.rstrip())
            stats["time [s]"].append(data["query_exec_time"])
            stats["codec_time [s]"].append(data["codec_time"])
            stats["mt_verify_time [s]"].append(data["mt_verify_time"])
        except Exception as e:
            stats["time [s]"].append(0)
            stats["codec_time [s]"].append(0)
            stats["mt_verify_time [s]"].append(0)
            print(e)
    
# Run script as sudo
def main():
    mem = sys.argv[3:] # in bytes separated by spaces
    mem = [int(i) for i in mem]

    setup_exp()

    df = pd.read_csv(OUT_FILE, sep="|", header=None)
    df = list(df[df.columns[:2]].values)
    stats = defaultdict(list)

    for q in df:
        query = q[1]
        for i in mem:
            clear_cache()
            sleep(5)
            global CURR_MEM_LIMIT
            CURR_MEM_LIMIT = i
            print(CURR_MEM_LIMIT)
            run_exp(stats, q[1], q[0])
    cleanup_exp()

    df = pd.DataFrame(stats)
    df.to_csv("sqlite_mem_limit_cgroup_{}.csv".format(NOW), index=False)


if __name__=="__main__":
    main()