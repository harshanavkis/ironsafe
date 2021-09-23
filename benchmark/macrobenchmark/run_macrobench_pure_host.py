import subprocess
import json
import os
from collections import defaultdict
import sys
import pandas as pd
from process_sql import process_sql
sys.path.append("../")
from helpers import clear_cache
from cpu_hotplug_helpers import setup_remote_cpu_hotplug, teardown_remote_cpu_hotplug
from datetime import datetime
import time

"""
    Environment variables:
        - NVME_TCP_DIR
        - SCALE_FACTOR
        - CPU_BENCH
        - CPU_HOTPLUG
        - REMOTE_USER
        - STORAGE_SERVER_IP
        - REMOTE_SRC
"""

# sudo docker run -it --mount type=bind,source=/home/hvub/nfs_mnt,target=/data --cpus="0.25" dummy-sqlite
NOW = datetime.now().strftime("%Y%m%d-%H%M%S")

ROOT_DIR = os.path.realpath("../../")
CURR_DIR = os.path.realpath(".")
SEC_BIN_DIR = os.path.join(ROOT_DIR, "sec-bin")

MERK_FILE = "merkle-tree-{}.bin"

SQL_FILE    = os.path.join(ROOT_DIR, "tpch/tpc_h_queries.sql")
OUT_FILE    = "queries.csv"
RUN_TYPE    = "dummy"
NUM_QUERIES = 22
CPUS = 0.4
TOTAL_STORAGE_CPUS = 16

ignore_queries = [1]

def run_local_proc(cmd, env=None):
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, env=env)
    return proc

def setup_exp():
    os.chdir(ROOT_DIR)
    cmd = ["docker", "image", "inspect", "pure-host-sec:latest"]
    proc = run_local_proc(cmd)
    # proc.wait()

    if proc.returncode == 1:
        cmd = ["docker", "build", "-f", f"{ROOT_DIR}/benchmark/scone-stuff/pure-host-sec", "-t", "pure-host-sec", f"{ROOT_DIR}/"]
        run_local_proc(cmd)
        # proc.wait()

    cmd = ["docker", "image", "inspect", "pure-host:latest"]
    proc = run_local_proc(cmd)
    if proc.returncode == 1:
        cmd = ["docker", "build", "-f", f"{ROOT_DIR}/benchmark/scone-stuff/pure-host", "-t", "pure-host", f"{ROOT_DIR}/"]
        run_local_proc(cmd)
        # proc.wait()

    os.chdir(f"{ROOT_DIR}/fresh-sqlite")
    make_env = os.environ.copy()
    make_env["SCONE"] = "false"
    make_env["OPENSSL_SRC"] = f"{ROOT_DIR}/openssl-src" 
    cmd = ["make", "clean"]
    run_local_proc(cmd)
    cmd = ["make", "hello-query"]
    run_local_proc(cmd, make_env)

    os.chdir(CURR_DIR)

    process_sql(SQL_FILE, OUT_FILE, RUN_TYPE, NUM_QUERIES)

def process_output(proc, kind, query_no, stats, cpu_hotplug):
    for line in proc.stdout:
        try:
            data = json.loads(line.rstrip())
            stats["kind"].append(kind)
            stats["query_no"].append(query_no)
            stats["cpus"].append("{}".format(cpu_hotplug))
            for i in data:
                stats[i].append(data[i])
        except Exception as e:
            continue

def run_pure_host_ns(kind, stats, cpu_hotplug):
    df = pd.read_csv(OUT_FILE, sep="|", header=None)
    df = list(df[df.columns[:2]].values)

    if cpu_hotplug != -1:
        setup_remote_cpu_hotplug(cpu_hotplug, os.environ)

    try:
        scale_factor = float(os.environ["SCALE_FACTOR"])
        if int(scale_factor)==scale_factor:
            scale_factor = int(scale_factor)
    except Exception as e:
        print("Provide SCALE_FACTOR env var")
        sys.exit(1)

    try:
        data_dir = os.environ["NVME_TCP_DIR"]
    except Exception as e:
        print("Provide NVME_TCP_DIR env var")
        sys.exit(1)

    db  = os.path.join("/data", f"TPCH-{scale_factor}.db")
    merk_file = os.path.join("/data", f"{MERK_FILE.format(scale_factor)}")
    exe = os.path.join(ROOT_DIR, "benchmark/macrobenchmark/selectivity-effect/run_pure_host_non_secure.sh")

    #cpu_df = pd.read_csv(sys.argv[1])
    #cpu_df = cpu_df.set_index("query").to_dict()
    #cpu_df = cpu_df["cpu"]

    for i in df:
        if i[0] in ignore_queries:
            continue
        #cmd = ["sudo", "systemctl", "restart", "docker"]
        #proc = subprocess.Popen(cmd)
        #proc.wait()

        #cpus = cpu_df[i[0]]

        clear_cache()
        cmd = [
        "docker",
        "run",
        #"--cpuset-cpus=0",
        "--mount",
        f"type=bind,source={data_dir},target=/data",
        #f"--cpus={CPUS}",
        "pure-host",
        "/bin/bash",
        "-c",
        "./hello-query {} {} \"\" \"{}\"".format(merk_file, db, i[1])
    ]

        print(cmd)

        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True, env=os.environ)
        proc.wait()

        #import pdb; pdb.set_trace()
        process_output(proc, kind, i[0], stats, cpu_hotplug)

        teardown_remote_cpu_hotplug(os.environ)

        time.sleep(5)

