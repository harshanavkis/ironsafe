CC=gcc
CFLAGS=-I../../include/
LDFLAGS= -lpthread -ldl -lssl -lcrypto

host-ndp: host_server.c host_sqlite3.c
	$(CC) -o host-ndp host_server.c host_sqlite3.c $(CFLAGS) $(LDFLAGS) -g

.PHONY: clean

clean:
	rm -f $(BUILD)host-ndp
