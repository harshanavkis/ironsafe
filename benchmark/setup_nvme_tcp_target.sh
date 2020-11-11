#!/bin/bash
# first argument must be the local ip addr

mkdir /sys/kernel/config/nvmet/subsystems/secndp
cd /sys/kernel/config/nvmet/subsystems/secndp

echo 1 | tee -a attr_allow_any_host
mkdir namespaces/1
cd namespaces/1
echo -n /dev/nvme0n1 | tee -a device_path
echo 1 | tee -a enable

mkdir /sys/kernel/config/nvmet/ports/1
cd /sys/kernel/config/nvmet/ports/1
echo $1 | tee -a addr_traddr
echo tcp | tee -a addr_trtype
echo 4420 | tee -a addr_trsvcid
echo ipv4 | tee -a addr_adrfam

ln -s /sys/kernel/config/nvmet/subsystems/secndp /sys/kernel/config/nvmet/ports/1/subsystems/secndp

dmesg | grep "nvmet_tcp"