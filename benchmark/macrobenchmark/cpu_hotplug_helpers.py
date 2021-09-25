import os
import subprocess

CURR_PATH = os.path.realpath(".")

def setup_remote_cpu_hotplug(cpu_hotplug, env):
    rem_cpus = []
    for i in range(15, cpu_hotplug - 1, -1):
        rem_cpus.append(str(i))
    rem_cpus = " ".join(rem_cpus)
    env["SHUTDOWN_CPUS"] = rem_cpus
    print("Shutting down cpus: {}".format(rem_cpus))
    cmd = [os.path.join(CURR_PATH, "./setup_remote_cpu_hotplug_remove.sh"), "{}".format(rem_cpus)]
    subprocess.run(cmd, env=env)

def teardown_remote_cpu_hotplug(env):
    cmd = [os.path.join(CURR_PATH, "./reset_cpu_hotplug_config.sh")]
    subprocess.run(cmd, env=env)
