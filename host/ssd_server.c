#include <stdio.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <stdlib.h>
#include <errno.h>
#include <string.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <netinet/in.h>
#include <pthread.h>

#include "sqlite3.h"
#include "ssd_server.h"
#include "common_globals.h"

void make_query_string(char *dest, char *start, char *middle, char *end)
{
  middle[strlen(middle) - 1] = 0;
  sprintf(dest, "%s %s %s", start, middle, end);
}

int schema_callback(void *n, int argc, char **argv, char **azColName)
{
  schema_cmd = (char*) malloc(strlen(argv[0])+1);
  sprintf(schema_cmd, "%s;", argv[0]);
  // printf("%s\n", schema_cmd);
  return 0;
}

int packets_sent = 0;
int rows_processed = 0;
int check_rows_proc = 0;

int dummy_callback(void *n, int argc, char **argv, char **azColName)
{
  rows_processed++;
  return 0;
}

void serialize_before_send(char *dest, record_batch *ssd_record)
{
	// char *res = (char*) malloc(RECV_BUF_SIZE);
	void *temp = dest;
	*((packet_type*)temp) = ssd_record->pkt_type;
	temp = (packet_type*)temp + 1;
	*((int*)temp) = ssd_record->num_records;
	temp = (int*)temp + 1;
	temp = memcpy((char*)temp, ssd_record->serial_data, payload_size);
}

void *producer_func(void *args)
{
  printf("In producer thread\n");
  p_args_ssd *producer_args = (p_args_ssd*) args;
  int ret;
  char *zErrMsg;

  make_record = 1;

  ret = sqlite3_exec(producer_args->db, producer_args->subquery, dummy_callback, 0, &zErrMsg);
  if (ret != SQLITE_OK)
  {
    fprintf(stderr, "SQL error: %s\n", zErrMsg);
    sqlite3_free(zErrMsg);
  }
  pcs_state.done = 1;
}

void *consumer_func(void* args)
{
  c_args_ssd *consumer_args = (c_args_ssd*) args;
  record_batch rec_pkt;
  char batch_pkt[RECV_BUF_SIZE];
  int len, nbuffer;

	for(;;)
  {
    if(pcs_state.done && (pcs_state.head == pcs_state.tail))
      break;
    char *dest;
    rec_pkt.pkt_type = REC_PKT;
    int window = RECV_BUF_SIZE;
    if (sem_wait(&ssd_full))
    { 
      /* wait */
      printf("Error: sem wait fail\n");
      pthread_exit(NULL);
    }

    if (sem_wait(&ssd_mutex))
    { 
      /* wait */
      printf("Error: sem mutex lock fail\n");
      pthread_exit(NULL);
    }

    int sbytes = pcs_state.record_pool[pcs_state.head].size;
    memcpy(rec_pkt.serial_data, pcs_state.record_pool[pcs_state.head].record, sbytes);
    pcs_state.head += 1;
    rec_pkt.num_records = 1;
    window -= sbytes;

    if (sem_post(&ssd_mutex))
    { 
      /* wait */
      printf("Error: sem mutex unlock fail\n");
      pthread_exit(NULL);
    }

    if (sem_post(&ssd_empty)) 
    { 
    /* post */
      printf("Error: sem post fail\n");
      pthread_exit(NULL);
    }

    // batch_pkt = serialize_before_send(&batch_pkt, &rec_pkt);
    serialize_before_send(batch_pkt, &rec_pkt);
    check_rows_proc += rec_pkt.num_records;

    len = 0;
    nbuffer = 0;

    while(nbuffer < RECV_BUF_SIZE)
    {
      len = send(consumer_args->socket, batch_pkt + nbuffer, RECV_BUF_SIZE - nbuffer, 0);
      nbuffer += len;
    }
    packets_sent += 1;
  }

  rec_pkt.pkt_type = END_PKT;
  // batch_pkt = serialize_before_send(&rec_pkt);
  serialize_before_send(batch_pkt, &rec_pkt);
  len = nbuffer = 0;
  while(nbuffer < RECV_BUF_SIZE)
  {
    len = send(consumer_args->socket, batch_pkt + nbuffer, RECV_BUF_SIZE - nbuffer, 0);
    nbuffer += len;
  }
}

