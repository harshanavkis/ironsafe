import sys
import os
import socket

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
    send_data_to_server()    

if __name__ == "__main__":
    main()