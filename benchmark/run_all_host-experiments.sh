#!/usr/bin/env bash

ROOT_DIR=$(realpath ../)
CUR_DIR=$(realpath .)

NVME_TCP_DIR=$NVME_TCP_DIR
SCALE_FACTOR=$SCALE_FACTOR
REMOTE_USER=$REMOTE_USER
STORAGE_SERVER_IP=$STORAGE_SERVER_IP
REMOTE_NIC_IP=$REMOTE_NIC_IP
REMOTE_SRC=$REMOTE_SRC
SCALE_FACTORS=$SCALE_FACTORS
SPLIT_POINTS=$SPLIT_POINTS

export NVME_TCP_DIR SCALE_FACTOR REMOTE_USER STORAGE_SERVER_IP REMOTE_NIC_IP REMOTE_SRC SCALE_FACTORS SPLIT_POINTS

cd $CUR_DIR/macrobenchmark

export CPU_HOTPLUG=false
python3 run_macrobench_pure_host.py
PURE_HOST_DATE=$(cat date_info)

export CPU_HOTPLUG=false
python3 run_macrobench_scone.py
NDP_DATE=$(cat date_info)

# CPU hotplug experiment: Pure host
export CPU_HOTPLUG=true
python3 run_macrobench_pure_host.py
PURE_HOST_HOTPLUG_DATE=$(cat date_info)

# CPU hotplug erxperiment: NDP
export CPU_HOTPLUG=true
python3 run_macrobench_scone.py
NDP_HOTPLUG_DATE=$(cat date_info)

cd $CUR_DIR

cd $ROOT_DIR/policy-compiler

# Policy benchmarks
./run_logging_exp.sh 5
LOGGING_EXP_DATE=$(cat date_info)
./run_policy_exp.sh 5 secure
POLICY_EXP_SECURE_DATE=$(cat date_info)
./run_policy_exp.sh 5 non-secure
POLICY_EXP_NON_SECURE_DATE=$(cat date_info)

# Selectivity benchmarks
cd $CUR_DIR/macrobenchmark/selectivity-effect
python3 run_selectivity_bench.py
SEL_EXP_DATE=$(cat date_info)

# Copy over data for plotting
cd $ROOT_DIR

# Macrobench host-side data
cp $ROOT_DIR/benchmark/macrobenchmark/pure_host_macrobench-${SCALE_FACTOR}-${PURE_HOST_DATE}.csv $ROOT_DIR/plots/pure_host_macrobench.csv
cp $ROOT_DIR/benchmark/macrobenchmark/pure_host_macrobench-hotplug-${SCALE_FACTOR}-${PURE_HOST_HOTPLUG_DATE}.csv $ROOT_DIR/plots/pure_host_macrobench_hotplug.csv
cp $ROOT_DIR/benchmark/macrobenchmark/ndp_macrobench-${SCALE_FACTOR}-${NDP_DATE}.csv $ROOT_DIR/plots/ndp_macrobench.csv
cp $ROOT_DIR/benchmark/macrobenchmark/ndp_macrobench-hotplug-${SCALE_FACTOR}-${NDP_HOTPLUG_DATE}.csv $ROOT_DIR/plots/ndp_macrobench_hotplug.csv

# Macrobench storage-side data
scp $REMOTE_USER:$STORAGE_SERVER_IP:$REMOTE_SRC/storage/non-secure/ssd-non-secure-split-comp-output-${NDP_DATE}.csv $ROOT_DIR/plots/ndp_storage_non_secure.csv
scp $REMOTE_USER:$STORAGE_SERVER_IP:$REMOTE_SRC/storage/secure/ssd-secure-split-comp-output-${NDP_DATE}.csv $ROOT_DIR/plots/ndp_storage_secure.csv

# Selectivity benchmarks data
cp $ROOT_DIR/benchmark/macrobenchmark/selectivity-effect/selectivity-effect-bench-${SEL_EXP_DATE}.csv $ROOT_DIR/plots/selectivity_bench.csv

