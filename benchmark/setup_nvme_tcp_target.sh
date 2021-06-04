#!/usr/bin/env bash
# first argument must be the local ip addr

mkdir /sys/kernel/config/nvmet/subsystems/secndp
cd /sys/kernel/config/nvmet/subsystems/secndp

echo 1 > attr_allow_any_host
mkdir namespaces/1
cd namespaces/1
echo -n /dev/nvme0n1 > device_path
echo 1 > enable

mkdir /sys/kernel/config/nvmet/ports/1
cd /sys/kernel/config/nvmet/ports/1
echo $1 > addr_traddr
echo "tcp" > addr_trtype
echo 4420 | tee -a addr_trsvcid
echo "ipv4" > addr_adrfam

ln -s /sys/kernel/config/nvmet/subsystems/secndp /sys/kernel/config/nvmet/ports/1/subsystems/secndp

dmesg | grep "nvmet_tcp"