int main(int argc, char const *argv[])
{
  make_ssd_records_proc = 0;
	/* DECL: socket stuff */
	int server_fd, new_socket;
	struct sockaddr_in address;
	int opt = 1;
	int addrlen = sizeof(address);
	int len, nbuffer;
	record_batch gen_schema;
  payload_size = RECV_BUF_SIZE - sizeof(packet_type) - sizeof(int);
  /****************/

  /* DECL: sqlite stuff */
	int ret;
	int out_str_len = 0;
	sqlite3 *db;
	char *zErrMsg = 0;
	char subquery[4096];
	char *create_table_cmd = "CREATE TABLE TABLE1 AS";
  char *limit_cmd = "LIMIT 0;";
  char *create_table_select;
  char schema_send_ser[RECV_BUF_SIZE];
	/**********************/

	/* DECL: thread stuff */
	pthread_t consumer, producer;
  c_args_ssd consumer_args;
  p_args_ssd producer_args;
	pcs_state.head = 0;
  pcs_state.tail = 0;
  pcs_state.done = 0;
	/**********************/

	/* socket init stuff */
  if ((server_fd = socket(AF_INET, SOCK_STREAM, 0)) == 0) 
  { 
    perror("socket failed"); 
    exit(EXIT_FAILURE); 
  }
  if (setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR | SO_REUSEPORT, 
                                                  &opt, sizeof(opt))) 
  { 
    perror("setsockopt"); 
    exit(EXIT_FAILURE);
  } 
  address.sin_family = AF_INET; 
  address.sin_addr.s_addr = INADDR_ANY; 
  address.sin_port = htons( SSD_SEND_PORT );
  if (bind(server_fd, (struct sockaddr *)&address,  
                                 sizeof(address))<0) 
  { 
    perror("bind failed"); 
    exit(EXIT_FAILURE); 
  }
  if (listen(server_fd, 1) < 0) 
  { 
    perror("listen"); 
    exit(EXIT_FAILURE);
  }

  if ((new_socket = accept(server_fd, (struct sockaddr *)&address,  
                       (socklen_t*)&addrlen))<0) 
  { 
    perror("accept"); 
    exit(EXIT_FAILURE);
  }
  /**********************/

  /* Connect to database */
  ret = sqlite3_open(DB_PATH, &db);
  if (ret)
  {
    fprintf(stderr, "Can't open database: %s\n", sqlite3_errmsg(db));
    sqlite3_close(db);
    return 1;
  }
  /***********************/

  /* Get subquery and generate the command for create table */
  len = nbuffer = 0;
  while(nbuffer < RECV_BUF_SIZE)
  {
  	len = recv (new_socket, subquery + nbuffer, RECV_BUF_SIZE-nbuffer, 0);
  	nbuffer += len;
  }

  out_str_len = strlen(create_table_cmd)+strlen(limit_cmd)+strlen(subquery);
  if(out_str_len >= (2*strlen(subquery)))
  {
    out_str_len += 1;
  }
  else
  {
    out_str_len = 2*strlen(subquery);
  }

  create_table_select = (char*) malloc(out_str_len);
  make_query_string(create_table_select, create_table_cmd, subquery, limit_cmd);
  /**********************************************************/

  /* Create temp table and generate its sql query, send sql query to host */
  ret = sqlite3_exec(db, create_table_select, NULL, 0, &zErrMsg);
  if (ret)
  {
    fprintf(stderr, "Can't create temp table TABLE1: %s\n", sqlite3_errmsg(db));
    sqlite3_close(db);
    return 1;
  }

  ret = sqlite3_exec(db, "SELECT sql FROM sqlite_master where tbl_name=\'TABLE1\';", schema_callback, 0, &zErrMsg);
  if (ret)
  {
    fprintf(stderr, "Can't extract sql of table TABLE1: %s\n", sqlite3_errmsg(db));
    sqlite3_close(db);
    return 1;
  }

  gen_schema.pkt_type = TAB_PKT;
  gen_schema.num_records = -1;
  memcpy(gen_schema.serial_data, schema_cmd, strlen(schema_cmd) + 1);
  // gen_schema.serial_data = schema_cmd;

  serialize_before_send(schema_send_ser, &gen_schema);

  len = 0;
  nbuffer = 0;

  while(nbuffer < RECV_BUF_SIZE)
  {
  	len = send(new_socket, schema_send_ser + nbuffer, RECV_BUF_SIZE - nbuffer, 0);
  	nbuffer += len;
  }
  /************************************************/

  /* Semaphore and mutex init */
  if (sem_init(&ssd_empty, 0, REC_POOL_SIZE)) 
  {
    printf("Error: semaphore not initialize\n");
    return -1;
  }

  if (sem_init(&ssd_full, 0, 0)) 
  {
    printf("Error: semaphore not initialize\n");
    return -1;
  }

  if (sem_init(&ssd_mutex, 0, 1)) 
  {
    printf("Error: semaphore not initialize\n");
    return -1;
  }
  /******************/

  /* create consumer threads
   * one producer: exec and add resultrow stuff to the queue
   * producer thread is the main thread itself, makerecord
   * one consumer: serialize record and batch them
   */
  consumer_args.socket = new_socket;
  producer_args.db = db;
  memcpy(producer_args.subquery, subquery, strlen(subquery) + 1);

  ret = pthread_create(&producer, NULL, producer_func, &producer_args);
  if(ret)
  {
    fprintf(stderr, "Unable to create producer thread.\n");
    return 1;
  }
  ret = pthread_create(&consumer, NULL, consumer_func, &consumer_args);
  if(ret)
  {
  	fprintf(stderr, "Unable to create consumer thread.\n");
  	return 1;
  }
  /****************************************/

  pthread_join(consumer, NULL);

  printf("Packets sent:%d\n", packets_sent);
  printf("Rows processed:%d\n", rows_processed);
  printf("Check rows processed:%d\n", check_rows_proc);
  printf("Records processed by make record:%d\n", make_ssd_records_proc);

  sqlite3_close(db);
	return 0;
}