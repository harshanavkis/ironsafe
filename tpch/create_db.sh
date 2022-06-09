#!/bin/bash

SRC=$(realpath .)
FRESH_SQLITE=$SRC/fresh-sqlite
TPCH_DBGEN=$SRC/tpch-dbgen
TPCH=$SRC/tpch

# compile fresh sqlite and the merkle tree library
echo "Building merkle tree library..."
cd $FRESH_SQLITE/merkle-tree/src
make clean && make

cd $FRESH_SQLITE
echo "Building rolback protected sqlite..."
make clean && make hello-insert

# compile tpch dbgen
echo "Building the tpch dbgen tool..."
cd $TPCH_DBGEN/dbgen
make clean && make

for scale in "$@"
do
	if [ ! -f $TPCH_DBGEN/build/TPC-H-$scale.sql ]; then
		cd $TPCH_DBGEN/dbgen
		echo "Generating TPC-H data..."
		./dbgen -v -f -s $scale

		# generate sqlite insert statements
		echo "Generating insert statements from tpch data..."
		cd $TPCH_DBGEN
		mkdir -p build
		python3 tbl_to_sql.py sqlite-ddl.sql dbgen/*.tbl $scale
	fi

	# create a build directory to store the databases
	echo "Generating encrypted and rollback protected database..."
	cd $TPCH
	mkdir -p build
	$FRESH_SQLITE/hello-insert build/TPCH-$scale-fresh-enc.db build/merkle-tree-$scale.bin kun $TPCH_DBGEN/build/TPC-H-$scale.sql "select count(*) from lineitem;"

	echo "Generating un-encrypted database..."
	echo ".read $TPCH_DBGEN/build/TPC-H-$scale.sql" | sqlite3 build/TPCH-$scale.db
done