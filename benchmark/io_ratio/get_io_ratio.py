# select name, sum(pgsize) as size from dbstat group by name order by size desc;
import sys
import os
import pandas as pd
import subprocess
from datetime import datetime
import re

NOW = datetime.now().strftime("%Y%m%d-%H%M%S")

ROOT_DIR = os.path.realpath("../../")
CURR_DIR = os.path.realpath(".")

sys.path.append(os.path.join(ROOT_DIR, "benchmark/macrobenchmark"))
from process_sql import process_sql

SQL_FILE    = os.path.join(ROOT_DIR, "tpch/tpc_h_queries.sql")
OUT_FILE    = "queries.csv"
RUN_TYPE    = "dummy"
NUM_QUERIES = 22

TABLE_LIST = ["LINEITEM", "ORDERS", "PARTSUPP", "CUSTOMER", "PART", "SUPPLIER", "NATION", "REGION"]

def get_tables(query):
    table_set = set()

    for i in TABLE_LIST:
        if i in query:
            table_set.add(i)
    
    return list(table_set)

def bytes_per_query(query_tab, database):
    dbstat_query = "select sum(pgsize) from dbstat where name='{}';"
    total_bytes = 0

    for i in query_tab:
        proc = subprocess.run(["sqlite3", database, dbstat_query.format(i)], stdout=subprocess.PIPE)
        total_bytes += int(proc.stdout)
    
    return total_bytes


def main():
    ndp_packets = sys.argv[1] # secndp storage side csv
    pure_host   = sys.argv[2] # pure host secure csv
    database    = sys.argv[3]

    ndp_packets = pd.read_csv(ndp_packets, header=None, sep=",")
    pure_host = pd.read_csv(pure_host, header=0, sep=",")

    query_no = list(pure_host["query_no"])

    ndp_packets_t = list(ndp_packets[ndp_packets.columns[6]])
    query_bytes = list(pure_host[pure_host.columns[-1]])
    query_bytes = [i*4*1024 for i in query_bytes]
    ndp_disk_io = list(ndp_packets[ndp_packets.columns[5]].values)
    for i in range(len(ndp_packets)):
        ndp_packets_t[i] = ndp_packets_t[i]*1024*1024 + (ndp_disk_io[i] * 4 * 1024)
    io_ratio = []
    # import pdb; pdb.set_trace()
    ndp_packets = []
    ndp_packets = ndp_packets_t

    # process_sql(SQL_FILE, OUT_FILE, RUN_TYPE, NUM_QUERIES)
    # queries = pd.read_csv(OUT_FILE, header=None, sep='|')
    # queries_sql = list(queries[queries.columns[1]])
    # tables_per_query = []
    
    # for q in queries_sql:
    #     tables = get_tables(q)
    #     tables_per_query.append(tables)

    # query_bytes = []    
    # for t in tables_per_query:
    #     print(t)
    #     qb = bytes_per_query(t, database)
    #     print(qb)
    #     query_bytes.append(qb)

    for (i, j) in zip(query_bytes, ndp_packets):
        io_ratio.append(float(i)/(float(j)))

    io_ratio_cols = ["pure host bytes", "ndp bytes", "I/O Ratio", "Query"]
    io_ratio_df = pd.DataFrame(columns=io_ratio_cols)

    # import pdb; pdb.set_trace()
    # del query_bytes[0]

    io_ratio_df[io_ratio_cols[0]] = query_bytes
    io_ratio_df[io_ratio_cols[1]] = ndp_packets
    io_ratio_df[io_ratio_cols[2]] = io_ratio
    io_ratio_df[io_ratio_cols[3]] = query_no

    io_ratio_df.to_csv("io_ratio.csv", header=True, index=False)



if __name__ == "__main__":
    main()