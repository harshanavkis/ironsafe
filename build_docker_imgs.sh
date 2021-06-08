#!/usr/bin/env bash

mkdir -p $SEC_BUILD_DIR

#docker build -f benchmark/scone-stuff/sec-ndp -t host-ndp .
hs=$(docker create host-ndp)
docker cp $hs:/sqlite-ndp/host/secure/host-ndp $SEC_BUILD_DIR
docker rm $hs
#sleep 5
#docker build -f benchmark/scone-stuff/vanilla-ndp -t vanilla-ndp .
#sleep 5
#docker build -f benchmark/scone-stuff/pure-host -t pure-host .
#sleep 5
#docker build -f benchmark/scone-stuff/pure-host-sec -t pure-host-sec .
#phs=$(docker create pure-host-sec)
#docker cp $phs:/fresh-sqlite/hello-query $SEC_BUILD_DIR
#docker rm $phs
