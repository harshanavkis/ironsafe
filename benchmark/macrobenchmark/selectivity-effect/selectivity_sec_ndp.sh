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

determine_sgx_device > /dev/null 2>&1

SRC=$(realpath ../../../)
CURR_PATH=$(realpath .)

mkdir -p result
DATE=$(date +"%Y-%m-%d-%H-%M")

# $1:non-secure/secure
# $2: scale_factor
ssh $REMOTE_USER@$STORAGE_SERVER_IP "cd $REMOTE_SRC/benchmark/macrobenchmark && DATE=selectivity-$DATE PASS=kun ./run_macrobench_storage.sh $1 $2" > /dev/null 2>&1 &

# sleep 20
