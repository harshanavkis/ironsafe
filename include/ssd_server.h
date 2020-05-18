#ifndef SSD_SERVER_H
#define SSD_SERVER_H

#include <semaphore.h>

#define SSD_SEND_PORT 5000
#define RECV_BUF_SIZE 1024*4
#define REC_POOL_SIZE 4*1024*1024

#define DB_PATH "../../TPC-H.db"

char *schema_cmd;

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
	int head;
	int tail;
	mem_serial record_pool[REC_POOL_SIZE];
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

void serialize_before_send(char* dest, record_batch *ssd_record);
void free_sqlite_mem(void *pMem);
int ssd_serialize_wrapper(char **dest, void *ssd_record);

#endif /* SSD_SERVER_H */