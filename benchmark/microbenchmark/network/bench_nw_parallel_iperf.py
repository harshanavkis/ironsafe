import os
import subprocess
import signal
import json
import sys
from datetime import datetime
from contextlib import contextmanager
import pandas as pd
# from threading import Condition, Thread
import multiprocessing

NOW = datetime.now().strftime("%Y%m%d-%H%M%S")
IPERF3_DEFAULT_PORT = 5201

# run server as remote(receiver), and clients locally(sender)
# use receiver bandwidth from client as link bandwidth
# provide REMOTE_IP as env var
# provide REMOTE_SSH_USER

def run_iperf_client(
    iperf_cmd,
    results,
    index
):
    print(f"$ {' '.join(iperf_cmd)}", file=sys.stderr)
    proc = subprocess.run(iperf_cmd, stdout=subprocess.PIPE)

    temp_dict = json.loads(proc.stdout.decode("utf-8"))
    res_dict = temp_dict["end"]["streams"][0]["receiver"]
    res_dict["client"] = index
    results.put(res_dict)

def run_remote_iperf(
    iperf_port
):
    remote_ip   = os.environ["REMOTE_SSH_IP"]
    remote_user = os.environ["REMOTE_SSH_USER"]

    iperf_cmd  = [f"{remote_user}@{remote_ip}", "iperf3", "-s", "-p", iperf_port]
    remote_cmd = ["ssh"]
    remote_cmd += iperf_cmd

    print(remote_cmd)

    proc = subprocess.Popen(remote_cmd, stdout=subprocess.PIPE)
    return proc

def kill_remote_proc(keyword):
    remote_ip   = os.environ["REMOTE_SSH_IP"]
    remote_user = os.environ["REMOTE_SSH_USER"]
    subprocess.run(["ssh", f"{remote_user}@{remote_ip}", "kill", "-9", f"$(pgrep {keyword})"])

def main():
    try:
        num_instances = int(sys.argv[1])
    except Exception as e:
        print("First argument must be an integer")
        sys.exit(1)

    try:
        remote_ip = os.environ["REMOTE_IP"]
    except Exception as e:
        print("Provide REMOTE_IP as env var")
        sys.exit(1)

    base_iperf_command = ["iperf3", "-c", f"{remote_ip}", "--json"]

    # run remote iperf server instances
    remote_iperf_procs = []
    for i in range(num_instances):
        rem_iperf = run_remote_iperf(str(IPERF3_DEFAULT_PORT + i))
        remote_iperf_procs.append(rem_iperf)

    for i in range(num_instances):
        while True:
            try:
                proc = subprocess.run(["nc", "-w1", "-z", "-v", f"{remote_ip}", f"{str(IPERF3_DEFAULT_PORT + i)}"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE)
                if proc.returncode:
                    continue
                break
            except subprocess.CalledProcessError:
                pass

    condition = multiprocessing.Condition()
    threads = []
    results = multiprocessing.Queue()
    for i in range(num_instances):
        iperf_cmd = base_iperf_command + ["-p", str(IPERF3_DEFAULT_PORT + i)]
        thread_args = (iperf_cmd, results, i)
        thread = multiprocessing.Process(target=run_iperf_client, args=thread_args)
        threads.append(thread)

    # with condition:
    #     condition.notify_all()
    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    instances = []
    # for i, result in enumerate(results):
        # instances.append(dict(port=IPERF3_DEFAULT_PORT + i, result=result))
    kill_remote_proc("iperf3")

    res_list = []
    for i in range(num_instances):
        res_list.append(results.get())

    df = pd.DataFrame(res_list)
    df = df.sort_values('client')
    df.to_csv(f"iperf-parallel-{NOW}.csv", index=False)
    # import pdb; pdb.set_trace()


if __name__=="__main__":
    main()