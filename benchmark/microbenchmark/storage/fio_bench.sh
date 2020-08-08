#!/bin/bash

for i in $(ls fio-jobs); do
	fio_out=$(fio "fio-jobs/$i" --output-format=json)
	python3 process_fio_json.py $i "$fio_out"
done