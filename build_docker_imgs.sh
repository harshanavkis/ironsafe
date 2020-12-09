#!/bin/bash

docker build -f benchmark/scone-stuff/sec-ndp -t host-ndp .
sleep 5
docker build -f benchmark/scone-stuff/vanilla-ndp -t vanilla-ndp .
sleep 5
docker build -f benchmark/scone-stuff/pure-host -t pure-host .
sleep 5
docker build -f benchmark/scone-stuff/pure-host-sec -t pure-host-sec .