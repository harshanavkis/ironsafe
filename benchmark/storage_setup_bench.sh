#!/bin/bash

sudo ls-addni dpmac.2

sudo ip link set eth1 up
sudo ip addr flush dev eth1
sudo ip addr add 10.0.42.21/24 dev eth1
sudo ip link set eth1 mtu 1500
sudo ip link set eth1 up
