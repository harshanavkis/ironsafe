#!/bin/bash

SRC=$(realpath ../..)

ssh $REMOTE_USER@$STORAGE_SERVER_IP "cd /home/hi/src/benchmark/macrobenchmark && PASS=kun ./run_macrobench_storage.sh $SCALE_FACTOR non-secure" > /dev/null 2>&1 &
sleep 30
./benchmark_whole.sh 1 non-secure $STORAGE_SERVER_IP
ssh $REMOTE_USER@$STORAGE_SERVER_IP "kill -9 \$(pgrep run_server)"
ssh $REMOTE_USER@$STORAGE_SERVER_IP "kill -9 \$(pgrep ssd-ndp)"

sleep 10

ssh $REMOTE_USER@$STORAGE_SERVER_IP "cd /home/hi/src/benchmark/macrobenchmark && PASS=kun ./run_macrobench_storage.sh $SCALE_FACTOR secure" > /dev/null 2>&1 &
sleep 30
./benchmark_whole.sh 1 secure $STORAGE_SERVER_IP
ssh $REMOTE_USER@$STORAGE_SERVER_IP "kill -9 \$(pgrep run_server)"
ssh $REMOTE_USER@$STORAGE_SERVER_IP "kill -9 \$(pgrep ssd-ndp)"