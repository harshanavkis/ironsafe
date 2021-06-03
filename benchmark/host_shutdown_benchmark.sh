#!/bin/bash

for x in /sys/devices/system/cpu/*/cpufreq/; do echo 5300000 | sudo tee $x/scaling_max_freq; done
