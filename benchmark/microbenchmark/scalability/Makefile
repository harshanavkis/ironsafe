CC=gcc
CFLAGS=-I${OPENSSL_SRC}/include/ -I../../../include/ -I../../../merkle-tree/src/ -I../../../include/mt_include/
LDFLAGS= -lpthread -ldl -lcrypto -lssl
CPPFLAGS= -DSQLITE_HAS_CODEC

all: multi-sqlite multi-sqlite-same-data

multi-sqlite: multi_sqlite.c ../../../storage/secure/sec_sqlite3.c
	$(CC) -o multi-sqlite multi_sqlite.c ../../../storage/secure/sec_sqlite3.c ../../../serialize/mt_serialize.c $(CFLAGS) $(LDFLAGS) $(CPPFLAGS) ../../../merkle-tree/src/libMerkleTree.a -g

multi-sqlite-same-data: multi_sqlite_same_data.c ../../../storage/secure/sec_sqlite3.c
	$(CC) -o multi-sqlite-same-data multi_sqlite_same_data.c ../../../storage/secure/sec_sqlite3.c ../../../serialize/mt_serialize.c $(CFLAGS) $(LDFLAGS) $(CPPFLAGS) ../../../merkle-tree/src/libMerkleTree.a -g

clean:
	rm multi-sqlite multi-sqlite-same-data
