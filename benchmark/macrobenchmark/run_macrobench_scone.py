import subprocess
import json
import os
from collections import defaultdict
import sys
import pandas as pd
from process_sql import process_sql
from datetime import datetime
import time
from cpu_hotplug_helpers import setup_remote_cpu_hotplug, teardown_remote_cpu_hotplug

NOW = datetime.now().strftime("%Y%m%d-%H%M%S")

"""
    Environment variables:
        - STORAGE_SERVER_IP
        - REMOTE_NIC_IP
        - REMOTE_USER
        - SCALE_FACTOR
        - REMOTE_SRC
        - CPU_BENCH
"""

ROOT_DIR = os.path.realpath("../../")
CURR_DIR = os.path.realpath(".")
SEC_BIN_DIR = os.path.join(ROOT_DIR, "sec-bin")

MERK_FILE = "merkle-tree-{}.bin"

SQL_FILE         = os.path.join(ROOT_DIR, "tpch/tpc_h_queries_filter_proj.sql")
ALL_OFF_SQL_FILE = os.path.join(ROOT_DIR, "tpch/tpc_h_queries_all_offload.sql")
OUT_FILE         = "queries.csv"
RUN_TYPE         = "dummy"
NUM_QUERIES      = 22
CPUS = 0.4

ignore_queries = [1]

# SCALE_FACTOR=0.01 REMOTE_USER=hvub STORAGE_SERVER_IP=127.0.0.1 REMOTE_SRC=/home/hvub/vanilla-ndp/ python3.8 run_macrobench_scone.py

def run_local_proc(cmd, env=None):
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, env=env, text=True, stderr=subprocess.PIPE)
    return proc

def setup_exp():
    os.chdir(ROOT_DIR)
    cmd = ["docker", "image", "inspect", "host-ndp:latest"]
    proc = run_local_proc(cmd)

    if proc.returncode == 1:
        cmd = ["docker", "build", "-f", f"{ROOT_DIR}/benchmark/scone-stuff/sec-ndp", "-t", "host-ndp", f"{ROOT_DIR}/"]
        run_local_proc(cmd)

    cmd = ["docker", "image", "inspect", "vanilla-ndp:latest"]
    proc = run_local_proc(cmd)

    if proc.returncode == 1:
        cmd = ["docker", "build", "-f", f"{ROOT_DIR}/benchmark/scone-stuff/vanilla-ndp", "-t", "vanilla-ndp", f"{ROOT_DIR}/"]
        run_local_proc(cmd)

    os.chdir(os.path.join(ROOT_DIR, "host/non-secure"))
    cmd = ["make", "clean"]
    run_local_proc(cmd)
    cmd = ["make"]
    run_local_proc(cmd)

    os.chdir(CURR_DIR)

def check_env_var():
    try:
        temp = os.environ["STORAGE_SERVER_IP"]
    except Exception as e:
        print("STORAGE_SERVER_IP not provided")
        sys.exit(1)

    try:
        temp = os.environ["REMOTE_USER"]
    except Exception as e:
        print("REMOTE_USER not provided")
        sys.exit(1)

    try:
        temp = os.environ["SCALE_FACTOR"]
    except Exception as e:
        print("SCALE_FACTOR not provided")
        sys.exit(1)

    try:
        temp = os.environ["REMOTE_SRC"]
    except Exception as e:
        print("REMOTE_SRC not provided")
        sys.exit(1)

def kill_rem_process(parent, child):
    rem_user = os.environ["REMOTE_USER"]
    rem_ip   = os.environ["STORAGE_SERVER_IP"]
    rem_cmd = f"ssh {rem_user}@{rem_ip} \"kill -9 \\$(pgrep {parent})\""
    proc = subprocess.Popen(rem_cmd, shell=True)
    proc.wait()

    rem_cmd = f"ssh {rem_user}@{rem_ip} \"kill -9 \\$(pgrep {child})\""
    proc = subprocess.Popen(rem_cmd, shell=True)
    proc.wait()

