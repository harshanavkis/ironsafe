import sys
import socket
import json
import os

from policy_compiler import compile_policy
from policy_checker import check_policy, check_node_policy_compliance

def run_server(storage_attr_json):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', int(os.environ["SERVER_PORT"])))
        s.listen()

        conn, addr = s.accept()
        with conn:
            # print("Connection from {}".format(addr))
            user_policy = ''
            data = conn.recv(1024)
            # print(data)
            user_policy += data.decode()
            user_policy = compile_policy(user_policy)

            # TODO: Add a return value
            check_policy(user_policy)

            if not check_node_policy_compliance(user_policy, storage_attr_json):
                conn.sendall("Failure".encode())
            else:
                conn.send("Success".encode())
        conn.close()
        s.close()


def main():
    storage_attr_json = sys.argv[1]
    storage_attr_json = open(storage_attr_json)
    storage_attr_json = json.load(storage_attr_json)

    run_server(storage_attr_json)


if __name__ == "__main__":
    main()