#!/bin/bash

SRC=$(realpath ../..)
TPCH=$SRC/tpch
SSD_SERVER=$SRC/storage/$2
MERK_DIR=$SRC/merkle-tree/src

DB_FILE=""
MERK_FILE=""

if [ "$2" = "non-secure" ]; then
	DB_FILE="$TPCH/build/TPCH-$1.db"
	MERK_FILE="crap"
fi

if [ "$2" = "secure" ]; then
	DB_FILE="$TPCH/build/TPCH-$1-fresh-enc.db"
	MERK_FILE="$TPCH/build/merkle-tree-$1.bin"
fi

if [ ! -e "$DB_FILE" ]; then
	cd $TPCH
	./create_db.sh $1 > /dev/null 2>&1
fi

# echo "DB name: $DB_FILE"

cd $MERK_DIR
make > /dev/null 2>&1

cd $SSD_SERVER
# echo $PASS
./run_server_$2_side.sh $DB_FILE $PASS $MERK_FILE "ssd-$2-$3-output-$DATE.csv"
