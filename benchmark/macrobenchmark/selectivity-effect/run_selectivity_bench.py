import sys
import os
import subprocess
from contextlib import contextmanager
import time

from selectivity_split import determine_split

import pdb

stdout=subprocess.PIPE

sql_query = "select l_returnflag, l_linestatus, sum(l_quantity) as sum_qty, sum(l_extendedprice) as sum_base_price, sum(l_extendedprice * (1 - l_discount)) as sum_disc_price, sum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge, avg(l_quantity) as avg_qty, avg(l_extendedprice) as avg_price, avg(l_discount) as avg_disc, count(*) as count_order from LINEITEM where l_shipdate {};"

host_query = "select l_returnflag, l_linestatus, sum(l_quantity) as sum_qty, sum(l_extendedprice) as sum_base_price, sum(l_extendedprice * (1 - l_discount)) as sum_disc_price, sum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge, avg(l_quantity) as avg_qty, avg(l_extendedprice) as avg_price, avg(l_discount) as avg_disc, count(*) as count_order from TABLE1;"

ssd_query = "select l_returnflag, l_linestatus,l_quantity, l_extendedprice, l_discount, l_tax from LINEITEM where l_shipdate {};"

device_host_query = "select l_returnflag, l_linestatus, sum_qty, sum_base_price, sum_disc_price, sum_charge, avg_qty, avg_price, avg_disc, count_order from TABLE1;"

device_ssd_query  = "select l_returnflag, l_linestatus, sum(l_quantity) as sum_qty, sum(l_extendedprice) as sum_base_price, sum(l_extendedprice * (1 - l_discount)) as sum_disc_price, sum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge, avg(l_quantity) as avg_qty, avg(l_extendedprice) as avg_price, avg(l_discount) as avg_disc, count(*) as count_order from LINEITEM where l_shipdate {};"

ROOT_DIR = os.path.realpath("../../../")
CURR_DIR = os.path.realpath(".")
DB_DIR = os.path.realpath("../../../tpch/build/TPCH-{}.db")
REM_DB_NAME = "tpch/build/TPCH-{}.db"

"""
	Environment variables:
		- REMOTE_SRC
		- STORAGE_SERVER_IP
		- REMOTE_USER
		- SCALE_FACTORS
		- SPLIT_POINTS
"""
def process_host_ndp_output(res):
	print(res)
	return res

def run_local_proc(cmd):
	proc = subprocess.run(cmd, stdout=stdout)
	return proc

def setup_exp():
	os.chdir(f"{ROOT_DIR}/host/non-secure/")
	cmd = ["make"]
	proc = run_local_proc(cmd)

	os.chdir(f"{ROOT_DIR}/openssl-src/")
	cmd = ["./Configure"]
	proc = run_local_proc(cmd)

	cmd = ["make"]
	proc = run_local_proc(cmd)

	cmd = ["docker", "image", "inspect", "host-ndp:latest"]
	proc = run_local_proc(cmd)

	if proc.returncode == 1:
		cmd = ["docker", "build", "-f", f"{ROOT_DIR}/benchmark/scone-stuff/Dockerfile", "-t", "host-ndp", f"{ROOT_DIR}/"]
		run_local_proc(cmd)

	os.chdir(CURR_DIR)


def run_pure_host_non_secure(cq, db_file):
	return ""

def run_pure_host_secure(cq, db_file):
	return ""

def run_vanilla_ndp_non_secure(hq, sq, db_file, scale_factor):
	proc = subprocess.run(["./selectivity_ndp.sh", f"{scale_factor}", "non-secure", hq, sq], stdout=stdout, text=True)

	kill_proc = subprocess.run(["./kill_rem_process.sh"], env=os.environ)

	return process_host_ndp_output(proc.stdout)


def run_secure_ndp_secure(hq, sq, scale_factor):
	remote_proc = subprocess.run(["./selectivity_sec_ndp.sh", f"{scale_factor}", "secure"], stdout=stdout, text=True)

	time.sleep(5)
	remote_ip = os.environ["STORAGE_SERVER_IP"]
	if remote_ip == "127.0.0.1":
		remote_ip = "172.17.0.1"

	local_cmd = ["docker", "run", "host-ndp", "/bin/bash", "-c", "cd /sqlite-ndp/host/secure/ && ./host-ndp -D .. -Q \"{}\" -S \"{}\" {}".format(hq, sq, remote_ip)]
	local_proc = subprocess.Popen(local_cmd, stdout=stdout, text=True)
	local_proc.wait()

	kill_proc = subprocess.run(["./kill_rem_process.sh"], env=os.environ)

	return process_host_ndp_output(local_proc.stdout.read())

def run_secure_device_only(dhq, dsq, db_file):
	return ""

def run_all_configs(cq, hq, sq, dhq, dsq, db_file, scale_factor):
	# phns = run_pure_host_non_secure(cq, db_file, scale_factor)
	# phs  = run_pure_host_secure(cq, db_file, scale_factor)
	vnns = run_vanilla_ndp_non_secure(hq, sq, db_file, scale_factor)
	sns  = run_secure_ndp_secure(hq, sq, scale_factor)
	# sss  = run_secure_device_only(dhq, dsq, scale_factor)

	# return [phns, phs, vnns, sns]
	return [vnns, sns]


def run_bench(scale_factor, split_point):
	db_file = DB_DIR.format(scale_factor)
	if not os.path.isfile(db_file):
		print(f"{db_file} does not exist")
		return

	result_dict = {}

	# split_point*total_rows < split_date
	split_date = determine_split(db_file, split_point, "L_SHIPDATE")

	upper_sel  = split_point
	lower_sel  = (1 - split_point)

	result_dict[upper_sel] = None
	result_dict[lower_sel] = None

	result_dict[upper_sel] = run_all_configs(
		sql_query.format("<={}".format(split_date)),
		host_query,
		ssd_query.format("<={}".format(split_date)),
		device_host_query,
		device_ssd_query.format("<={}".format(split_date)),
		db_file,
		scale_factor
	)

	if upper_sel != lower_sel:
		result_dict[lower_sel] = run_all_configs(
			sql_query.format(">{}".format(split_date)),
			host_query,
			device_host_query,
			device_ssd_query.format("<={}".format(split_date)),
			ssd_query.format(">{}".format(split_date)),
			db_file,
			scale_factor
		)

	return result_dict

def main():
	scale_factors = os.environ['SCALE_FACTORS']
	split_points  = os.environ['SPLIT_POINTS']

	if not scale_factors:
		print("Provide SCALE_FACTORS env var")
		sys.exit(1)
	if not split_points:
		print("Provide SPLIT_POINTS env var")

	scale_factors = scale_factors.split(" ")
	scale_factors = [float(i) for i in scale_factors]

	split_points  = split_points.split(" ")
	split_points  = [float(i) for i in split_points]

	setup_exp()

	for sf in scale_factors:
		for sp in split_points:
			run_bench(sf, sp)


if __name__=="__main__":
	main()