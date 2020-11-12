import subprocess
import os

'''
    - 40GbE network
    - block device in ram on storage server
    - nfs
        - ram block device
        - nvme device

    - env var:
        - REMOTE_USER
        - STORAGE_SERVER_IP
        - REMOTE_IF_NAME
        - REMOTE_NIC_IP
        - NETMASK
        - REMOTE_SRC
'''

def remote_cmd(args):
    remote_user = os.environ["REMOTE_USER"]
    remote_ip   = os.environ["STORAGE_SERVER_IP"]

    rem_cmd = ["ssh", f"{remote_user}@{remote_ip}"]
    rem_cmd += args

    proc = subprocess.Popen(rem_cmd)
    proc.wait()


def setup_network():
    #setup remote
    remote_interface = os.environ["REMOTE_IF_NAME"]
    remote_nic_ip    = os.environ["REMOTE_NIC_IP"]
    netmask          = os.environ["NETMASK"]
    rem_cmds = [
        f"sudo ip link set {remote_interface} up",
        f"sudo ip addr flush dev {remote_interface}",
        f"sudo ip addr add {remote_nic_ip}/{netmask} dev {remote_interface}",
        f"sudo ip link set {remote_interface} mtu 1500",
        f"sudo ip link set {remote_interface} up"
    ]

    for i in rem_cmds:
        remote_cmd(i.split(" "))

    # setup local
    local_interface = os.environ["LOCAL_IF_NAME"]
    local_nic_ip    = os.environ["LOCAL_NIC_IP"]

    local_cmds = [
        f"sudo ip link set {local_interface} up",
        f"sudo ip addr flush dev {local_interface}",
        f"sudo ip addr add {local_nic_ip}/{netmask} dev {local_interface}",
        f"sudo ip link set {local_interface} mtu 1500",
        f"sudo ip link set {local_interface} up"
    ]

    for i in local_cmds:
        proc = subprocess.Popen(i.split(" "))
        proc.wait()

def setup_nvme_tcp():
    remote_nic_ip = os.environ["REMOTE_NIC_IP"]
    remote_src    = os.environ["REMOTE_SRC"]

    rem_cmd = [os.path.join(remote_src, "benchmark/setup_nvme_tcp_target.sh"), f"{remote_nic_ip}"]
    remote_cmd(rem_cmd)

    nvme_discover = ["sudo", "nvme", "discover", "-t", "tcp", "-a", f"{remote_nic_ip}", "-s", "4420"]
    proc = subprocess.Popen(nvme_discover)
    proc.wait()

    nvme_connect = ["sudo", "nvme", "connect", "-t", "tcp", "-n", "secndp", "-a", f"{remote_nic_ip}", "-s", "4420"]
    proc = subprocess.Popen(nvme_connect)
    proc.wait()

def mount_nvme_dir(mount_point):
    if not os.path.isdir(os.path.abspath(mount_point)):
        os.mkdir(os.path.abspath(mount_point))


    mount_cmd = ["sudo", "mount", "-U", f"{uuid}", f"{mount_point}"]
    # TODO: figure out nvme namespace

def setup_rem_blk_ram():
    pass

def main():
    setup_network()

if __name__=="__main__":
    main()
