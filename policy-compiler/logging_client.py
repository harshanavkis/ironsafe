import sys
import os
import socket
import time

# SERVER_IP=127.0.0.1 SERVER_PORT=5000 python3 logging_client.py

# docker run --rm  $MOUNT_SGXDEVICE -v "$PWD":/usr/src/myapp -w /usr/src/myapp -e SCONE_HEAP=256M -e SCONE_MODE=HW -e SCONE_ALLOW_DLOPEN=2 -e SCONE_ALPINE=1 -e SCONE_VERSION=1 -e SERVER_IP=172.17.0.2 -e SERVER_PORT=5000 sconecuratedimages/apps:python-3.7-alpine python logging_client.py

def send_data_to_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        data = "{\"host_query\": \"bitch\",\"storage_query\": \"bitch\",\"user_key\": \"bitch\"}"
        s.connect((os.environ["SERVER_IP"], int(os.environ["SERVER_PORT"])))
        s.sendall(data.encode())
        # print(user_policy)

        data = s.recv(1024)

        s.close()
    
    # print(data)

def main():
    start = time.time()
    send_data_to_server()
    end = time.time()

    print(end - start)

if __name__ == "__main__":
    main()