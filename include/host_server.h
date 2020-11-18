#ifndef HOST_SERVER_H
#define HOST_SERVER_H

#include <semaphore.h>
#include <openssl/ssl.h>
#include <openssl/err.h>

#define SSD_SEND_PORT 5000 /* port from which storage server sends data */
#define HOST_LISTEN_PORT 5003
#define SSD_ADDRESS "172.17.0.1"

#define RECV_BUF_SIZE 1024*1024*2
#define BUF_POOL_SIZE 64

typedef struct query_opts
{
  char *outer_query;
  char *sub_query;
  char *db;
} query_opts;

query_opts ndp_opts;

int table_n_cols;

typedef enum
{
	REC_PKT,
	TAB_PKT,
	END_PKT
} packet_type;

int payload_size;

typedef struct
{
	packet_type pkt_type;
	int num_records; /* valid if packet type if REC_PKT */
	char *serial_data;
} record_batch;

sem_t full, empty, host_mutex;

/* DECL: producer consumer stuff */
typedef struct
{
	unsigned long head;
	unsigned long tail;
	record_batch* record_pool[BUF_POOL_SIZE];
} prod_cons;

prod_cons pc_state;
/***************************/

typedef struct
{
	int socket;
} p_args;

typedef struct
{
	sqlite3* db;
} c_args;

void batch_deserialize_add(sqlite3 *db, void **pC, record_batch *ssd_record, int n_cols);
int col_count(char *sql);

#endif /*HOST_SERVER_H*/