def run_vanilla_ndp(name, stats, cpu_hotplug):
    process_sql(SQL_FILE, OUT_FILE, RUN_TYPE, NUM_QUERIES)

    if cpu_hotplug != -1:
        setup_remote_cpu_hotplug(cpu_hotplug, os.environ.copy())

    df = pd.read_csv(OUT_FILE, sep="|", header=None)
    df = list(df.drop(df.columns[1], axis=1).values)

    check_env_var()

    env_var = os.environ.copy()
    env_var["CONN_TYPE"] = "non-secure"
    env_var["OFFLOAD_TYPE"] = "split-comp"
    env_var["DATE"] = f"{NOW}"

    init_cmd = [
        './run_macrobench_host.sh'
    ]

    #cpu_df = pd.read_csv(sys.argv[1])
    #cpu_df = cpu_df.set_index("query").to_dict()
    #cpu_df = cpu_df["cpu"]

    for i in df:
        if i[0] in ignore_queries:
            continue
        storage_proc = subprocess.Popen(init_cmd, stdout=subprocess.PIPE, env=env_var)
        storage_proc.wait()

        time.sleep(10)

        rem_ip   = os.environ["REMOTE_NIC_IP"]
        cmd = ["sudo", "systemctl", "restart", "docker"]
        proc = subprocess.Popen(cmd)
        proc.wait()

        #cpus = cpu_df[i[0]]

        stats["kind"].append(name)
        stats["query"].append(i[0])
        print(i[0])

        local_cmd = [
            "docker",
            "run",
            #f"--cpus={CPUS}",
            #"--cpuset-cpus=0",
            "vanilla-ndp",
            "/bin/bash",
            "-c",
            "./host-ndp -D dummy -Q \"{}\" -S \"{}\" {}".format(i[1], i[2], os.environ["REMOTE_NIC_IP"])
        ]
        print(local_cmd)
        local_proc = subprocess.Popen(local_cmd, stdout=subprocess.PIPE, env=env_var, text=True, stderr=subprocess.PIPE)
        while True:
            local_proc.wait()
            if local_proc.returncode !=0:
                continue
            else:
                break

        query_res = local_proc.stdout.read().strip().split(',')
        # import pdb; pdb.set_trace()
        stats["total_time"].append(float(query_res[0].strip()))
        stats["total_host_query_time"].append(float(query_res[1].strip()))
        stats["cpus"].append("{}".format(cpu_hotplug))

        time.sleep(10)

    kill_rem_process("run_server", "ssd-ndp")

    teardown_remote_cpu_hotplug(os.environ)

def run_sec_ndp(name, stats, cpu_hotplug):
    process_sql(SQL_FILE, OUT_FILE, RUN_TYPE, NUM_QUERIES)

    if cpu_hotplug != -1:
        setup_remote_cpu_hotplug(cpu_hotplug, os.environ.copy())

    df = pd.read_csv(OUT_FILE, sep="|", header=None)
    df = list(df.drop(df.columns[1], axis=1).values)

    check_env_var()

    env_var = os.environ.copy()
    env_var["CONN_TYPE"] = "secure"
    env_var["OFFLOAD_TYPE"] = "split-comp"
    env_var["DATE"] = NOW

    init_cmd = [
        './run_macrobench_host.sh'
    ]

    #cpu_df = pd.read_csv(sys.argv[1])
    #cpu_df = cpu_df.set_index("query").to_dict()
    #cpu_df = cpu_df["cpu"]

    binary = os.path.join(SEC_BIN_DIR, "host-ndp")
    env_var["SCONE_VERSION"] = "1"
    env_var["SCONE_HEAP"] = "4G"

    for i in df:
        if i[0] in ignore_queries:
            continue
        storage_proc = subprocess.Popen(init_cmd, stdout=subprocess.PIPE, env=env_var)
        storage_proc.wait()

        time.sleep(10)

        #cmd = ["sudo", "systemctl", "restart", "docker"]
        #proc = subprocess.Popen(cmd)
        #proc.wait()

        #cpus = cpu_df[i[0]]

        stats["kind"].append(name)
        stats["query"].append(i[0])
        print(i[0])

        local_cmd = [
            binary,
            "-D",
            "dummy",
            "-Q",
            i[1],
            "-S",
            i[2],
            os.environ["REMOTE_NIC_IP"]
        ]
        print(local_cmd)
        # local_proc = run_local_proc(local_cmd, env=env_var)
        local_proc = subprocess.Popen(local_cmd, stdout=subprocess.PIPE, env=env_var, text=True)
        while True:
            local_proc.wait()
            #import pdb; pdb.set_trace()
            if local_proc.returncode !=0:
                #print(local_proc.returncode)
                continue
            else:
                break

        query_res = local_proc.stdout.read().strip().split(',')
        #import pdb; pdb.set_trace()
        stats["total_time"].append(float(query_res[0].strip()))
        stats["total_host_query_time"].append(float(query_res[1].strip()))
        stats["cpus"].append("{}".format(cpu_hotplug))

        time.sleep(10)

    kill_rem_process("run_server", "ssd-ndp")

    teardown_remote_cpu_hotplug(os.environ)

