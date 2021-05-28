#!/bin/bash

LOG_FILE="secndp_log"
ENC_VOL="volume"
ORIG_VOL="/tmp/secndp"

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

    docker run -it --rm  $MOUNT_SGXDEVICE -v "$PWD/volume:/data" -v /tmp/secndp/:/data-original -v "$PWD:/usr/src/myapp" -w "/usr/src/myapp" -e SCONE_HEAP=256M -e SCONE_MODE=HW -e SCONE_ALLOW_DLOPEN=2 -e SCONE_ALPINE=1 -e SCONE_VERSION=1 sconecuratedimages/apps:python-3.7-alpine /bin/bash -c "SCONE_FSPF_KEY=$SCONE_FSPF_KEY SCONE_FSPF_TAG=$SCONE_FSPF_TAG SCONE_FSPF=/data/fspf.pb LOG_FILE=/data/secndp_log python test_scone_file_shield.py"
}

if [ ! -f "$ENC_VOL/fspf.pb" ]; then
    echo "Setting up encrypted volume"
    setup_encr_vol
fi

test_encr_vol