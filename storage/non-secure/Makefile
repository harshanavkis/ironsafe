CC=gcc
CFLAGS=-I../../include/
LDFLAGS= -lpthread -ldl -zmuldefs

ssd-ndp: ssd_server.c ssd_sqlite3.c
	$(CC) -o ssd-ndp ssd_server.c ssd_sqlite3.c $(CFLAGS) $(LDFLAGS) -g

.PHONY: clean

clean:
	rm -f ssd-ndp
