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

function setup_encr_vol() {
    mkdir -p $ENC_VOL
    mkdir -p $ORIG_VOL
    touch "$ORIG_VOL/$LOG_FILE"
    echo "hello" > "$ORIG_VOL/$LOG_FILE"
    docker run -v "$PWD/$ENC_VOL:/data" -v "$ORIG_VOL:/data-original" sconecuratedimages/crosscompilers:ubuntu /bin/bash -c "cd data && scone fspf create fspf.pb"

    docker run -v "$PWD/$ENC_VOL:/data" -v "$ORIG_VOL:/data-original" sconecuratedimages/crosscompilers:ubuntu /bin/bash -c "cd data && scone fspf addr fspf.pb / --kernel / --not-protected"

    docker run -v "$PWD/$ENC_VOL:/data" -v "$ORIG_VOL:/data-original" sconecuratedimages/crosscompilers:ubuntu /bin/bash -c "cd data && scone fspf addr fspf.pb /data --encrypted --kernel /data"

    docker run -v "$PWD/$ENC_VOL:/data" -v "$ORIG_VOL:/data-original" sconecuratedimages/crosscompilers:ubuntu /bin/bash -c "cd data && scone fspf addf fspf.pb /data /data-original /data"

    docker run -v "$PWD/$ENC_VOL:/data" -v "$ORIG_VOL:/data-original" sconecuratedimages/crosscompilers:ubuntu /bin/bash -c "cd data && scone fspf encrypt fspf.pb > /data-original/keytag"
}

function test_encr_vol() {
    SCONE_FSPF_KEY=$(cat $ORIG_VOL/keytag | awk '{print $11}')
    SCONE_FSPF_TAG=$(cat $ORIG_VOL/keytag | awk '{print $9}')

    docker run --rm  $MOUNT_SGXDEVICE -v "$PWD/volume:/data" -v /tmp/secndp/:/data-original -v "$PWD:/usr/src/myapp" -w "/usr/src/myapp" -e SCONE_HEAP=256M -e SCONE_MODE=HW -e SCONE_ALLOW_DLOPEN=2 -e SCONE_ALPINE=1 -e SCONE_VERSION=1 sconecuratedimages/apps:python-3.7-alpine /bin/bash -c "SCONE_FSPF_KEY=$SCONE_FSPF_KEY SCONE_FSPF_TAG=$SCONE_FSPF_TAG SCONE_FSPF=/data/fspf.pb LOG_FILE=/data/secndp_log python test_scone_file_shield.py"
}

function setup_log_server() {
    SCONE_FSPF_KEY=$(cat $ORIG_VOL/keytag | awk '{print $11}')
    SCONE_FSPF_TAG=$(cat $ORIG_VOL/keytag | awk '{print $9}')

    docker run --rm  $MOUNT_SGXDEVICE -v "$PWD/volume:/data" -v /tmp/secndp/:/data-original -v "$PWD:/usr/src/myapp" -w "/usr/src/myapp" -e SCONE_HEAP=256M -e SCONE_MODE=HW -e SCONE_ALLOW_DLOPEN=2 -e SCONE_ALPINE=1 -e SCONE_VERSION=1 sconecuratedimages/apps:python-3.7-alpine /bin/bash -c "SCONE_FSPF_KEY=$SCONE_FSPF_KEY SCONE_FSPF_TAG=$SCONE_FSPF_TAG SCONE_FSPF=/data/fspf.pb LOG_FILE=/data/secndp_log SERVER_IP=172.17.0.2 SERVER_PORT=5000 python logging_server.py"
}

function run_log_client() {
    docker run --rm  $MOUNT_SGXDEVICE -v "$PWD:/usr/src/myapp" -w /usr/src/myapp -e SCONE_HEAP=256M -e SCONE_MODE=HW -e SCONE_ALLOW_DLOPEN=2 -e SCONE_ALPINE=1 -e SCONE_VERSION=1 -e SERVER_IP=172.17.0.2 -e SERVER_PORT=5000 sconecuratedimages/apps:python-3.7-alpine python logging_client.py
}

determine_sgx_device

if [ ! -f "$ENC_VOL/fspf.pb" ]; then
    echo "Setting up encrypted volume"
    setup_encr_vol
    test_encr_vol
fi

DATE=$(date +"%Y-%m-%d-%H-%M")
ITER=$1

for i in $(eval echo {1..$ITER})
do
    setup_log_server &
    sleep 10
    result=$(run_log_client)
    echo "$i, $result" >> log_res-$DATE.csv
    sleep 10
done