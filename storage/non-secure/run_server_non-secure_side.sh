#!/bin/bash

# ROOT_DIR=..

make clean && make

./ssd-ndp $1 $2 $3
