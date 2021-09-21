#!/usr/bin/env bash

# $1: pid
# $2: memory limit

echo $1 > /sys/fs/cgroup/memory/sqlite_cgroup/cgroup.procs
echo $2 > /sys/fs/cgroup/memory/sqlite_cgroup/memory.limit_in_bytes