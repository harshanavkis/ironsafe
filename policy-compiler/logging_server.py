import os
import socket
import ast

from execution_logger import log_query_execution

def run_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', int(os.environ["SERVER_PORT"])))
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