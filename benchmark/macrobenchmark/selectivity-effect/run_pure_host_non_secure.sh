#!/bin/bash

SRC_DIR=$(realpath ../../)
CURR_DIR=$(realpath .)

#cd $SRC_DIR/fresh-sqlite
$SRC_DIR/fresh-sqlite/hello-query $1 $2 "" "$3"
#cd $CURR_DIR
