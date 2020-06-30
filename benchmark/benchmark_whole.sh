#!/bin/bash

ROOT_DIR=..

python3 process_sql.py $ROOT_DIR/tpch/tpc_h_queries.sql queries.csv

flag=0

while IFS= read -r line; do
		IFS='|' read -ra CSV_ROW <<< "$line"
		echo "${CSV_ROW[0]}"
		echo "${CSV_ROW[2]}"
		echo "${CSV_ROW[3]}"

		res_row="${CSV_ROW[0]}"

		counter=1
		while [ $counter -le $1 ]; do
  		exec_time=$("$ROOT_DIR/host/$2/host-ndp" -D .. -Q "${CSV_ROW[2]}" -S "${CSV_ROW[3]}" $3 | awk '{ print $4 }')
  		res_row="$res_row,${exec_time}"
      counter=$((counter+1))
  		sleep 10
    done

		if [ $flag == 0 ]
		then
			echo $res_row > result.csv
      flag=1
		else
			echo $res_row >> result.csv
		fi

done < queries.csv
