#!/bin/bash

# ROOT_DIR=..

make

echo "Running storage side application..."

echo $1
echo $2
echo $3

while true
do
  ./sec-ssd-ndp $1 $2 $3
done
