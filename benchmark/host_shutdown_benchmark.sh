#!/usr/bin/env bash

for x in /sys/devices/system/cpu/*/cpufreq/; do echo 5300000 | sudo tee $x/scaling_max_freq; done

sudo umount /home/$USER/nfs_mnt
