import sys
import json
import pandas as pd

def json_to_csv(data, file_name):
	jsondata = json.loads(data)
	stats = {}
	for jobnum, job in enumerate(jsondata["jobs"]):
		if "job" not in stats:
			stats["job"] = []
		stats["job"].append(jobnum)
		for op in ["read", "write", "trim"]:
			metrics = job[op]
			for metric_name, metric in metrics.items():
				if isinstance(metric, dict):
					for name, submetric in metric.items():
						if f"{op}-{metric_name}-{name}" not in stats:
							stats[f"{op}-{metric_name}-{name}"] = []
						stats[f"{op}-{metric_name}-{name}"].append(submetric)
				else:
					if f"{op}-{metric_name}" not in stats:
						stats[f"{op}-{metric_name}"] = []
					stats[f"{op}-{metric_name}"].append(metric)

	throughput_df = pd.DataFrame(stats)
	throughput_df.to_csv(file_name, index=False)

def main():
	fio_type   = sys.argv[1]
	fio_output = sys.argv[2].split('\n')

	data = ""
	in_json = False

	for line in fio_output:
		if line == "{":
			in_json = True
		if in_json:
			data += line
		if line == "}":
			break

	json_to_csv(data, fio_type+".csv")


if __name__=="__main__":
	main()