# Storage side experimental data
scp $REMOTE_USER:$STORAGE_SERVER_IP:$REMOTE_SRC/benchmark/microbenchmark/scalability/multi_sqlite_${SCALE_FACTOR}_secure_*.csv $ROOT_DIR/plots/
scp $REMOTE_USER:$STORAGE_SERVER_IP:$REMOTE_SRC/benchmark/microbenchmark/scalability/sqlite_mem_limit_cgroup*.csv $ROOT_DIR/plots/sqlite_mem_limit_cgroup.csv

# Generate plots
cd $ROOT_DIR/plots
mkdir -p $ROOT_DIR/paper-plots

# Figure 6
python3 plot.py figure6 $ROOT_DIR/plots/pure_host_macrobench.csv $ROOT_DIR/plots/ndp_macrobench.csv
cp END_2_END_REL.pdf $ROOT_DIR/paper-plots/figure6.pdf
cp END_2_END_REL.pdf $ROOT_DIR/paper-src/plots/

# Figure 7
python3 plot.py figure7 $ROOT_DIR/plots/ndp_storage_secure.csv $ROOT_DIR/plots/pure_host_macrobench.csv
cp IO_SPEEDUP.pdf $ROOT_DIR/paper-plots/figure7.pdf
cp IO_SPEEDUP.pdf $ROOT_DIR/paper-src/plots/

# Figure 8
python3 plot.py figure8 $ROOT_DIR/plots/ndp_macrobench.csv $ROOT_DIR/plots/ndp_macrobench.csv $ROOT_DIR/plots/ndp_storage_secure.csv
cp END_END_OVERHEAD.pdf $ROOT_DIR/paper-plots/figure8.pdf
cp END_END_OVERHEAD.pdf $ROOT_DIR/paper-src/plots/

# Figure 9a
python3 plot.py figure9a $ROOT_DIR/plots/selectivity_bench.csv
cp SIZE_VS_QUERY.pdf $ROOT_DIR/paper-plots/figure9a.pdf
cp SIZE_VS_QUERY.pdf $ROOT_DIR/paper-src/plots/

# Figure 9b
python3 plot.py figure9b $ROOT_DIR/plots/selectivity_bench.csv
cp SELECTIVITY_VS_QUERY.pdf $ROOT_DIR/paper-plots/figure9b.pdf
cp SELECTIVITY_VS_QUERY.pdf $ROOT_DIR/paper-src/plots/

# Figure 9c
# TODO: Check if all offload is required
python3 plot.py figure9c $ROOT_DIR/plots/ndp_storage_secure.csv $ROOT_DIR/plots/ndp_macrobench.csv
cp SEC_STORAGE.pdf $ROOT_DIR/paper-plots/figure9c.pdf
cp SEC_STORAGE.pdf $ROOT_DIR/paper-src/plots/

# Figure 10
python3 plot.py figure10 $ROOT_DIR/plots/ndp_macrobench_hotplug.csv $ROOT_DIR/plots/pure_host_macrobench_hotplug.csv
cp SQLITE_CPUS.pdf $ROOT_DIR/paper-plots/figure10.pdf
cp SQLITE_CPUS.pdf $ROOT_DIR/paper-src/plots/

# Figure 11
python3 plot.py figure11 $ROOT_DIR/plots/sqlite_mem_limit_cgroup.csv
cp SQLITE_MEM_LIMIT.pdf $ROOT_DIR/paper-plots/figure11.pdf
cp SQLITE_MEM_LIMIT.pdf $ROOT_DIR/paper-src/plots/

# Figure 12
python3 plot.py figure12 $ROOT_DIR/plots/multi_sqlite_*.csv
cp SQLITE_INC_THREADS.pdf $ROOT_DIR/paper-plots/figure12.pdf
cp SQLITE_INC_THREADS.pdf $ROOT_DIR/paper-src/plots/
