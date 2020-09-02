import subprocess
import os
import sys
from collections import defaultdict
import pandas as pd
import signal
import re

ROOT_DIR = os.path.realpath("../../../")
CURR_DIR = os.path.realpath(".")

def run_local_proc(cmd, env=None):
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, env=env)
    return proc

def setup_exp():
    os.chdir(os.path.join(ROOT_DIR, "sqlite-speedtest"))
    cmd = ["./configure"]
    proc = run_local_proc(cmd)
    cmd = ["make", "speedtest1"]
    proc = run_local_proc(cmd)

    os.chdir(ROOT_DIR)
    cmd = ["docker", "image", "inspect", "sqlite-speedtest:latest"]
    proc = run_local_proc(cmd)
    if proc.returncode != 0:
        cmd = ["docker", "build", "-f", f"{ROOT_DIR}/benchmark/scone-stuff/sqlite-speedtest", "-t", "sqlite-speedtest", f"{ROOT_DIR}/"]
        proc = run_local_proc(cmd)

    os.chdir(CURR_DIR)

def process_speedtest_output(proc, kind, stats):
    stats["kind"].append(kind)
    n_rows = 0
    try:
        if proc.stdout is None:
            proc.wait()
        else:
            for line in proc.stdout:
                line = line.rstrip()
                print(line)
                match = re.match(r"(?: \d+ - |\s+)([^.]+)[.]+\s+([0-9.]+)s", line)
                if match:
                    stats[match.group(1)].append(match.group(2))
                    n_rows += 1
    finally:
        proc.send_signal(signal.SIGINT)

    expected = 33
    if n_rows != expected:
        raise RuntimeError(f"Expected {expected} rows, got: {n_rows} when running benchmark for {kind}")

def run_sqlite_speedtest_native(row_scale, kind, stats):
    cmd = [
        os.path.join(ROOT_DIR, "sqlite-speedtest/speedtest1"),
        f"{row_scale}",
        ":memory:"
    ]

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True)
    process_speedtest_output(proc, kind, stats)

def run_sqlite_speedtest_sgx(row_scale, kind, stats):
    cmd = [
        "docker",
        "run",
        "sqlite-speedtest",
        "/bin/bash",
        "-c",
        f"SCONE_VERSION=1 SCONE_HEAP=2G ./speedtest1 {row_scale} :memory:"
    ]

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True)
    process_speedtest_output(proc, kind, stats)

def main():
    row_scale = int(sys.argv[1])
    stats = defaultdict(list)
    setup_exp()

    benchmarks = {
        "native-sqlite-speedtest": run_sqlite_speedtest_native,
        "sgx-sqlite-speedtest": run_sqlite_speedtest_sgx
    }

    for name, benchmark in benchmarks.items():
        benchmark(row_scale, name, stats)

    csv = f"sqlite-speedtest-tee-{row_scale}.csv"
    df = pd.DataFrame(stats)
    df.to_csv(csv, index=False)

if __name__=="__main__":
    main()