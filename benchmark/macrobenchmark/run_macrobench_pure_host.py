import subprocess
import json
import os
from collections import defaultdict
import sys
import pandas as pd
from process_sql import process_sql

"""
    Environment variables:
        - NVME_TCP_DIR
        - SCALE_FACTOR
"""

ROOT_DIR = os.path.realpath("../../")
CURR_DIR = os.path.realpath(".")

MERK_FILE = "merkle-tree-{}.bin"

SQL_FILE    = os.path.join(ROOT_DIR, "tpch/tpc_h_queries.sql")
OUT_FILE    = "queries.csv"
RUN_TYPE    = "dummy"
NUM_QUERIES = 22

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

def process_output(proc, kind, query_no, stats):
    for line in proc.stdout:
        try:
            data = json.loads(line.rstrip())
            stats["kind"].append(kind)
            stats["query_no"].append(query_no)
            for i in data:
                stats[i].append(data[i])
        except Exception as e:
            continue

def run_pure_host_ns(kind, stats):
    df = pd.read_csv(OUT_FILE, sep="|", header=None)
    df = list(df[df.columns[:2]].values)

    try:
        scale_factor = float(os.environ["SCALE_FACTOR"])
    except Exception as e:
        print("Provide SCALE_FACTOR env var")
        sys.exit(1)

    try:
        data_dir = os.environ["NVME_TCP_DIR"]
    except Exception as e:
        print("Provide NVME_TCP_DIR env var")
        sys.exit(1)

    exe = os.path.join(ROOT_DIR, "benchmark/macrobenchmark/selectivity-effect/run_pure_host_non_secure.sh")
    db  = os.path.join(ROOT_DIR, f"{data_dir}/TPCH-{scale_factor}.db")
    merk_file = os.path.join(ROOT_DIR, f"{data_dir}/{MERK_FILE.format(scale_factor)}")

    for i in df:
        cmd = [
            exe,
            merk_file,
            db,
            f"{i[1]}"
        ]

        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True)
        proc.wait()

        process_output(proc, kind, i[0], stats)

def run_pure_host_sec(kind, stats):
    df = pd.read_csv(OUT_FILE, sep="|", header=None)
    df = list(df[df.columns[:2]].values)

    try:
        scale_factor = float(os.environ["SCALE_FACTOR"])
    except Exception as e:
        print("Provide SCALE_FACTOR env var")
        sys.exit(1)

    try:
        data_dir = os.environ["NVME_TCP_DIR"]
    except Exception as e:
        print("Provide NVME_TCP_DIR env var")
        sys.exit(1)

    db  = os.path.join("/data", f"TPCH-{scale_factor}-fresh-enc.db")
    merk_file = os.path.join("/data", f"{MERK_FILE.format(scale_factor)}")

    for i in df:
        cmd = [
        "docker",
        "run",
        "--mount",
        f"type=bind,source={data_dir},target=/data",
        "pure-host-sec",
        "/bin/bash",
        "-c",
        "SCONE_VERSION=1 SCONE_HEAP=2G ./hello-query {} {} kun \"{}\"".format(merk_file, db, i[1].replace("'", "'\\''"))
    ]

        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True)
        proc.wait()

        process_output(proc, kind, i[0], stats)

def main():
    stats = defaultdict(list)
    setup_exp()

    benchmarks = {
        "pure-host-non-secure": run_pure_host_ns,
        "pure-host-secure": run_pure_host_sec,
    }

    for name, benchmark in benchmarks.items():
        benchmark(name, stats)

    df = pd.DataFrame(stats)
    df.to_csv("pure_host_macrobench.csv", index=False)

if __name__=="__main__":
    main()