CC=gcc
CFLAGS=-I../../include/
LDFLAGS= -lpthread -ldl -lcrypto -lssl
CPPFLAGS= -DSQLITE_HAS_CODEC

ssd-ndp: sec_ssd_server.c sec_sqlite3.c
	$(CC) -o sec-ssd-ndp sec_ssd_server.c sec_sqlite3.c $(CFLAGS) $(LDFLAGS) $(CPPFLAGS)

.PHONY: clean

clean:
	rm -f sec-ssd-ndp
