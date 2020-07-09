CC=gcc
CFLAGS=-I../../include/
LDFLAGS= -lpthread -ldl -lcrypto -lssl
CPPFLAGS= -DSQLITE_HAS_CODEC

ssd-ndp: sec_ssd_server.c sec_sqlite3.c ../../serialize/mt_serialize.c
	$(CC) -o sec-ssd-ndp sec_ssd_server.c sec_sqlite3.c ../../serialize/mt_serialize.c $(CFLAGS) $(LDFLAGS) $(CPPFLAGS) ../../merkle-tree/src/libMerkleTree.a -g

.PHONY: clean

clean:
	rm -f sec-ssd-ndp
