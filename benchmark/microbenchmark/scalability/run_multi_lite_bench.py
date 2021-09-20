import os
from posixpath import realpath
import sys
sys.path.append("../../macrobenchmark/")
sys.path.append("../../")
import subprocess
from datetime import datetime
import pandas as pd
from shutil import copyfile
from process_sql import process_sql
from helpers import clear_cache

NOW = datetime.now().strftime("%Y%m%d-%H%M%S")
ROOT_DIR = os.path.realpath("../../../")
SQL_FILE         = os.path.join(ROOT_DIR, "tpch/tpc_h_queries_filter_proj.sql")
OUT_FILE         = "queries.csv"
RUN_TYPE         = "dummy"
NUM_QUERIES      = 22

def setup_exp(kind, scale_factor, db_dir, instances):
    subprocess.run(["make"], stdout=subprocess.PIPE)

    if int(scale_factor) == scale_factor:
        scale_factor = int(scale_factor)

    # TODO: Is flushing necessary?
    for i in range(instances):
        if kind == "secure":
            copyfile(os.path.join(os.path.realpath(db_dir), "merkle-tree-{}.bin".format(scale_factor)), os.path.join(os.path.realpath(db_dir), "merkle-tree-{}-{}.bin".format(scale_factor, i+1)))
            copyfile(os.path.join(os.path.realpath(db_dir), "TPCH-{}-fresh-enc.db".format(scale_factor)), os.path.join(os.path.realpath(db_dir), "TPCH-{}-fresh-enc-{}.db".format(scale_factor, i+1)))
        else:
            copyfile(os.path.join(os.path.realpath(db_dir), "TPCH-{}.db".format(scale_factor)), os.path.join(os.path.realpath(db_dir), "TPCH-{}-{}.db".format(scale_factor, i+1)))

    process_sql(SQL_FILE, OUT_FILE, RUN_TYPE, NUM_QUERIES)
    print("process sql done")

def run_exp(kind, scale_factor, db_dir, instances, query, query_num, res_df):
    if int(scale_factor) == scale_factor:
        scale_factor = int(scale_factor)
    
    cmd = [os.path.join(os.path.realpath("."), "multi-sqlite"), "{}".format(kind), "{}".format(scale_factor), "{}".format(os.path.realpath(db_dir)), "{}".format(query), "{}".format(instances), "kun"]

    print(cmd)

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True, stderr=subprocess.PIPE)
    proc.wait()

    # print(proc.stdout.read())

    res = proc.stdout.read().strip()
    print(res)
    res = res.split("\n")
    res = [i.split(",") for i in res]

    for i in res:
        res_df.append([query_num]+i)

    # print(res)


def main():
    kind = sys.argv[1]
    scale_factor = float(sys.argv[2])
    db_dir = sys.argv[3]
    instances = int(sys.argv[4])
    query = sys.argv[5]

    setup_exp(kind, scale_factor, db_dir, instances)

    df = pd.read_csv(OUT_FILE, sep="|", header=None)
    df = list(df[df.columns[:2]].values)

    res_df = []

    for i in df:
        run_exp(kind, scale_factor, db_dir, instances, i[1], i[0], res_df)
        clear_cache()
    
    # print(res_df)

    res_df = pd.DataFrame(res_df)
    res_df.columns = ["query", "worker id", "time [s]"]
    print(res_df)

    res_df.to_csv("multi_sqlite_{}_{}_{}.csv".format(scale_factor, kind, NOW), index=False)

if __name__=="__main__":
    main()