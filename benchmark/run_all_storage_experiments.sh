#!/usr/bin/env bash

# This is run directly on the storage server
# Make sure there are no csv files in the directories before running this script

ROOT_DIR=$(realpath ../)
CUR_DIR=$(realpath .)

DB_DIR=$NVME_TCP_DIR
SCALE_FACTOR=3

cd $CUR_DIR/microbenchmark/scalability

# Run scalability experiments
for i in 1 2 4 8 16
do
    python3 run_multi_lite_bench.py "secure" $SCALE_FACTOR $DB_DIR $i -1
done

# Run memory limit experiment
sudo python3 run_sqlite_mem_limit_cgroup.py "secure" $SCALE_FACTOR 134217728 268435456 536870912 1073741824 2147483648

cd $CUR_DIR
