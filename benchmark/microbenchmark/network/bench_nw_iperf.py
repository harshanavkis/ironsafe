import os
import subprocess
import signal
import json
from datetime import datetime
from contextlib import contextmanager
import pandas as pd

NOW = datetime.now().strftime("%Y%m%d-%H%M%S")

def process_iperf_output(result):
	stats = {}

	print(list(result.keys()))

	if "error" in result:
		print(result["error"], file=sys.stderr)
		sys.exit(1)
	cpu = result["end"]["cpu_utilization_percent"]

	for interval in result["intervals"]:
		for key in cpu.keys():
			if f"cpu_{key}" not in stats:
				stats[f"cpu_{key}"] = []
			stats[f"cpu_{key}"].append(cpu[key])

		moved_bytes = 0
		seconds = 0.0
		for stream in interval["streams"]:
			moved_bytes += stream["bytes"]
			seconds += stream["seconds"]

		seconds /= len(interval["streams"])

		start = int(interval["streams"][0]["start"])
		if "interval" not in stats:
			stats["interval"] = []
		stats["interval"].append(start)

		if "bytes" not in stats:
			stats["bytes"] = []
		stats["bytes"].append(moved_bytes)

		if "seconds" not in stats:
			stats["seconds"] = []
		stats["seconds"].append(seconds)

		if "bits_per_sec" not in stats:
			stats["bits_per_sec"] = []
		stats["bits_per_sec"].append(interval["streams"][0]["bits_per_second"])

	return stats

@contextmanager
def spawn_host_iperf(cmd):
	proc = subprocess.Popen(cmd)

	try:
		yield proc
	finally:
		print("Terminating iperf")
		proc.send_signal(signal.SIGINT)
		proc.wait()

def remote_iperf_run(cmd, storage_server, remote_user):
	remote_cmd = ["ssh", f"{remote_user}@{storage_server}"]
	remote_cmd.append(cmd)
	proc = subprocess.run(cmd, stdout=subprocess.PIPE)

	return proc

def main():
	host_iperf     = ['iperf3', '-s']
	storage_server = os.environ['STORAGE_SERVER_IP']
	remote_user    = os.environ['REMOTE_USER']
	host_ip        = os.environ['HOST_IP']

	with spawn_host_iperf(host_iperf):
		while True:
			try:
				proc = remote_iperf_run(
					[
						"iperf3",
						"-c",
						host_ip,
						"--json",
					],
					storage_server,
					remote_user
				)
				break
			except subprocess.CalledProcessError:
				print(".")
				pass
		stats = process_iperf_output(json.loads(proc.stdout))

	csv = f"iperf-{NOW}.csv"
	pd.DataFrame(stats).to_csv(csv, index=False)


if __name__=="__main__":
	main()