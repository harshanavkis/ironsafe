CC=gcc
CFLAGS=-I../../include/
LDFLAGS= -lpthread -ldl -zmuldefs

host-ndp: host_server.c host_sqlite3.c
	$(CC) -o host-ndp host_server.c host_sqlite3.c $(CFLAGS) $(LDFLAGS) -g

.PHONY: clean

clean:
	rm -f host-ndp
