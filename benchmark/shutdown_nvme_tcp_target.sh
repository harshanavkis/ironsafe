#!/bin/bash
cd /sys/kernel/config/nvmet
rm -f ports/1/subsystems/secndp
rmdir ports/1
rmdir subsystems/secndp/namespaces/1 
rmdir subsystems/secndp
