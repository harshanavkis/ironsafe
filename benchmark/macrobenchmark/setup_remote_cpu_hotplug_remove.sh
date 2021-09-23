#!/usr/bin/env bash

ssh $REMOTE_USER@$STORAGE_SERVER_IP "cd $REMOTE_SRC/benchmark/macrobenchmark/turn_off_cpus.sh $SHUTDOWN_CPUS"