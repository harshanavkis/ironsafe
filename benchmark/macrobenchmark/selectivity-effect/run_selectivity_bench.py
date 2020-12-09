import sys
sys.path.append("../../")
import os
import subprocess
from collections import defaultdict
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
import time
from io import StringIO
import json
import pandas as pd

from selectivity_split import determine_split
from helpers import clear_cache

NOW = datetime.now().strftime("%Y%m%d-%H%M%S")

stdout=subprocess.PIPE

sql_query = "select l_returnflag, l_linestatus, sum(l_quantity) as sum_qty, sum(l_extendedprice) as sum_base_price, sum(l_extendedprice*(1 - l_discount)) as sum_disc_price, sum(l_extendedprice*(1 - l_discount)*(1 + l_tax)) as sum_charge, avg(l_quantity) as avg_qty, avg(l_extendedprice) as avg_price, avg(l_discount) as avg_disc, count(*) as count_order from LINEITEM where l_shipdate <= {} group by l_returnflag, l_linestatus order by l_returnflag, l_linestatus;"

host_query = "select l_returnflag, l_linestatus, sum(l_quantity) as sum_qty, sum(l_extendedprice) as sum_base_price, sum(l_extendedprice*(1 - l_discount)) as sum_disc_price, sum(l_extendedprice*(1 - l_discount)*(1 + l_tax)) as sum_charge, avg(l_quantity) as avg_qty, avg(l_extendedprice) as avg_price, avg(l_discount) as avg_disc, count(*) as count_order from TABLE1 group by l_returnflag, l_linestatus order by l_returnflag, l_linestatus;"

ssd_query = "select l_returnflag, l_linestatus,l_quantity, l_extendedprice, l_discount, l_tax from LINEITEM where l_shipdate <= '1998-08-15';"

device_host_query = "select l_returnflag, l_linestatus, sum_qty, sum_base_price, sum_disc_price, sum_charge, avg_qty, avg_price, avg_disc, count_order from TABLE1;"

device_ssd_query  = "select l_returnflag, l_linestatus, sum(l_quantity) as sum_qty, sum(l_extendedprice) as sum_base_price, sum(l_extendedprice*(1 - l_discount)) as sum_disc_price, sum(l_extendedprice*(1 - l_discount)*(1 + l_tax)) as sum_charge, avg(l_quantity) as avg_qty, avg(l_extendedprice) as avg_price, avg(l_discount) as avg_disc, count(*) as count_order from LINEITEM where l_shipdate {};"

ROOT_DIR = os.path.realpath("../../../")
CURR_DIR = os.path.realpath(".")
DB_DIR = os.path.realpath("../../../tpch/build/TPCH-{}.db")
REM_DB_NAME = "tpch/build/TPCH-{}.db"
NVME_TCP_DIR = ""
DB_FILE_NAME   = "TPCH-{}.db"
FRESH_DB_NAME  = "TPCH-{}-fresh-enc.db"
MERK_FILE_NAME = "merkle-tree-{}.bin"

"""
    Environment variables:
        - REMOTE_SRC
        - STORAGE_SERVER_IP
        - REMTOE_NIC_IP
        - REMOTE_USER
        - SCALE_FACTORS
        - SPLIT_POINTS
        - NVME_TCP_DIR
"""
def process_host_ndp_output(res):
    return res

def run_local_proc(cmd, env=None):
    proc = subprocess.run(cmd, stdout=stdout, env=env)
    return proc

def setup_exp():
    os.chdir(f"{ROOT_DIR}/host/non-secure/")
    cmd = ["make"]
    proc = run_local_proc(cmd)
    # proc.wait()

    os.chdir(f"{ROOT_DIR}/openssl-src/")
    cmd = ["./Configure"]
    proc = run_local_proc(cmd)
    # proc.wait()

    cmd = ["make"]
    proc = run_local_proc(cmd)
    # proc.wait()

    cmd = ["docker", "image", "inspect", "host-ndp:latest"]
    proc = run_local_proc(cmd)
    # proc.wait()

    os.chdir(ROOT_DIR)
    if proc.returncode == 1:
        cmd = ["docker", "build", "-f", f"{ROOT_DIR}/benchmark/scone-stuff/sec-ndp", "-t", "host-ndp", f"{ROOT_DIR}/"]
        run_local_proc(cmd)
        # proc.wait()

    cmd = ["docker", "image", "inspect", "pure-host-sec:latest"]
    proc = run_local_proc(cmd)
    # proc.wait()

    if proc.returncode == 1:
        cmd = ["docker", "build", "-f", f"{ROOT_DIR}/benchmark/scone-stuff/pure-host-sec", "-t", "pure-host-sec", f"{ROOT_DIR}/"]
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

    # TODO: Correctly setup nvme over tcp and mount drive
    NVME_TCP_DIR = os.path.join(ROOT_DIR, "tpch/build")

    os.chdir(CURR_DIR)

