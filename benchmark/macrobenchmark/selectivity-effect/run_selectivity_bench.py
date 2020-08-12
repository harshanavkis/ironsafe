import sys
import os
import subprocess

from selectivity_split import determine_split

sql_query = "select l_returnflag, l_linestatus, sum(l_quantity) as sum_qty, sum(l_extendedprice) as sum_base_price, sum(l_extendedprice * (1 - l_discount)) as sum_disc_price, sum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge, avg(l_quantity) as avg_qty, avg(l_extendedprice) as avg_price, avg(l_discount) as avg_disc, count(*) as count_order from LINEITEM where l_shipdate {};"

host_query = "select l_returnflag, l_linestatus, sum(l_quantity) as sum_qty, sum(l_extendedprice) as sum_base_price, sum(l_extendedprice * (1 - l_discount)) as sum_disc_price, sum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge, avg(l_quantity) as avg_qty, avg(l_extendedprice) as avg_price, avg(l_discount) as avg_disc, count(*) as count_order from TABLE1;"

ssd_query = "select l_returnflag, l_linestatus,l_quantity, l_extendedprice, l_discount, l_tax from LINEITEM where l_shipdate {};"

device_host_query = "select l_returnflag, l_linestatus, sum_qty, sum_base_price, sum_disc_price, sum_charge, avg_qty, avg_price, avg_disc, count_order from TABLE1;"

device_ssd_query  = "select l_returnflag, l_linestatus, sum(l_quantity) as sum_qty, sum(l_extendedprice) as sum_base_price, sum(l_extendedprice * (1 - l_discount)) as sum_disc_price, sum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge, avg(l_quantity) as avg_qty, avg(l_extendedprice) as avg_price, avg(l_discount) as avg_disc, count(*) as count_order from LINEITEM where l_shipdate {};"

DB_DIR = "../../../tpch/build/TPCH-{}.db"

def run_all_configs(cq, hq, sq, dhq, dsq, db_file):
	phns = run_pure_host_non_secure(cq, db_file)
	phs  = run_pure_host_secure(cq, db_file)
	vnns = run_vanilla_ndp_non_secure(hq, sq, db_file)
	sns  = run_secure_ndp_secure(hq, sq, db_file)
	sss  = run_secure_device_only(dhq, dsq, db_file)

	return [phns, phs, vnns, sns]


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
		device_ssd_query.format("<={}".format(split_date))
		db_file
	)

	if upper_sel != lower_sel:
		result_dict[lower_sel] = run_all_configs(
			sql_query.format(">{}".format(split_date)),
			host_query,
			device_host_query,
			device_ssd_query.format("<={}".format(split_date))
			ssd_query.format(">{}".format(split_date)),
			db_file
		)

	return result_dict

def main():
	scale_factors = os.environ(['SCALE_FACTORS'])
	split_points  = os.environ(['SPLIT_POINTS'])

	if not scale_factors:
		print("Provide SCALE_FACTORS env var")
		sys.exit(1)
	if not split_points:
		print("Provide SPLIT_POINTS env var")

	scale_factors = scale_factors.split(" ")
	scale_factors = [float(i) for i in scale_factors]

	split_points  = split_points.split(" ")
	split_points  = [float(i) for i in split_points]

	for sf in scale_factors:
		for sp in split_points:
			run_bench(sf, sp)


if __name__=="__main__":
	main()