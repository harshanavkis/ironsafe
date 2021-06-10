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

function setup_policy_server() {
    docker run --rm  $MOUNT_SGXDEVICE -v "$PWD:/usr/src/myapp" -w /usr/src/myapp -e SCONE_HEAP=256M -e SCONE_MODE=HW -e SCONE_ALLOW_DLOPEN=2 -e SCONE_ALPINE=1 -e SCONE_VERSION=1 -e SERVER_IP=172.17.0.2 -e IDENTITY_FILE=dummy-user.pub -e STORAGE_FW_VERS_DB=storage_version.csv -e SERVER_PORT=5000 sconecuratedimages/apps:python-3.7-alpine python policy_server.py dummy_storage_attr.json
}

function run_policy_client() {
    docker run --rm  $MOUNT_SGXDEVICE -v "$PWD:/usr/src/myapp" -w /usr/src/myapp -e SCONE_HEAP=256M -e SCONE_MODE=HW -e SCONE_ALLOW_DLOPEN=2 -e SERVER_IP=172.17.0.2 -e SERVER_PORT=5000 -e SCONE_ALPINE=1 -e SCONE_VERSION=1 sconecuratedimages/apps:python-3.7-alpine python policy_client.py user_policy.txt
}

determine_sgx_device
sleep 5

DATE=$(date +"%Y-%m-%d-%H-%M")
ITER=$1

for i in $(eval echo {1..$ITER})
do
    setup_policy_server &
    sleep 10
    result=$(run_policy_client)
    echo "$i, $result" >> pol_eval-$DATE.csv
    sleep 5
done