#!/bin/bash
cd /sys/kernel/config/nvmet
rm -f ports/1/subsystems/secndp
rmdir ports/1
rmdir subsystems/ndp-subsystem/secndp/1
rmdir subsystems/secndp
