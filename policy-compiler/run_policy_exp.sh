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
    docker run --rm  $MOUNT_SGXDEVICE -v "$PWD:/usr/src/myapp" -w /usr/src/myapp -e SCONE_HEAP=256M -e SCONE_MODE=HW -e SCONE_ALLOW_DLOPEN=2 -e SCONE_ALPINE=1 -e SCONE_VERSION=1 -e SERVER_IP=172.17.0.2 -e IDENTITY_FILE=dummy-user.pub -e STORAGE_FW_VERS_DB=storage_version.csv -e SERVER_PORT=5000 -e LOG_FILE=secndp-log -e DATA_ACCESS_POLICY=user_data_access_policy.json sconecuratedimages/apps:python-3.7-alpine python policy_server.py $1 dummy_storage_attr.json
}

function run_policy_client() {
    docker run --rm  $MOUNT_SGXDEVICE -v "$PWD:/usr/src/myapp" -w /usr/src/myapp -e SCONE_HEAP=256M -e SCONE_MODE=HW -e SCONE_ALLOW_DLOPEN=2 -e SERVER_IP=172.17.0.2 -e SERVER_PORT=5000 -e SCONE_ALPINE=1 -e SCONE_VERSION=1 sconecuratedimages/apps:python-3.7-alpine python policy_client.py user_policy.txt
}

function clear_page_cache() {
    sudo sysctl -w vm.drop_caches=3
}

determine_sgx_device
sleep 5

DATE=$(date +"%Y-%m-%d-%H-%M")
ITER=$1

echo "Running use case 1: timely deletion"
for i in $(eval echo {1..$ITER})
do
    clear_page_cache
    setup_policy_server "1" &
    sleep 10
    result=$(run_policy_client)
    echo "$i, $result" >> use-case-one-$DATE.csv
    sleep 5
done

echo "Running use case 2: indiscr use case"
for i in $(eval echo {1..$ITER})
do
    clear_page_cache
    setup_policy_server "2" &
    sleep 10
    result=$(run_policy_client)
    echo "$i, $result" >> use-case-two-$DATE.csv
    sleep 5
done

echo "Running use case 3: obtain shared data"
setup_policy_server "4" &
sleep 10
result=$(run_policy_client)
for i in $(eval echo {1..$ITER})
do
    clear_page_cache
    setup_policy_server "3" &
    sleep 10
    result=$(run_policy_client)
    echo "$i, $result" >> use-case-three-$DATE.csv
    sleep 5
done

echo "Running use case 4: risk agnostic"
for i in $(eval echo {1..$ITER})
do
    clear_page_cache
    setup_policy_server "4" &
    sleep 10
    result=$(run_policy_client)
    echo "$i, $result" >> use-case-four-$DATE.csv
    sleep 5
done

echo "Running use case 5: hiding breaches"
for i in $(eval echo {1..$ITER})
do
    clear_page_cache
    setup_policy_server "5" &
    sleep 10
    result=$(run_policy_client)
    echo "$i, $result" >> use-case-five-$DATE.csv
    sleep 5
done