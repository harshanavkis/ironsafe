#ifndef SSD_SERVER_H
#define SSD_SERVER_H

#include <semaphore.h>
#include <openssl/ssl.h>
#include <openssl/err.h>
#include "sqlite3.h"

#define SSD_SEND_PORT 5000
#define RECV_BUF_SIZE 1024*1024*1
#define REC_POOL_SIZE 1048576
#define MK_REC_POOL_SIZE 1048576

#define DB_PATH "TPC-H-fresh.db"

char *schema_cmd;

int rows_processed;
int sqlite_step_time;

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
	char serial_data[RECV_BUF_SIZE - sizeof(packet_type) - sizeof(int)];
} record_batch;

sem_t ssd_full, ssd_empty, ssd_mutex;

/* DECL: producer consumer stuff */
typedef struct
{
	int size;
	char *record;
} mem_serial;

typedef struct
{
	unsigned long head;
	unsigned long tail;
	mem_serial *record_pool;
	int done;
} prod_cons_ssd;

typedef struct
{
	int socket;
} c_args_ssd;

typedef struct
{
	sqlite3 *db;
	char subquery[4096];
} p_args_ssd;

prod_cons_ssd pcs_state;

typedef struct sqlite3_value Mem;

typedef struct mk_rec {
  Mem **rec_queue;
  unsigned long head;
  unsigned long tail;
  int done;
} mk_rec;

mk_rec mk_rec_state;

// extern int size_Mem;

void serialize_before_send(char* dest, record_batch *ssd_record);
void free_sqlite_mem(void *pMem);
int ssd_serialize_wrapper(char **dest, void *ssd_record);
void make_ssd_record();

#endif /* SSD_SERVER_H */
