#!/bin/bash

for x in /sys/devices/system/cpu/*/cpufreq/; do echo 2000000 | sudo tee $x/scaling_max_freq; done

sudo ip link set enp2s0f1 up
sudo ip addr flush dev enp2s0f1
sudo ip addr add 10.0.42.22/24 dev enp2s0f1
sudo ip link set enp2s0f1 mtu 1500
sudo ip link set enp2s0f1 up


