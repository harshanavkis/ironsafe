#!/bin/bash

# ROOT_DIR=..

make clean > /dev/null 2>&1
make > /dev/null 2>&1

# echo "Running storage side application..."

# echo $1
# echo $2
# echo $3

# while true
# do
./sec-ssd-ndp $1 $2 $3
# done
