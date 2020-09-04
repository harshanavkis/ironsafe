import subprocess
import os
import re
import pandas as pd
import signal
from contextlib import contextmanager
from collections import defaultdict

def process_qperf_output(proc_stdout):
    stats = defaultdict(list)

    for line in proc_stdout:
        match = re.match(r"\s+(.*)  =  (.*)", line)
        if match:
            stats[match.group(1)].append(match.group(2))

    return stats

@contextmanager
def spawn_host_qperf(cmd):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True)

    try:
        yield proc
    finally:
        print("Terminating qperf")
        proc.send_signal(signal.SIGINT)
        proc.wait()

def remote_qperf_run(cmd, storage_server, remote_user):
    remote_cmd = ["ssh", f"{remote_user}@{storage_server}"]
    remote_cmd.append(cmd)
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
    return proc

def main():
    host_qperf = ["qperf"]
    storage_server = os.environ['STORAGE_SERVER_IP']
    remote_user    = os.environ['REMOTE_USER']
    host_ip        = os.environ['HOST_IP']

    with spawn_host_qperf(host_qperf):
        while True:
            try:
                proc = remote_qperf_run(
                        [
                            "qperf",
                            host_ip,
                            "tcp_bw",
                            "tcp_lat"
                        ],
                        storage_server,
                        remote_user
                    )
                break
            except subprocess.CalledProcessError:
                print(".")
                pass
        import pdb; pdb.set_trace()
        stats = process_qperf_output(proc.stdout.split('\n'))

    df = pd.DataFrame(stats)
    df.to_csv("qperf-test.csv", index=False)

if __name__=="__main__":
    main()