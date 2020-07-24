CC=gcc
CFLAGS=-I../../include/ -I${OPENSSL_SRC}/include/
LDFLAGS= -lpthread -ldl -lssl -lcrypto

host-ndp: host_server.c host_sqlite3.c
	$(CC) -o host-ndp host_server.c host_sqlite3.c $(CFLAGS) $(LDFLAGS) -L${OPENSSL_SRC} -g

.PHONY: clean

clean:
	rm -f $(BUILD)host-ndp
