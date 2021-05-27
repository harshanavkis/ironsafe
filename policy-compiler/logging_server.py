import os
import socket
import ast

# LOG_FILE=bitch-log SERVER_PORT=5000 python3 logging_server.py

# docker run --rm  $MOUNT_SGXDEVICE -v "$PWD":/usr/src/myapp -w /usr/src/myapp -e SCONE_HEAP=256M -e SCONE_MODE=HW -e SCONE_ALLOW_DLOPEN=2 -e SCONE_ALPINE=1 -e SCONE_VERSION=1 -e SERVER_IP=172.17.0.2 -e LOG_FILE=bitch-log -e SERVER_PORT=5000 sconecuratedimages/apps:python-3.7-alpine python logging_server.py

from execution_logger import log_query_execution

def run_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((os.environ["SERVER_IP"], int(os.environ["SERVER_PORT"])))
        s.listen()

        conn, addr = s.accept()
        with conn:
            # print("Connection from {}".format(addr))
            data = conn.recv(1024)
            
            data = ast.literal_eval(data.decode())
            print(data)

            log_query_execution(data["host_query"], data["storage_query"], data["user_key"])
            conn.send("Success".encode())
        conn.close()
        s.close()

def main():
    run_server()

if __name__ == "__main__":
    main()