def process_pure_host_output(proc_stdout):
    try:
        data = json.loads(proc_stdout.rstrip())
        print(data)
        return data["query_exec_time"]
    except Exception as e:
        print("Unable to decode json...")
        sys.exit(1)

def run_pure_host_non_secure(cq, db_file, scale_factor):
    try:
        data_dir = os.environ["NVME_TCP_DIR"]
    except Exception as e:
        print("Provide NVME_TCP_DIR env var")
        sys.exit(1)

    cmd = [
        "docker",
        "run",
        "--mount",
        f"type=bind,source={data_dir},target=/data",
        "pure-host",
        "/bin/bash",
        "-c",
        "./hello-query {} {} \"\" \"{}\"".format(os.path.join("/data", MERK_FILE_NAME.format(scale_factor)), os.path.join("/data", DB_FILE_NAME.format(scale_factor)), cq.replace("'", "'\\''"))
    ]

    print(cmd)

    proc = subprocess.run(cmd, stdout=stdout, text=True)
    return process_pure_host_output(proc.stdout)

def run_pure_host_secure(cq, db_file, scale_factor):
    try:
        data_dir = os.environ["NVME_TCP_DIR"]
    except Exception as e:
        print("Provide NVME_TCP_DIR env var")
        sys.exit(1)

    cmd = [
        "docker",
        "run",
        "--mount",
        f"type=bind,source={data_dir},target=/data",
        "pure-host-sec",
        "/bin/bash",
        "-c",
        "SCONE_VERSION=1 SCONE_HEAP=4G ./hello-query {} {} kun \"{}\"".format(os.path.join("/data", MERK_FILE_NAME.format(scale_factor)), os.path.join("/data", FRESH_DB_NAME.format(scale_factor)), cq.replace("'", "'\\''"))
    ]
    print(cmd)

    proc = subprocess.run(cmd, stdout=stdout, text=True)
    return process_pure_host_output(proc.stdout.rstrip())

def run_vanilla_ndp_non_secure(hq, sq, db_file, scale_factor):
    env_var = os.environ.copy()
    env_var["CONN_TYPE"] = "non-secure"
    env_var["OFFLOAD_TYPE"] = "split-comp"
    env_var["DATE"] = f"{NOW}"
    env_var["SCALE_FACTOR"] = str(scale_factor)
    
    init_cmd = [
        '../run_macrobench_host.sh'
    ]
    storage_proc = subprocess.Popen(init_cmd, env=env_var)
    storage_proc.wait()
    time.sleep(10)

    rem_ip   = os.environ["REMOTE_NIC_IP"]
    local_cmd = [
        "docker",
        "run",
        "vanilla-ndp",
        "/bin/bash",
        "-c",
        "./host-ndp -D dummy -Q \"{}\" -S \"{}\" {}".format(hq.replace("'", "'\\''"), sq.replace("'", "'\\''"), os.environ["REMOTE_NIC_IP"])
    ]

    local_proc = subprocess.Popen(local_cmd, stdout=subprocess.PIPE, env=env_var, text=True, stderr=subprocess.PIPE)
    while True:
            local_proc.wait()
            if local_proc.returncode !=0:
                continue
            else:
                break
    query_res = local_proc.stdout.read().strip().split(',')

    return float(query_res[0].strip())


def run_secure_ndp_secure(hq, sq, scale_factor):
    env_var = os.environ.copy()
    env_var["CONN_TYPE"] = "secure"
    env_var["OFFLOAD_TYPE"] = "split-comp"
    env_var["DATE"] = NOW
    env_var["SCALE_FACTOR"] = str(scale_factor)

    init_cmd = [
        '../run_macrobench_host.sh'
    ]
    storage_proc = subprocess.Popen(init_cmd, stdout=subprocess.PIPE, env=env_var)
    storage_proc.wait()

    time.sleep(10)

    local_cmd = [
        "docker",
        "run",
        "--device=/dev/isgx",
        "host-ndp",
        "/bin/bash",
        "-c",
        "SCONE_VERSION=1 SCONE_HEAP=4G ./host-ndp -D dummy -Q \"{}\" -S \"{}\" {}".format(hq.replace("'", "'\\''"), sq.replace("'", "'\\''"), os.environ["REMOTE_NIC_IP"])
    ]

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

    return float(query_res[0].strip())

