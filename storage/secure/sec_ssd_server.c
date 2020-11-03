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

#include "sec_sqlite3.h"
#include "sec_ssd_server.h"
#include "common_globals.h"
#include "mt_include/mt_serialize.h"
#include "mt_include/mt_wrapper.h"
#include "perf_counter.h"

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
  // printf("In producer thread\n");
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
  // printf("Producer exits\n");
}

void *consumer_func(void* args)
{
  /*
   * Create a batch of records from the queue
   * and send them over tcp to the host
   */
  c_args_ssd *consumer_args = (c_args_ssd*) args;
  record_batch rec_pkt;
  char batch_pkt[RECV_BUF_SIZE];
  int len, nbuffer;

  static const unsigned long Q_MASK = REC_POOL_SIZE - 1;

	for(;;)
  {
    while(pcs_state.head == pcs_state.tail)
    {
      if(pcs_state.done)
        break;
    }
    if(pcs_state.done && (pcs_state.head == pcs_state.tail))
    {
      break;
    }
    char *dest;
    rec_pkt.pkt_type = REC_PKT;
    int window = RECV_BUF_SIZE - sizeof(packet_type) - sizeof(int);

    while(pcs_state.head == pcs_state.tail){};
    int sbytes = pcs_state.record_pool[pcs_state.head & Q_MASK].size;
    memcpy(rec_pkt.serial_data, pcs_state.record_pool[pcs_state.head & Q_MASK].record, sbytes);
    free(pcs_state.record_pool[pcs_state.head & Q_MASK].record);
    unsigned long temp_old_head = __sync_fetch_and_add(&pcs_state.head, 1);
    rec_pkt.num_records = 1;
    window -= sbytes;

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
        break;
      }

      while(pcs_state.head == pcs_state.tail){};
      int rec_len = pcs_state.record_pool[pcs_state.head & Q_MASK].size;
      int old_window = window;
      if(window >= rec_len)
      {
        memcpy(rec_pkt.serial_data + sbytes, pcs_state.record_pool[pcs_state.head & Q_MASK].record, rec_len);
        free(pcs_state.record_pool[pcs_state.head & Q_MASK].record);
        rec_pkt.num_records += 1;
        sbytes += rec_len;
        window -= rec_len;
        temp_old_head = __sync_fetch_and_add(&pcs_state.head, 1);
      }

      if(rec_len > old_window)
      {
        break;
      }
    }

    serialize_before_send(batch_pkt, &rec_pkt);
    check_rows_proc += rec_pkt.num_records;

    while(nbuffer < RECV_BUF_SIZE)
    {
      // len = send(consumer_args->socket, batch_pkt + nbuffer, RECV_BUF_SIZE - nbuffer, 0);
      len = SSL_write(consumer_args->ssl, batch_pkt + nbuffer, RECV_BUF_SIZE - nbuffer);
      nbuffer += len;
      // printf("Sending packet\n");
    }
    packets_sent += 1;
    // printf("Number of packets sent:%d\n", packets_sent);
  }

  rec_pkt.pkt_type = END_PKT;
  // batch_pkt = serialize_before_send(&rec_pkt);
  serialize_before_send(batch_pkt, &rec_pkt);
  len = nbuffer = 0;
  while(nbuffer < RECV_BUF_SIZE)
  {
    // len = send(consumer_args->socket, batch_pkt + nbuffer, RECV_BUF_SIZE - nbuffer, 0);
    len = SSL_write(consumer_args->ssl, batch_pkt + nbuffer, RECV_BUF_SIZE - nbuffer);
    nbuffer += len;
  }
}

void init_openssl()
{ 
    SSL_load_error_strings(); 
    OpenSSL_add_ssl_algorithms();
}

void cleanup_openssl()
{
    EVP_cleanup();
}

SSL_CTX *create_context()
{
    const SSL_METHOD *method;
    SSL_CTX *ctx;

    method = SSLv23_server_method();

    ctx = SSL_CTX_new(method);
    if (!ctx) {
  perror("Unable to create SSL context");
  ERR_print_errors_fp(stderr);
  exit(EXIT_FAILURE);
    }

    return ctx;
}

