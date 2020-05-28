CC=gcc
CFLAGS=-I../include/
LDFLAGS= -lpthread -ldl

host-ndp: host_server.c host_sqlite3.c
	$(CC) -o host-ndp host_server.c host_sqlite3.c $(CFLAGS) $(LDFLAGS)

.PHONY: clean

clean:
	rm -f host-ndp
