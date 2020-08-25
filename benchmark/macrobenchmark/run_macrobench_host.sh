#!/bin/bash

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

SRC=$(realpath ../..)
CURR_PATH=$(realpath .)

mkdir -p result

DATE=$(date +"%Y-%m-%d-%H-%M")

count=1

ssh $REMOTE_USER@$STORAGE_SERVER_IP "cd $REMOTE_SRC/benchmark/macrobenchmark && DATE=$DATE PASS=kun ./run_macrobench_storage.sh $SCALE_FACTOR non-secure" &
sleep 10
./benchmark_whole.sh $count non-secure $STORAGE_SERVER_IP
sleep 30
ssh $REMOTE_USER@$STORAGE_SERVER_IP "kill -9 \$(pgrep run_server)"
ssh $REMOTE_USER@$STORAGE_SERVER_IP "kill -9 \$(pgrep ssd-ndp)"

# sleep 30

# ssh $REMOTE_USER@$STORAGE_SERVER_IP "cd $REMOTE_SRC/benchmark/macrobenchmark && DATE=$DATE PASS=kun ./run_macrobench_storage.sh $SCALE_FACTOR secure" &
# sleep 10
# docker run $MOUNT_SGXDEVICE -v $CURR_PATH/result/:/sqlite-ndp/benchmark/macrobenchmark/result host-ndp /bin/bash -c "./benchmark_whole.sh $count secure $STORAGE_SERVER_IP"
# ssh $REMOTE_USER@$STORAGE_SERVER_IP "kill -9 \$(pgrep run_server)"
# ssh $REMOTE_USER@$STORAGE_SERVER_IP "kill -9 \$(pgrep ssd-ndp)"