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
#include <sys/time.h>

#include "sqlite3.h"
#include "ssd_server.h"
#include "common_globals.h"

//25819: Mem struct

void make_query_string(char *dest, char *start, char *middle, char *end)
{
  /*
   * Generates the sql statement to create a table in
   * the in-memory database on the host
   */
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
float pack_per = 0.0;

int dummy_callback(void *n, int argc, char **argv, char **azColName)
{
  rows_processed++;
  return 0;
}

void serialize_before_send(char *dest, record_batch *ssd_record)
{
  /*
   * Serialize record_batch structure
   * before sending over tcp
   */
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
  /*
   * Execute subquery containing the filter ops
   * and add them to the consumer queue
   */
  struct timespec currTime;
  clockid_t threadClockId;

  pthread_getcpuclockid(pthread_self(), &threadClockId);

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

  clock_gettime(threadClockId, &currTime);

  // printf("Producer took: %lds\n", currTime.tv_sec);

  // printf("Producer exits\n");

  pthread_exit(NULL);
}

void *consumer_func(void* args)
{
  /*
   * Create a batch of records from the queue
   * and send them over tcp to the host
   */
  struct timespec currTime;
  clockid_t threadClockId;

  // pthread_getcpuclockid(pthread_self(), &threadClockId);

  c_args_ssd *consumer_args = (c_args_ssd*) args;
  record_batch rec_pkt;
  char batch_pkt[RECV_BUF_SIZE];
  int len, nbuffer;

	for(;;)
  {
    while(pcs_state.head == pcs_state.tail)
    {
      if(pcs_state.done)
        break;
    }
    if(pcs_state.done && (pcs_state.head == pcs_state.tail))
    {
      // printf("Breaking out of consumer for\n");
      break;
    }
    char *dest;
    rec_pkt.pkt_type = REC_PKT;
    int window = RECV_BUF_SIZE - sizeof(packet_type) - sizeof(int);
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
    free(pcs_state.record_pool[pcs_state.head].record);
    pcs_state.head += 1;
    pcs_state.head %= REC_POOL_SIZE;
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

    len = 0;
    nbuffer = 0;

    while(1)
    {
      while(pcs_state.head == pcs_state.tail)
      {
        if(pcs_state.done)
          break;
      }
      if(pcs_state.done && (pcs_state.head == pcs_state.tail))
      {
        // printf("Breaking out of inner while loop\n");
        break;
      }

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

      int rec_len = pcs_state.record_pool[pcs_state.head].size;
      int old_window = window;
      if(window >= rec_len)
      {
        memcpy(rec_pkt.serial_data + sbytes, pcs_state.record_pool[pcs_state.head].record, rec_len);
        free(pcs_state.record_pool[pcs_state.head].record);
        /* FIXME: Circular array, will lead to buffer overflow for
         * large number of records
         */
        pcs_state.head += 1;
        pcs_state.head %= REC_POOL_SIZE;
        rec_pkt.num_records += 1;
        sbytes += rec_len;
        window -= rec_len;
      }

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

      if(rec_len > old_window)
      {
        if (sem_post(&ssd_full))
        { 
          /* wait */
          printf("Error: sem post to ssd_full fail\n");
          pthread_exit(NULL);
        }
        break;
      }
    }

    serialize_before_send(batch_pkt, &rec_pkt);
    check_rows_proc += rec_pkt.num_records;

    while(nbuffer < RECV_BUF_SIZE)
    {
      len = send(consumer_args->socket, batch_pkt + nbuffer, RECV_BUF_SIZE - nbuffer, 0);
      nbuffer += len;
    }
    packets_sent += 1;
    float occupancy = ((float)sbytes/(512*1024));
    pack_per += occupancy;
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

  // clock_gettime(threadClockId, &currTime);

  // printf("Consumer took: %lds\n", currTime.tv_sec);

  pthread_exit(NULL);
}

int main(int argc, char const *argv[])
{
  while(1)
  {
    // printf("Waiting for connection from host...\n");
    make_ssd_records_proc = 0;
    make_record = 0;
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
  	sqlite3 *db, *safe_db;
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

    /* File stuff */
    FILE *csv_out_file;
    csv_out_file = fopen(argv[4], "a");
    /**************/

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

    // printf("Received connection from host...\n");

    /* Connect to database */
    ret = sqlite3_open(argv[1], &db);
    if (ret)
    {
      fprintf(stderr, "Can't open database: %s\n", sqlite3_errmsg(db));
      sqlite3_close(db);
      return 1;
    }
    safe_db = db;
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

    struct timeval  tv1, tv2;

    gettimeofday(&tv1, NULL);

    create_table_select = (char*) malloc(out_str_len);
    make_query_string(create_table_select, create_table_cmd, subquery, limit_cmd);
    /**********************************************************/

    /* Create temp table and generate its sql query, send sql query to host */
    ret = sqlite3_exec(safe_db, create_table_select, NULL, 0, &zErrMsg);
    if (ret)
    {
      fprintf(stderr, "RC:%d, Can't create table TABLE1: %s\n", ret, sqlite3_errmsg(safe_db));
      sqlite3_close(safe_db);
      return 1;
    }

    ret = sqlite3_exec(safe_db, "SELECT sql FROM sqlite_master where tbl_name=\'TABLE1\';", schema_callback, 0, &zErrMsg);
    if (ret)
    {
      fprintf(stderr, "Can't extract sql of table TABLE1: %s\n", sqlite3_errmsg(db));
      sqlite3_close(safe_db);
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
    producer_args.db = safe_db;
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

    pthread_join(producer, NULL);
    pthread_join(consumer, NULL);

    gettimeofday(&tv2, NULL);

    // printf ("Total time spent to execute offloaded query  = %f seconds\n",
    //        (double) (tv2.tv_usec - tv1.tv_usec) / 1000000 +
    //        (double) (tv2.tv_sec - tv1.tv_sec));

    // printf("Packets sent:%d\n", packets_sent);
    // printf("Rows processed:%d\n", rows_processed);
    // printf("Check rows processed:%d\n", check_rows_proc);
    // printf("Records processed by make record:%d\n", make_ssd_records_proc);
    // printf("Packet occupancy: %f\n", (pack_per/packets_sent));

    double query_exec_time = ((double) (tv2.tv_usec - tv1.tv_usec) / 1000000 + (double) (tv2.tv_sec - tv1.tv_sec));

    ret = sqlite3_exec(safe_db, "DROP TABLE TABLE1;", NULL, 0, &zErrMsg);
    if (ret)
    {
      fprintf(stderr, "RC:%d, Can't create table TABLE1: %s\n", ret, sqlite3_errmsg(safe_db));
      sqlite3_close(safe_db);
      return 1;
    }

    // fprintf("{num_prot_pages: 0, query_exec_time: %f, codec_time: 0, mt_verify_time: 0, num_encryption: 0, num_decryption: 0, packets_sent: %d, rows_processed: %u}\n", 
    //  query_exec_time, packets_sent, rows_processed);

    fprintf(csv_out_file, "0,%f,0,0,0,0,%d,%u\n", query_exec_time, packets_sent, rows_processed);
    fclose(csv_out_file);

    sqlite3_close(safe_db);

    // printf("Done host processing...\n");

    packets_sent = 0;
    rows_processed = 0;
    check_rows_proc = 0;
    pack_per = 0.0;

    close(new_socket);
    close(server_fd);
  }
	return 0;
}
