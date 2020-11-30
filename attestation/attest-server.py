import socket
import ssl
import subprocess

#server
if __name__ == '__main__':

    HOST = '10.0.210.1'
    PORT = 5000

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(10)

    client, fromaddr = server_socket.accept()
    secure_sock = ssl.wrap_socket(client, server_side=True, ca_certs = "client.pem", certfile="server.pem", keyfile="server.key", cert_reqs=ssl.CERT_REQUIRED,
                           ssl_version=ssl.PROTOCOL_TLSv1_2)

    cert = secure_sock.getpeercert()
    # print(cert)

    # verify client
    if not cert: raise Exception("ERROR")

    try:
        # data = secure_sock.read(1024)
        proc = subprocess.Popen(["sudo", "attestation_storage", "/boot/Image"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        proc.wait()
        secure_sock.write(b'%s'.format(proc.stdout.read()))
    finally:
        secure_sock.close()
        server_socket.close()

    with open('attest_bench.csv', "a") as f:
        f.write(proc.stderr.read())