def run_pure_host_sec(kind, stats, cpu_hotplug):
    df = pd.read_csv(OUT_FILE, sep="|", header=None)
    df = list(df[df.columns[:2]].values)

    if cpu_hotplug != -1:
        setup_remote_cpu_hotplug(cpu_hotplug)

    try:
        scale_factor = float(os.environ["SCALE_FACTOR"])
        if int(scale_factor)==scale_factor:
            scale_factor = int(scale_factor)
    except Exception as e:
        print("Provide SCALE_FACTOR env var")
        sys.exit(1)

    try:
        data_dir = os.environ["NVME_TCP_DIR"]
    except Exception as e:
        print("Provide NVME_TCP_DIR env var")
        sys.exit(1)

    #cmd = ["sudo", "systemctl", "restart", "docker"]
    #proc = subprocess.Popen(cmd)
    #proc.wait()

    db  = os.path.join(data_dir, f"TPCH-{scale_factor}-fresh-enc.db")
    merk_file = os.path.join(data_dir, f"{MERK_FILE.format(scale_factor)}")

    #cmd = ["sudo", "systemctl", "restart", "docker"]
    #proc = subprocess.Popen(cmd)
    #proc.wait()

    #cpu_df = pd.read_csv(sys.argv[1])
    #cpu_df = cpu_df.set_index("query").to_dict()
    #cpu_df = cpu_df["cpu"]
    
    binary = os.path.join(SEC_BIN_DIR, "hello-query")
    scone_env = os.environ.copy()
    scone_env["SCONE_VERSION"] = "1"
    scone_env["SCONE_HEAP"] = "4G"

    for i in df:
        if i[0] in ignore_queries:
            continue
        clear_cache()

        #cpus = cpu_df[i[0]]

        cmd = [
            binary,
            merk_file,
            db,
            "kun",
            "{}".format(i[1])
            ]
        print(cmd)

        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True, env=scone_env)
        proc.wait()

        process_output(proc, kind, i[0], stats, cpu_hotplug)

        teardown_remote_cpu_hotplug(os.environ)

def run_pure_host_sec_sim(kind, stats, cpu_hotplug):
    df = pd.read_csv(OUT_FILE, sep="|", header=None)
    df = list(df[df.columns[:2]].values)

    try:
        scale_factor = float(os.environ["SCALE_FACTOR"])
        if int(scale_factor)==scale_factor:
            scale_factor = int(scale_factor)
    except Exception as e:
        print("Provide SCALE_FACTOR env var")
        sys.exit(1)

    try:
        data_dir = os.environ["NVME_TCP_DIR"]
    except Exception as e:
        print("Provide NVME_TCP_DIR env var")
        sys.exit(1)

    db  = os.path.join(data_dir, f"TPCH-{scale_factor}-fresh-enc.db")
    merk_file = os.path.join(data_dir, f"{MERK_FILE.format(scale_factor)}")
    
    binary = os.path.join(SEC_BIN_DIR, "hello-query")
    scone_env = os.environ.copy()
    scone_env["SCONE_VERSION"] = "1"
    scone_env["SCONE_HEAP"] = "4G"
    scone_env["SCONE_MODE"] = "SIM"

    for i in df:
        if i[0] in ignore_queries:
            continue
        clear_cache()

        #cpus = cpu_df[i[0]]

        cmd = [
            binary,
            merk_file,
            db,
            "kun",
            "{}".format(i[1])
            ]
        print(cmd)

        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True, env=scone_env)
        proc.wait()

        process_output(proc, kind, i[0], stats, cpu_hotplug)

def main():
    stats = defaultdict(list)
    setup_exp()

    benchmarks = {
        #"pure-host-non-secure": run_pure_host_ns,
        # "pure-host-secure": run_pure_host_sec,
        "pure-host-secure-sim": run_pure_host_sec_sim
    }

    storage_cpus = [1, 2, 4, 8]
    cpu_hotplug = os.environ["CPU_HOTPLUG"]

    for name, benchmark in benchmarks.items():
        if cpu_hotplug == "true":
            if name == "pure-host-secure-sim":
                print("Skipping {}".format(name))
                continue
            for i in storage_cpus:
                teardown_remote_cpu_hotplug(os.environ)
                benchmark(name, stats, i)
        else:
            teardown_remote_cpu_hotplug(os.environ)
            benchmark(name, stats, -1)


    df = pd.DataFrame(stats)
    sf = os.environ["SCALE_FACTOR"]
    # cpus = os.environ["CPU_BENCH"]
    if cpu_hotplug == "true":
        df.to_csv(f"pure_host_macrobench-hotplug-{sf}-{NOW}.csv", index=False)
    else:
        df.to_csv(f"pure_host_macrobench-{sf}-{NOW}.csv", index=False)

if __name__=="__main__":
    main()