def run_sec_ndp_sim(name, stats, cpu_hotplug):
    process_sql(SQL_FILE, OUT_FILE, RUN_TYPE, NUM_QUERIES)

    df = pd.read_csv(OUT_FILE, sep="|", header=None)
    df = list(df.drop(df.columns[1], axis=1).values)

    check_env_var()

    env_var = os.environ.copy()
    env_var["CONN_TYPE"] = "secure"
    env_var["OFFLOAD_TYPE"] = "split-comp"
    env_var["DATE"] = NOW

    init_cmd = [
        './run_macrobench_host.sh'
    ]

    binary = os.path.join(SEC_BIN_DIR, "host-ndp")
    env_var["SCONE_VERSION"] = "1"
    env_var["SCONE_HEAP"] = "4G"
    env_var["SCONE_MODE"] = "SIM"

    for i in df:
        if i[0] in ignore_queries:
            continue
        storage_proc = subprocess.Popen(init_cmd, stdout=subprocess.PIPE, env=env_var)
        storage_proc.wait()

        time.sleep(10)

        stats["kind"].append(name)
        stats["query"].append(i[0])
        print(i[0])

        local_cmd = [
            binary,
            "-D",
            "dummy",
            "-Q",
            i[1],
            "-S",
            i[2],
            os.environ["REMOTE_NIC_IP"]
        ]
        print(local_cmd)
        # local_proc = run_local_proc(local_cmd, env=env_var)
        local_proc = subprocess.Popen(local_cmd, stdout=subprocess.PIPE, env=env_var, text=True)
        while True:
            local_proc.wait()
            #import pdb; pdb.set_trace()
            if local_proc.returncode !=0:
                #print(local_proc.returncode)
                continue
            else:
                break

        query_res = local_proc.stdout.read().strip().split(',')
        #import pdb; pdb.set_trace()
        stats["total_time"].append(float(query_res[0].strip()))
        stats["total_host_query_time"].append(float(query_res[1].strip()))
        stats["cpus"].append("{}".format(cpu_hotplug))

        time.sleep(10)

    kill_rem_process("run_server", "ssd-ndp")

def run_all_offload(name, stats, cpu_hotplug):
    process_sql(ALL_OFF_SQL_FILE, OUT_FILE, RUN_TYPE, NUM_QUERIES)

    df = pd.read_csv(OUT_FILE, sep="|", header=None)
    df = list(df.drop(df.columns[1], axis=1).values)

    check_env_var()

    env_var = os.environ.copy()
    env_var["CONN_TYPE"] = "secure"
    env_var["OFFLOAD_TYPE"] = "all-offload"
    env_var["DATE"] = NOW

    init_cmd = [
        './run_macrobench_host.sh'
    ]

    for i in df:
        if i[0] != 4:
            continue
        print(i[0])
        storage_proc = subprocess.Popen(init_cmd, stdout=subprocess.PIPE, env=env_var)
        storage_proc.wait()

        time.sleep(10)

        stats["kind"].append(name)
        stats["query"].append(i[0])

        local_cmd = [
            "docker",
            "run",
            # "--device=/dev/isgx",
            "host-ndp",
            "/bin/bash",
            "-c",
            "SCONE_VERSION=1 SCONE_HEAP=4G SCONE_STACK=8M ./host-ndp -D dummy -Q \"{}\" -S \"{}\" {}".format(i[1], i[2], os.environ["REMOTE_NIC_IP"])
        ]
        # local_proc = run_local_proc(local_cmd, env=env_var)
        local_proc = subprocess.Popen(local_cmd, stdout=subprocess.PIPE, env=env_var, text=True)
        while True:
            local_proc.wait()
            #import pdb; pdb.set_trace()
            if local_proc.returncode !=0:
                #print(local_proc.returncode)
                continue
            else:
                break

        query_res = local_proc.stdout.read().strip().split(',')
        #import pdb; pdb.set_trace()
        stats["total_time"].append(float(query_res[0].strip()))
        stats["total_host_query_time"].append(float(query_res[1].strip()))
        stats["cpus"].append("{}".format(cpu_hotplug))

        time.sleep(10)


    kill_rem_process("run_server", "ssd-ndp")

def main():
    stats = defaultdict(list)
    setup_exp()

    benchmarks = {
        "vanilla-ndp": run_vanilla_ndp,
        "sec-ndp": run_sec_ndp,
        #"all-offload": run_all_offload
        #"sec-ndp-sim": run_sec_ndp_sim,
    }

    storage_cpus = [1, 2, 4, 8]
    cpu_hotplug = os.environ["CPU_HOTPLUG"]

    for name, benchmark in benchmarks.items():
        if cpu_hotplug == "true":
            if name == "sec-ndp-sim" or name == "all-offload":
                print(name)
                continue
            for i in storage_cpus:
                teardown_remote_cpu_hotplug(os.environ)
                benchmark(name, stats, i)
        else:
            teardown_remote_cpu_hotplug(os.environ)
            benchmark(name, stats, -1)

    # for name, benchmark in benchmarks.items():
    #     benchmark(name, stats)

    df = pd.DataFrame(stats)
    scale = os.environ["SCALE_FACTOR"]
    #cpus = os.environ["CPU_BENCH"]
    if cpu_hotplug == "true":
        df.to_csv(f"ndp_macrobench-hotplug-{scale}-{NOW}.csv", index=False)
    else:
        df.to_csv(f"ndp_macrobench-{scale}-{NOW}.csv", index=False)

if __name__=="__main__":
    main()
