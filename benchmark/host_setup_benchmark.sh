#!/bin/bash

for x in /sys/devices/system/cpu/*/cpufreq/; do echo 2000000 | sudo tee $x/scaling_max_freq; done


