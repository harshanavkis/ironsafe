import sys
import os
import socket
import time

# SERVER_IP=127.0.0.1 SERVER_PORT=5000 python3 policy_client.py user_policy.txt

# docker run --rm  $MOUNT_SGXDEVICE -v "$PWD":/usr/src/myapp -w /usr/src/myapp -e SCONE_HEAP=256M -e SCONE_MODE=HW -e SCONE_ALLOW_DLOPEN=2 -e SERVER_IP=172.17.0.2 -e SERVER_PORT=5000 -e SCONE_ALPINE=1 -e SCONE_VERSION=1 sconecuratedimages/apps:python-3.7-alpine python policy_client.py user_policy.txt

def send_policy_to_server(user_policy):
    # print(len(user_policy))
    # print(os.environ["SERVER_IP"])
    # print(os.environ["SERVER_PORT"])
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((os.environ["SERVER_IP"], int(os.environ["SERVER_PORT"])))
        s.sendall(user_policy.encode())
        # print(user_policy)

        data = s.recv(1024)

        s.close()
    
    # print(data)

def main():
    user_policy = sys.argv[1]
    user_policy = open(user_policy)
    user_policy = user_policy.readline().rstrip()

    start = time.time()
    send_policy_to_server(user_policy)
    end = time.time()

    print(end - start)

if __name__ == "__main__":
    main()