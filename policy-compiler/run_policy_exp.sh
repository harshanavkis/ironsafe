#!/usr/bin/env bash

LOG_FILE="secndp_log"
ENC_VOL="volume"
ORIG_VOL="/tmp/secndp"

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
    SCONE_FSPF_KEY=$(cat $ORIG_VOL/keytag | awk '{print $11}')
    SCONE_FSPF_TAG=$(cat $ORIG_VOL/keytag | awk '{print $9}')

    EXP_OP=$1

    docker run --rm  $MOUNT_SGXDEVICE -v "$PWD/volume:/data" -v /tmp/secndp/:/data-original -v "$PWD:/usr/src/myapp" -w /usr/src/myapp -e SCONE_HEAP=256M -e SCONE_MODE=HW -e SCONE_ALLOW_DLOPEN=2 -e SCONE_ALPINE=1 -e SCONE_VERSION=1 -e SERVER_IP=172.17.0.2 -e IDENTITY_FILE=dummy-user.pub -e STORAGE_FW_VERS_DB=storage_version.csv -e SERVER_PORT=5000 -e LOG_FILE=/data/secndp_log -e DATA_ACCESS_POLICY=/data/user_data_access_policy.json sconecuratedimages/apps:python-3.7-alpine /bin/bash -c "SCONE_FSPF_KEY=$SCONE_FSPF_KEY SCONE_FSPF_TAG=$SCONE_FSPF_TAG SCONE_FSPF=/data/fspf.pb python policy_server.py $EXP_OP dummy_storage_attr.json"
}

function run_policy_client() {
    docker run --rm  $MOUNT_SGXDEVICE -v "$PWD:/usr/src/myapp" -w /usr/src/myapp -e SCONE_HEAP=256M -e SCONE_MODE=HW -e SCONE_ALLOW_DLOPEN=2 -e SERVER_IP=172.17.0.2 -e SERVER_PORT=5000 -e SCONE_ALPINE=1 -e SCONE_VERSION=1 sconecuratedimages/apps:python-3.7-alpine python policy_client.py user_policy.txt
}

function clear_page_cache() {
    sudo sysctl -w vm.drop_caches=3
}

function setup_encr_vol() {
    mkdir -p $ENC_VOL
    mkdir -p $ORIG_VOL
    # touch "$ORIG_VOL/$LOG_FILE"
    # echo "hello" > "$ORIG_VOL/$LOG_FILE"
    cp "user_data_access_policy.json" $ORIG_VOL
    docker run -v "$PWD/$ENC_VOL:/data" -v "$ORIG_VOL:/data-original" sconecuratedimages/crosscompilers:ubuntu /bin/bash -c "cd data && scone fspf create fspf.pb"

    docker run -v "$PWD/$ENC_VOL:/data" -v "$ORIG_VOL:/data-original" sconecuratedimages/crosscompilers:ubuntu /bin/bash -c "cd data && scone fspf addr fspf.pb / --kernel / --not-protected"

    docker run -v "$PWD/$ENC_VOL:/data" -v "$ORIG_VOL:/data-original" sconecuratedimages/crosscompilers:ubuntu /bin/bash -c "cd data && scone fspf addr fspf.pb /data --encrypted --kernel /data"

    docker run -v "$PWD/$ENC_VOL:/data" -v "$ORIG_VOL:/data-original" sconecuratedimages/crosscompilers:ubuntu /bin/bash -c "cd data && scone fspf addf fspf.pb /data /data-original /data"

    docker run -v "$PWD/$ENC_VOL:/data" -v "$ORIG_VOL:/data-original" sconecuratedimages/crosscompilers:ubuntu /bin/bash -c "cd data && scone fspf encrypt fspf.pb > /data-original/keytag"
}

function test_encr_vol() {
    SCONE_FSPF_KEY=$(cat $ORIG_VOL/keytag | awk '{print $11}')
    SCONE_FSPF_TAG=$(cat $ORIG_VOL/keytag | awk '{print $9}')

    docker run --rm  $MOUNT_SGXDEVICE -v "$PWD/volume:/data" -v /tmp/secndp/:/data-original -v "$PWD:/usr/src/myapp" -w "/usr/src/myapp" -e SCONE_HEAP=256M -e SCONE_MODE=HW -e SCONE_ALLOW_DLOPEN=2 -e SCONE_ALPINE=1 -e SCONE_VERSION=1 sconecuratedimages/apps:python-3.7-alpine /bin/bash -c "SCONE_FSPF_KEY=$SCONE_FSPF_KEY SCONE_FSPF_TAG=$SCONE_FSPF_TAG SCONE_FSPF=/data/fspf.pb LOG_FILE=/data/user_data_access_policy.json python test_scone_file_shield.py"
}

determine_sgx_device

if [ ! -f "$ENC_VOL/fspf.pb" ]; then
    echo "Setting up encrypted volume"
    setup_encr_vol
    test_encr_vol
fi
# exit 0

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