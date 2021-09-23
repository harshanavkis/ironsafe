#!/usr/bin/env bash

for cpu in "$@";
do
    echo 0 | sudo tee "/sys/devices/system/cpu/cpu$cpu/online";
done