#!/usr/bin/env bash

ssh $REMOTE_USER@$STORAGE_SERVER_IP "$REMOTE_SRC/benchmark/macrobenchmark/turn_on_cpus.sh"
