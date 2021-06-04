#!/usr/bin/env bash

ROOT_DIR=$(realpath ../..)
BENCH_DIR=$(realpath .)
RESULT_DIR=$BENCH_DIR/result

cd $ROOT_DIR/host/$2
make

cd $BENCH_DIR


python3 process_sql.py $ROOT_DIR/tpch/$4 queries.csv $2 22

flag=0

FILENAME=$(date +"%Y_%m_%d_%I_%M_%p")

while IFS= read -r line; do
		IFS='|' read -ra CSV_ROW <<< "$line"
		echo "${CSV_ROW[0]}"
		echo "${CSV_ROW[2]}"
		echo "${CSV_ROW[3]}"

		res_row="${CSV_ROW[0]}"

		counter=1
		while [ $counter -le $1 ]; do
		if [ "$2" = "non-secure" ]; then
  			exec_time=$("$ROOT_DIR/host/$2/host-ndp" -D .. -Q "${CSV_ROW[2]}" -S "${CSV_ROW[3]}" $3)
  		fi
  		if [ "$2" = "secure" ]; then
  			export SCONE_VERSION=1 SCONE_HEAP=2G
  			exec_time=$("$ROOT_DIR/host/$2/host-ndp" -D .. -Q "${CSV_ROW[2]}" -S "${CSV_ROW[3]}" $3)
  		fi
  		res_row="$res_row,${exec_time}"
      counter=$((counter+1))
  		sleep 10
    done

		if [ $flag == 0 ]
		then
			echo $res_row > "$RESULT_DIR/$2-result-$FILENAME-$5.csv"
      flag=1
		else
			echo $res_row >> "$RESULT_DIR/$2-result-$FILENAME-$5.csv"
		fi

done < queries.csv
