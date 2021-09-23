#!/usr/bin/env bash

for cpu in {1..15};
do
    echo 1 | sudo tee "/sys/devices/system/cpu/cpu$cpu/online";
done