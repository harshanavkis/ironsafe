import subprocess

def clear_cache():
    print("Clearing page cache...")
    cmd = [
        "sudo sysctl vm.drop_caches=3"
    ]

    for i in cmd:
        proc = subprocess.Popen(i.split(" "))
        proc.wait()
