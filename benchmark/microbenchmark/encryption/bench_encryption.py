import sys
import subprocess
import os
from pathlib import Path
from shutil import copyfile
from collections import defaultdict
from datetime import datetime
import json
import pandas as pd
import math

NOW = datetime.now().strftime("%Y%m%d-%H%M%S")

SRC_DIR = os.path.realpath("../../../")
CURR_DIR = os.path.realpath(".")
TPCH_DATA_DIR = os.path.join(SRC_DIR, "tpch/build/")

DB_FILE_NAME   = "TPCH-{}.db"
FRESH_DB_NAME  = "TPCH-{}-fresh-enc.db"
MERK_FILE_NAME = "merkle-tree-{}.bin"
ENC_IMAGE_NAME = "TPCH-DM-CRYPT-{}.img"
KEYFILE        = "DM-CRYPT-KEY-{}.keyfile"

TEST_QUERY = "select * from lineitem;"

"""
    Environment variables:
        - SCALE_FACTOR
"""

def run_local_proc(cmd):
    proc = subprocess.run(cmd, stdout=stdout)
    return proc

def setup_stuff():
    try:
        scale_factor = float(os.environ["SCALE_FACTOR"])
    except Exception as e:
        print("SCALE_FACTOR should be a number, preferably a float")
        sys.exit(1)

    db_file = Path(os.path.join(TPCH_DATA_DIR, DB_FILE_NAME.format(scale_factor)))
    if not db_file.is_file():
        os.chdir(f"{SRC_DIR}/tpch")
        cmd = ["./create_db.sh", f"{scale_factor}"]
        proc = run_local_proc(cmd)
        proc.wait()

    img_file = Path(os.path.join(TPCH_DATA_DIR, ENC_IMAGE_NAME.format(scale_factor)))
    if not img_file.is_file():
        img_size = math.ceil(scale_factor*1.2*1.5) 
        subprocess.run(
                [
                    "fallocate",
                    "-l",
                    f"{img_size}G",
                    f"{str(img_file)}"
                ]
            )

        subprocess.run(
                [
                    "dd",
                    "if=/dev/urandom",
                    f"of={os.path.join(TPCH_DATA_DIR, KEYFILE.format(scale_factor))}",
                    "bs=1024",
                    "count=1"
                ]
            )

        subprocess.run(
                [
                    "sudo",
                    "cryptsetup",
                    "luksFormat",
                    f"{str(img_file)}",
                    f"{os.path.join(TPCH_DATA_DIR, KEYFILE.format(scale_factor))}"
                ],
                input="YES",
                encoding="ascii"
            )

        subprocess.run(
                [
                    "sudo",
                    "cryptsetup",
                    "luksOpen",
                    f"{str(img_file)}",
                    "benchEncryptVol",
                    "--key-file",
                    f"{os.path.join(TPCH_DATA_DIR, KEYFILE.format(scale_factor))}"
                ]
            )

        subprocess.run(["sudo", "mkfs.ext4", "/dev/mapper/benchEncryptVol"])
        subprocess.run(["sudo", "mount", "/dev/mapper/benchEncryptVol", "/mnt"])
        # subprocess.run(["sudo", "chown", "-R", "$USER", "/mnt"])

        copyfile(db_file, os.path.join("/mnt", DB_FILE_NAME.format(scale_factor)))

        subprocess.run(["sudo", "umount", "/mnt"])
        subprocess.run(["sudo", "cryptsetup", "luksClose", "benchEncryptVol"])

    os.chdir(os.path.join(SRC_DIR, "fresh-sqlite"))
    fresh_lite_env = os.environ.copy()
    openssl_src = os.path.join(SRC_DIR, "openssl-src")
    if not Path(os.path.join(openssl_src, "libcrypto.so.3")).is_file():
        os.chdir(openssl_src)
        subprocess.run(["./config"])
        subprocess.run(["make"])
        os.chdir(os.path.join(SRC_DIR, "fresh-sqlite"))

    fresh_lite_env["OPENSSL_SRC"] = os.path.join(SRC_DIR, "openssl-src")
    subprocess.run(["make", "hello-query"], env=fresh_lite_env)

    os.chdir(CURR_DIR)

def process_enc_bench_out(kind, stats, proc_out):
    stats["kind"].append(kind)
    for line in proc_out:
        try:
            data = json.loads(line)
            for i in data:
                stats[i].append(data[i])
        except Exception as e:
            print(f"{line}: not in JSON format")

def bench_dm_crypt(kind, stats):
    scale_factor = float(os.environ["SCALE_FACTOR"])
    subprocess.run(
                [
                    "sudo",
                    "cryptsetup",
                    "luksOpen",
                    f"{os.path.join(TPCH_DATA_DIR, ENC_IMAGE_NAME.format(scale_factor))}",
                    "benchEncryptVol",
                    "--key-file",
                    f"{os.path.join(TPCH_DATA_DIR, KEYFILE.format(scale_factor))}"
                ]
            )

    subprocess.run(["sudo", "mount", "/dev/mapper/benchEncryptVol", "/mnt"])

    proc = subprocess.Popen(
            [
                os.path.join(SRC_DIR, "fresh-sqlite/hello-query"),
                os.path.join(TPCH_DATA_DIR, MERK_FILE_NAME.format(scale_factor)),
                os.path.join("/mnt", DB_FILE_NAME.format(scale_factor)),
                "",
                TEST_QUERY
            ],
            stdout=subprocess.PIPE,
            text=True
        )

    proc.wait()

    subprocess.run(["sudo", "umount", "/mnt"])
    subprocess.run(["sudo", "cryptsetup", "luksClose", "benchEncryptVol"])

    process_enc_bench_out(kind, stats, proc.stdout)

def bench_fresh_crypt(kind, stats):
    scale_factor = float(os.environ["SCALE_FACTOR"])
    proc = subprocess.Popen(
            [
                os.path.join(SRC_DIR, "fresh-sqlite/hello-query"),
                os.path.join(TPCH_DATA_DIR, MERK_FILE_NAME.format(scale_factor)),
                os.path.join(TPCH_DATA_DIR, FRESH_DB_NAME.format(scale_factor)),
                "kun",
                TEST_QUERY,
            ],
            stdout=subprocess.PIPE,
            text=True
        )

    process_enc_bench_out(kind, stats, proc.stdout)

def main():
    stats = defaultdict(list)

    setup_stuff()

    benchmarks = {
        "dm-crypt": bench_dm_crypt,
        "fresh-crypt": bench_fresh_crypt,
    }

    for name, benchmark in benchmarks.items():
        print(f"Running benchmark for {name}")
        benchmark(name, stats)

    csv = f"encrypt-bench-{NOW}.csv"
    print(csv)

    df = pd.DataFrame(stats)
    df.to_csv(csv, index=False)
    df.to_csv("encrypt-bench-latest.csv", index=False)

if __name__=="__main__":
    main()