void configure_context(SSL_CTX *ctx)
{
    SSL_CTX_set_ecdh_auto(ctx, 1);

    /* Set the key and cert */
    if (SSL_CTX_use_certificate_file(ctx, "server-cert.pem", SSL_FILETYPE_PEM) <= 0) {
        ERR_print_errors_fp(stderr);
  exit(EXIT_FAILURE);
    }

    if (SSL_CTX_use_PrivateKey_file(ctx, "server-key.pem", SSL_FILETYPE_PEM) <= 0 ) {
        ERR_print_errors_fp(stderr);
  exit(EXIT_FAILURE);
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
	sqlite3 *db, *safe_db;
	char *zErrMsg = 0;
	char subquery[4096];
	char *create_table_cmd = "CREATE TEMPORARY TABLE TABLE1 AS";
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

  /* Encryption counters */
  num_codec_enc = 0;
  num_codec_dec = 0;
  total_enc_time = 0;
  total_kdf_time = 0;
  mt_verify_time = 0;
  /***********************/

  /* DECL: SSL stuff */
  SSL_CTX *ctx;
  SSL *ssl;
  /*******************/

  /* Init SSL stuff */
  // printf("Init SSL...\n");
  init_openssl();
  ctx = create_context();
  configure_context(ctx);
  // printf("SSL init complete...\n");
  /*******************/

  /* DECL: Merkle tree stuff */
  mt_obj *tree = (mt_obj*) malloc(sizeof(mt_obj));
  /***************************/

  /* Connect to database */
  ret = sqlite3_open(argv[1], &db);
  if (ret)
  {
    fprintf(stderr, "Can't open database: %s\n", sqlite3_errmsg(db));
    sqlite3_close(db);
    return 1;
  }
  safe_db = db; /* No clue why this works */
  /***********************/

  /* Read in merkle tree from disk */
  deserialize_init_mt(argv[3], tree);
  num_pages_decrypted = 0;
  int num_ele = mt_get_size(tree->mt);
  // printf("Number of pages protected by tree:%d\n", num_ele);
  /*********************************/

  /* Set database passphrase to derive key */
  ret = sqlite3_key(safe_db, argv[2], strlen(argv[2]), tree);
  if(ret != SQLITE_OK)
  {
    fprintf(stderr, "Can't set key for database: %s\n", sqlite3_errmsg(db));
    sqlite3_close(safe_db);
    return 1;
  } 
  /*****************************************/

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

  ssl = SSL_new(ctx);
  SSL_set_fd(ssl, new_socket);

  if (SSL_accept(ssl) <= 0) 
  {
    ERR_print_errors_fp(stderr);
    SSL_shutdown(ssl);
    SSL_free(ssl);
    return -1;
  }
  /******************/

  struct timeval tv1, tv2;
  gettimeofday(&tv1, NULL);
  /* Get subquery and generate the command for create table */
  len = nbuffer = 0;
  while(nbuffer < RECV_BUF_SIZE)
  {
  	// len = recv (new_socket, subquery + nbuffer, RECV_BUF_SIZE-nbuffer, 0);
    len = SSL_read(ssl, subquery + nbuffer, RECV_BUF_SIZE-nbuffer);
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
  ret = sqlite3_exec(safe_db, create_table_select, NULL, 0, &zErrMsg);
  if (ret)
  {
    fprintf(stderr, "RC:%d, Can't create table TABLE1: %s\n", ret, sqlite3_errmsg(safe_db));
    sqlite3_close(safe_db);
    return 1;
  }

  ret = sqlite3_exec(safe_db, "SELECT sql FROM sqlite_temp_master where tbl_name=\'TABLE1\';", schema_callback, 0, &zErrMsg);
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
  	// len = send(new_socket, schema_send_ser + nbuffer, RECV_BUF_SIZE - nbuffer, 0);
    len = SSL_write(ssl, schema_send_ser + nbuffer, RECV_BUF_SIZE - nbuffer);
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
  consumer_args.ssl = ssl;
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

  pthread_join(consumer, NULL);
  gettimeofday(&tv2, NULL);

  // printf ("Total query execution time = %f seconds\n",
  //        (double) (tv2.tv_usec - tv1.tv_usec) / 1000000 +
  //        (double) (tv2.tv_sec - tv1.tv_sec));

  // printf("Packets sent:%d\n", packets_sent);
  // printf("Rows processed:%d\n", rows_processed);
  // printf("Check rows processed:%d\n", check_rows_proc);
  // printf("Records processed by make record:%d\n", make_ssd_records_proc);
  // printf("Number of pages decrypted: %u\n", num_pages_decrypted);
  
  // printf("Total time spent in codec: %f seconds\n", total_enc_time);
  // printf("Total time for key derivation: %f seconds\n", total_kdf_time);
  // printf("Total time spent in merkle tree verification during decryption: %f seconds\n", mt_verify_time);
  // printf("Total number of encryptions: %u\n", num_codec_enc);
  // printf("Total number of decryptions: %u\n", num_codec_dec);
  double query_exec_time = ((double) (tv2.tv_usec - tv1.tv_usec) / 1000000 + (double) (tv2.tv_sec - tv1.tv_sec));

  num_ele = mt_get_size(tree->mt);
  // printf("Number of pages protected by tree:%d\n", num_ele);  

  ret = sqlite3_exec(safe_db, "DROP TABLE TABLE1;", NULL, 0, &zErrMsg);
  if (ret)
  {
    fprintf(stderr, "RC:%d, Can't drop table TABLE1: %s\n", ret, sqlite3_errmsg(safe_db));
    sqlite3_close(safe_db);
    return 1;
  }

  // printf("{num_prot_pages: %d, query_exec_time: %f, codec_time: %f, mt_verify_time: %f, num_encryption: %u, num_decryption: %u, packets_sent: %d, rows_processed: %u}\n", 
  //   num_ele, query_exec_time, total_enc_time, mt_verify_time, num_codec_enc, num_codec_dec, packets_sent, rows_processed);
  fprintf(csv_out_file, "%d,%f,%f,%f,%u,%u,%d,%u\n", 
    num_ele, query_exec_time, total_enc_time, mt_verify_time, num_codec_enc, num_codec_dec, packets_sent, rows_processed);

  sqlite3_close(safe_db);
	return 0;
}
