#!/bin/bash
# WRITE_BATCH="1" ./dd_bench.sh /media/hvub/harshaDrive/ 4 8 16 32 64 128 256

MICRO_DIR=$(realpath ..)
RES_DIR=$MICRO_DIR/result
COUNT=1000

mkdir -p $RES_DIR

# measure write latency
echo "Write latency..."
for bs in "${@:2}"
do
	write_latency=$(dd if=/dev/zero of=$1/dd-write bs=${bs}K count=$COUNT oflag=direct 2>&1)
	python process_csv.py "w" "l" "$write_latency" $COUNT "$bs" "$RES_DIR/write_lat_dd.csv"
done

#measure write throughput
echo "Write throughput..."
COUNT=1
for bs in $WRITE_BATCH
do
	echo "$bs"
	write_throughput=$(dd if=/dev/zero of=$1/dd-write bs=1G count=${bs} oflag=direct 2>&1)
	python process_csv.py "w" "t" "$write_throughput" $COUNT "$bs" "$RES_DIR/write_thru_dd.csv"
done

echo "Read throughput and latency..."

#measure read throughput and latency
for bs in "${@:2}"
do
	echo 3 > /proc/sys/vm/drop_caches
	read_metrics=$(dd if=$1/dd-write of=/dev/zero bs=${bs}K 2>&1)
	python process_csv.py "r" "b" "$read_metrics" $COUNT $bs "$RES_DIR/read_thru_lat_dd.csv"
done