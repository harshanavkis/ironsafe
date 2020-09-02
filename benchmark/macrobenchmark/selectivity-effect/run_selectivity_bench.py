import sys
import os
import subprocess
from contextlib import contextmanager
from pathlib import Path
import time
from io import StringIO

from selectivity_split import determine_split

import pdb

stdout=subprocess.PIPE

sql_query = "select l_returnflag, l_linestatus, sum(l_quantity) as sum_qty, sum(l_extendedprice) as sum_base_price, sum(l_extendedprice*(1 - l_discount)) as sum_disc_price, sum(l_extendedprice*(1 - l_discount)*(1 + l_tax)) as sum_charge, avg(l_quantity) as avg_qty, avg(l_extendedprice) as avg_price, avg(l_discount) as avg_disc, count(*) as count_order from LINEITEM where l_shipdate {};"

host_query = "select l_returnflag, l_linestatus, sum(l_quantity) as sum_qty, sum(l_extendedprice) as sum_base_price, sum(l_extendedprice*(1 - l_discount)) as sum_disc_price, sum(l_extendedprice*(1 - l_discount)*(1 + l_tax)) as sum_charge, avg(l_quantity) as avg_qty, avg(l_extendedprice) as avg_price, avg(l_discount) as avg_disc, count(*) as count_order from TABLE1;"

ssd_query = "select l_returnflag, l_linestatus,l_quantity, l_extendedprice, l_discount, l_tax from LINEITEM where l_shipdate {};"

device_host_query = "select l_returnflag, l_linestatus, sum_qty, sum_base_price, sum_disc_price, sum_charge, avg_qty, avg_price, avg_disc, count_order from TABLE1;"

device_ssd_query  = "select l_returnflag, l_linestatus, sum(l_quantity) as sum_qty, sum(l_extendedprice) as sum_base_price, sum(l_extendedprice*(1 - l_discount)) as sum_disc_price, sum(l_extendedprice*(1 - l_discount)*(1 + l_tax)) as sum_charge, avg(l_quantity) as avg_qty, avg(l_extendedprice) as avg_price, avg(l_discount) as avg_disc, count(*) as count_order from LINEITEM where l_shipdate {};"

ROOT_DIR = os.path.realpath("../../../")
CURR_DIR = os.path.realpath(".")
DB_DIR = os.path.realpath("../../../tpch/build/TPCH-{}.db")
REM_DB_NAME = "tpch/build/TPCH-{}.db"
NVME_TCP_DIR = ""
DB_FILE_NAME   = "TPCH-{}.db"
FRESH_DB_NAME  = "TPCH-{}-fresh-enc.db"
MERK_FILE_NAME = "merkle-tree-{}.bin"

"""
	Environment variables:
		- REMOTE_SRC
		- STORAGE_SERVER_IP
		- REMOTE_USER
		- SCALE_FACTORS
		- SPLIT_POINTS
"""
def process_host_ndp_output(res):
	return res

def run_local_proc(cmd, env=None):
	proc = subprocess.run(cmd, stdout=stdout, env=env)
	return proc

def setup_exp():
	os.chdir(f"{ROOT_DIR}/host/non-secure/")
	cmd = ["make"]
	proc = run_local_proc(cmd)
	# proc.wait()

	os.chdir(f"{ROOT_DIR}/openssl-src/")
	cmd = ["./Configure"]
	proc = run_local_proc(cmd)
	# proc.wait()

	cmd = ["make"]
	proc = run_local_proc(cmd)
	# proc.wait()

	cmd = ["docker", "image", "inspect", "host-ndp:latest"]
	proc = run_local_proc(cmd)
	# proc.wait()

	os.chdir(ROOT_DIR)
	if proc.returncode == 1:
		cmd = ["docker", "build", "-f", f"{ROOT_DIR}/benchmark/scone-stuff/sec-ndp", "-t", "host-ndp", f"{ROOT_DIR}/"]
		run_local_proc(cmd)
		# proc.wait()

	cmd = ["docker", "image", "inspect", "pure-host-sec:latest"]
	proc = run_local_proc(cmd)
	# proc.wait()

	if proc.returncode == 1:
		cmd = ["docker", "build", "-f", f"{ROOT_DIR}/benchmark/scone-stuff/pure-host-sec", "-t", "pure-host-sec", f"{ROOT_DIR}/"]
		run_local_proc(cmd)
		# proc.wait()

	os.chdir(f"{ROOT_DIR}/fresh-sqlite")
	make_env = os.environ.copy()
	make_env["SCONE"] = "false"
	make_env["OPENSSL_SRC"] = f"{ROOT_DIR}/openssl-src"	
	cmd = ["make", "clean"]
	run_local_proc(cmd)
	cmd = ["make", "hello-query"]
	run_local_proc(cmd, make_env)

	# TODO: Correctly setup nvme over tcp and mount drive
	NVME_TCP_DIR = os.path.join(ROOT_DIR, "tpch/build")

	os.chdir(CURR_DIR)

