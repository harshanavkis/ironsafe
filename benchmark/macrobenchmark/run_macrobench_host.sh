#!/usr/bin/env bash

function determine_sgx_device {
    export SGXDEVICE="/dev/sgx"
    export MOUNT_SGXDEVICE="-v /dev/sgx/:/dev/sgx"
    if [[ ! -e "$SGXDEVICE" ]] ; then
        export SGXDEVICE="/dev/isgx"
        export MOUNT_SGXDEVICE="--device=/dev/isgx"
        if [[ ! -c "$SGXDEVICE" ]] ; then
            echo "Warning: No SGX device found! Will run in SIM mode." > /dev/stderr
            export MOUNT_SGXDEVICE=""
            export SGXDEVICE=""
        fi
    fi
}

determine_sgx_device

# SRC=$(realpath ../..)
# CURR_PATH=$(realpath .)

# mkdir -p result

# DATE=$(date +"%Y-%m-%d-%H-%M")

# count=1

ssh $REMOTE_USER@$STORAGE_SERVER_IP "cd $REMOTE_SRC/benchmark/macrobenchmark && DATE=$DATE PASS=kun ./run_macrobench_storage.sh $SCALE_FACTOR $CONN_TYPE $OFFLOAD_TYPE" &
