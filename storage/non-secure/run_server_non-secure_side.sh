#!/bin/bash

# ROOT_DIR=..

make clean > /dev/null 2>&1
make > /dev/null 2>&1

./ssd-ndp $1 $2 $3 $4