def process_pure_host_output(proc_stdout):
	print("Bitch")
	print(proc_stdout)
	for line in proc_stdout:
		try:
			data = json.loads(line)
			data = pd.DataFrame(data)
			print(data)
			return data
		except Exception as e:
			continue

def run_pure_host_non_secure(cq, db_file, scale_factor):
	local_cmd = [
		"./run_pure_host_non_secure.sh",
		os.path.join(os.path.join(ROOT_DIR, "tpch/build"), MERK_FILE_NAME.format(scale_factor)),
		os.path.join(os.path.join(ROOT_DIR, "tpch/build"), DB_FILE_NAME.format(scale_factor)),
		f"{cq}"
	]
	print(local_cmd)

	proc = subprocess.run(local_cmd, stdout=stdout, text=True)
	return process_pure_host_output(proc.stdout)

def run_pure_host_secure(cq, db_file, scale_factor):
	local_cmd = [
		"docker",
		"run",
		"--mount",
		f"type=bind,source={ROOT_DIR}/tpch/build,target=/data",
		"pure-host-sec",
		"/bin/bash",
		"-c",
		"SCONE_VERSION=1 SCONE_HEAP=2G ./hello-query /data/{} /data/{} kun \"{}\"".format(MERK_FILE_NAME.format(scale_factor), FRESH_DB_NAME.format(scale_factor), cq)
	]
	proc = subprocess.run(local_cmd, stdout=stdout, text=True)
	# proc.wait()
	return process_pure_host_output(proc.stdout)

def run_vanilla_ndp_non_secure(hq, sq, db_file, scale_factor):
	proc = subprocess.run(["./selectivity_ndp.sh", f"{scale_factor}", "non-secure", hq, sq], stdout=stdout, text=True)
	# proc.wait()

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

def run_secure_device_only(dhq, dsq, scale_factor):
	remote_proc = subprocess.run(["./selectivity_sec_ndp.sh", f"{scale_factor}", "secure"], stdout=stdout, text=True)

	time.sleep(5)
	remote_ip = os.environ["STORAGE_SERVER_IP"]
	if remote_ip == "127.0.0.1":
		remote_ip = "172.17.0.1"

	local_cmd = ["docker", "run", "host-ndp", "/bin/bash", "-c", "cd /sqlite-ndp/host/secure/ && ./host-ndp -D .. -Q \"{}\" -S \"{}\" {}".format(dhq, dsq, remote_ip)]
	local_proc = subprocess.Popen(local_cmd, stdout=stdout, text=True)
	local_proc.wait()

	kill_proc = subprocess.run(["./kill_rem_process.sh"], env=os.environ)

	return process_host_ndp_output(local_proc.stdout.read())

def run_all_configs(cq, hq, sq, dhq, dsq, db_file, scale_factor):
	print("Running pure host non-secure...")
	phns = run_pure_host_non_secure(cq, db_file, scale_factor)

	print("Running pure host secure...")
	phs  = run_pure_host_secure(cq, db_file, scale_factor)
	# vnns = run_vanilla_ndp_non_secure(hq, sq, db_file, scale_factor)
	# sns  = run_secure_ndp_secure(hq, sq, scale_factor)
	# sss  = run_secure_device_only(dhq, dsq, scale_factor)

	# return [phns, phs, vnns, sns, sss]
	return [phns, phs]

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

def save_to_csv(result_dict, scale_factor, f_names):
	for selectivity in result_dict:
		temp_f_names = [i.format(selectivity, scale_factor) for i in f_names]
		data = result_dict[selectivity][:2]
		for i in range(len(data)):
			result_dict[selectivity][i].to_csv(temp_f_names[i], index=False)


def result_to_csv(result_dict, scale_factor, f_names):
	for selectivity in result_dict:
		temp_f_names = [i.format(selectivity, scale_factor) for i in f_names]
		sel_res = result_dict[selectivity][2:]

		for i in range(len(sel_res)):
			csv_data = StringIO(sel_res[i])
			df = pd.read_csv(csv_data, sep=',', header=None, index=False)
			df.to_csv(temp_f_names[i], header=None, index=False)		

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

	res_f_names = [
		"phns-{}-scale-{}.csv",
		"phs-{}-scale-{}.csv",
		"vnns-{}-scale-{}.csv",
		"sns-{}-scale-{}.csv",
		"sss-{}-scale-{}.csv"
	]	

	for sf in scale_factors:
		for sp in split_points:
			result_dict = run_bench(sf, sp)
			# result_to_csv(result_dict, sf, res_f_names[2:])
			# save_to_csv(result_dict, sf, res_f_names[:2])


if __name__=="__main__":
	main()