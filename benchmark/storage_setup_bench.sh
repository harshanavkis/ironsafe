#!/bin/bash

sudo ls-addni dpmac.2

sudo ip link set eth1 up
sudo ip addr flush dev eth1
sudo ip addr add 10.0.42.21/24 dev eth1
sudo ip link set eth1 mtu 1500
sudo ip link set eth1 up

# change tcp window settings
sudo sysctl -w net.ipv4.tcp_timestamps=0
sudo sysctl -w net.ipv4.tcp_sack=1
sudo sysctl -w net.core.netdev_max_backlog=250000
sudo sysctl -w net.core.rmem_max=4194304
sudo sysctl -w net.core.wmem_max=4194304
sudo sysctl -w net.core.rmem_default=4194304
sudo sysctl -w net.core.wmem_default=4194304
sudo sysctl -w net.core.optmem_max=4194304
sudo sysctl -w net.ipv4.tcp_rmem="4096 87380 4194304"
sudo sysctl -w net.ipv4.tcp_wmem="4096 65536 4194304"
sudo sysctl -w net.ipv4.tcp_low_latency=1
sudo sysctl -w net.ipv4.tcp_adv_win_scale=1

sudo sysctl net.ipv4.tcp_timestamps=0
sudo sysctl net.ipv4.tcp_sack=1
sudo sysctl net.core.netdev_max_backlog=250000
sudo sysctl net.core.rmem_max=4194304
sudo sysctl net.core.wmem_max=4194304
sudo sysctl net.core.rmem_default=4194304
sudo sysctl net.core.wmem_default=4194304
sudo sysctl net.core.optmem_max=4194304
sudo sysctl net.ipv4.tcp_rmem="4096 87380 4194304"
sudo sysctl net.ipv4.tcp_wmem="4096 65536 4194304"
sudo sysctl net.ipv4.tcp_low_latency=1
sudo sysctl net.ipv4.tcp_adv_win_scale=1