def run_secure_device_only(cq, scale_factor):
    rem_src = os.environ["REMOTE_SRC"]
    rem_user = os.environ["REMOTE_USER"]

    remote_ip = os.environ["STORAGE_SERVER_IP"]
    if remote_ip == "127.0.0.1":
        remote_ip = "172.17.0.1"

    merk_file = os.path.join(rem_src, f"tpch/build/merkle-tree-{scale_factor}.bin")
    db_file   = os.path.join(rem_src, f"tpch/build/TPCH-{scale_factor}-fresh-enc.db")

    rem_cmd = [
        os.path.join(rem_src, "fresh-sqlite/run_query.sh"),
        merk_file,
        db_file,
        "kun"
    ]

    rem_cmd = " ".join(rem_cmd)

    ssh_cmd = ["ssh", f"{rem_user}@{remote_ip}", f"{rem_cmd} \"{cq}\""]
    print(ssh_cmd)
    proc = subprocess.Popen(ssh_cmd, stdout=subprocess.PIPE, text=True)
    proc.wait()

    return process_pure_host_output(proc.stdout.read())

def run_all_configs(cq, hq, sq, dhq, dsq, db_file, scale_factor, split_point, split_date, stats):
    print("Running pure host non-secure...")
    phns = run_pure_host_non_secure(cq, db_file, scale_factor)
    stats["system"].append("phns")
    stats["time"].append(phns)
    stats["scale_factor"].append(scale_factor)
    stats["split_point"].append(split_point)
    stats["split_date"].append(split_date)

    print("Running pure host secure...")
    phs  = run_pure_host_secure(cq, db_file, scale_factor)
    stats["system"].append("phs")
    stats["time"].append(phs)
    stats["scale_factor"].append(scale_factor)
    stats["split_point"].append(split_point)
    stats["split_date"].append(split_date)

    print("Running vanilla ndp non-secure...")
    vnns = run_vanilla_ndp_non_secure(hq, sq, db_file, scale_factor)
    stats["system"].append("vnns")
    stats["time"].append(vnns)
    stats["scale_factor"].append(scale_factor)
    stats["split_point"].append(split_point)
    stats["split_date"].append(split_date)

    print("Running secure ndp...")
    sns  = run_secure_ndp_secure(hq, sq, scale_factor)
    stats["system"].append("sns")
    stats["time"].append(sns)
    stats["scale_factor"].append(scale_factor)
    stats["split_point"].append(split_point)
    stats["split_date"].append(split_date)

    print("Running purely on storage server...")
    sss  = run_secure_device_only(cq, scale_factor)
    stats["system"].append("sss")
    stats["time"].append(sss)
    stats["scale_factor"].append(scale_factor)
    stats["split_point"].append(split_point)
    stats["split_date"].append(split_date)
    import pdb; pdb.set_trace()

def run_bench(scale_factor, split_point, stats):
    db_file = DB_DIR.format(scale_factor)
    if not os.path.isfile(db_file):
        print(f"{db_file} does not exist")
        return

    # split_point*total_rows < split_date
    split_date = determine_split(db_file, split_point, "L_SHIPDATE")
    #split_date = "1995-06-17"

    upper_sel  = split_point

    run_all_configs(
        sql_query.format("\'{}\'".format(split_date)),
        host_query,
        ssd_query.format("{}".format(split_date)),
        device_host_query,
        device_ssd_query.format("{}".format(split_date)),
        db_file,
        scale_factor,
        split_point,
        split_date,
        stats
    )

def main():
    scale_factors = os.environ['SCALE_FACTORS']
    split_points  = os.environ['SPLIT_POINTS']

    if not scale_factors:
        print("Provide SCALE_FACTORS env var")
        sys.exit(1)
    if not split_points:
        print("Provide SPLIT_POINTS env var")

    scale_factors = scale_factors.split(" ")
    scale_factors = [int(i) for i in scale_factors]

    split_points  = split_points.split(" ")
    split_points  = [float(i) for i in split_points]

    # setup_exp()

    stats = defaultdict(list)

    for sf in scale_factors:
        for sp in split_points:
            run_bench(sf, sp, stats)

    import pdb; pdb.set_trace()
    df = pd.DataFrame(stats)
    df.to_csv(f"selectivity-effect-bench-{NOW}.csv", index=False)


if __name__=="__main__":
    main()
