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
#include "host_server.h"

/*
gdb --args ./host-ndp -D ../../TPC-H.db -Q "SELECT C_CUSTKEY, C_NAME, SUM(L_EXTENDEDPRICE*(1-L_DISCOUNT)) AS REVENUE, C_ACCTBAL, N_NAME, C_ADDRESS, C_PHONE, C_COMMENT FROM TABLE1 GROUP BY C_CUSTKEY, C_NAME, C_ACCTBAL, C_PHONE, N_NAME, C_ADDRESS, C_COMMENT ORDER BY REVENUE DESC LIMIT 20;" -S "SELECT * FROM CUSTOMER, ORDERS, LINEITEM, NATION WHERE C_CUSTKEY = O_CUSTKEY AND L_ORDERKEY = O_ORDERKEY AND O_ORDERDATE>= '1993-10-01' AND O_ORDERDATE < '1994-02-01' AND L_RETURNFLAG = 'R' AND C_NATIONKEY = N_NATIONKEY;"
 */

int parse_options(int argc, char **argv)
{
  int opt;
  static const char short_opts[] = "Q:D:S";

  // while ((opt = getopt(argc, argv, short_opts)) != -1)
  // {
  //   switch(opt)
  //   {
  //     case 'Q':
  //       ndp_opts.outer_query = optarg;
  //       break;
  //     case 'S':
  //       ndp_opts.sub_query = optarg;
  //       break;
  //     case 'D':
  //       ndp_opts.db = optarg;
  //       break;
  //   }
  // }
  ndp_opts.outer_query = argv[4];
  ndp_opts.sub_query = argv[6];
  ndp_opts.db = argv[1];

  return 0;
}

int col_count(char *sql)
{
  /*
   * Return the number of columns in the new schema to be created
   */
	int res = 0;

	for(int i=0; i<strlen(sql); i++)
	{
		if(sql[i] == ',')
			res++;
	}
	return res + 1;
}

int callback(void *n, int argc, char **argv, char **azColName)
{
  /*
   * Prints out final result in sqlite column format
   */
  int i;
  for(i=0; i<argc; i++){
    printf("%s|", argv[i] ? argv[i] : "NULL");
  }
  printf("\n");

  return 0;
}

void *producer_func(void *args)
{
  /*
   * Producer thread:
   * Read data sent over the tcp port and add
   * a batch of records to the queue to be consumed
   */
	p_args *producer_args = (p_args*) args;
	int len, nbuffer=0;
	char tcp_data[RECV_BUF_SIZE];

	for(;;)
	{
		record_batch *ssd_record_batch = (record_batch*) malloc(sizeof(record_batch));
		ssd_record_batch->serial_data = (char*) malloc(payload_size*sizeof(char));

	  while(nbuffer < RECV_BUF_SIZE)
	  {
	  	len = recv (producer_args->socket, tcp_data + nbuffer, RECV_BUF_SIZE-nbuffer, 0);
	  	nbuffer += len;
	  }

	  nbuffer = len = 0;

	  /* create a batch record to be added to buffer pool */
	  void *temp = tcp_data;
	  ssd_record_batch->pkt_type = *((packet_type*)temp);
	  temp = (packet_type*)temp + 1;
	  ssd_record_batch->num_records = *((int*)temp);
	  temp = (int *)temp + 1;
	  ssd_record_batch->serial_data = (char*) memcpy(
	  	ssd_record_batch->serial_data, (char*)temp, payload_size);

	  if (sem_wait(&empty))
		{ 
			/* wait */
	    printf("Error: sem wait fail\n");
		  pthread_exit(NULL);
	  }
    if (sem_wait(&host_mutex))
    { 
      /* wait */
      printf("Error: sem mutex lock fail\n");
      pthread_exit(NULL);
    }

	  pc_state.record_pool[pc_state.tail] = ssd_record_batch;
	  pc_state.tail = (pc_state.tail + 1) % BUF_POOL_SIZE;

    if (sem_post(&host_mutex))
    { 
      /* wait */
      printf("Error: sem mutex lock fail\n");
      pthread_exit(NULL);
    }

	  if (sem_post(&full)) 
	  { 
	  /* post */
      printf("Error: sem wait fail\n");
      pthread_exit(NULL);
    }

    if(ssd_record_batch->pkt_type == END_PKT)
    {
    	break;
    }
	}
}

void *consumer_func(void *args)
{
  /* Consumer thread:
   * Deserialize a batch of records and add it to
   * the in memory table
   */
	c_args *consumer_args = (c_args*) args;

	for(;;)
	{
		void *pC = NULL;

		if (sem_wait(&full))
		{ 
			/* wait */
	    printf("Error: sem wait fail\n");
		  pthread_exit(NULL);
	  }
    if (sem_wait(&host_mutex))
    { 
      /* wait */
      printf("Error: sem mutex lock fail\n");
      pthread_exit(NULL);
    }

	  record_batch *ssd_record_batch = pc_state.record_pool[pc_state.head];
	  pc_state.head = (pc_state.head + 1) % BUF_POOL_SIZE;

    if (sem_post(&host_mutex))
    { 
      /* wait */
      printf("Error: sem mutex lock fail\n");
      pthread_exit(NULL);
    }

	  if (sem_post(&empty)) 
	  { 
	  /* post */
	    printf("Error: sem wait fail\n");
	    pthread_exit(NULL);
	  }

	  if(ssd_record_batch->pkt_type == END_PKT)
	  {
	  	/* no more records to add */
	  	free(ssd_record_batch->serial_data);
  		free(ssd_record_batch);
	  	break;
	  }
	  if(ssd_record_batch->pkt_type == TAB_PKT)
	  {
	  	table_n_cols = col_count(ssd_record_batch->serial_data);

	  	/* create a new table */
	  	int ret;
	  	char *zErrMsg = 0;
	  	ret = sqlite3_exec(consumer_args->db, ssd_record_batch->serial_data, NULL, 0, &zErrMsg);
	  	if (ret)
		  {
		    exit(0);
		  }
	  }
	  else
	  {
	  	batch_deserialize_add(consumer_args->db, &pC, ssd_record_batch, table_n_cols);
	  }

	  free(ssd_record_batch->serial_data);
  	free(ssd_record_batch);
	}
}

int main(int argc, char  **argv)
{
	/* DECL: socket stuff */
	ssize_t len, rem_bytes_ptr;
  struct sockaddr_in storage_server_addr;
  int host_socket;
  int subq_len;
  int nbuffer;
  payload_size = RECV_BUF_SIZE - sizeof(packet_type) - sizeof(int);
  /****************/

	/* DECL: sqlite stuff */
	int ret;
	sqlite3 *mem_db;
	char *zErrMsg = 0;
	char *create_table_select[4096];
	/**********************/

	/* DECL: thread stuff */
	p_args producer_args;
	c_args consumer_args;
	pthread_t producer, consumer;
	pc_state.head = pc_state.tail = 0;
	/**********************/

  /* DECL: timing stuff */
  struct timeval  tv1, tv2;
  /**********************/

	ret = parse_options(argc, argv);
	if (ret)
    goto usage;

  gettimeofday(&tv1, NULL);

  /* The remote address of the server is entered into the
   * header file at compile time.
   */
  memset(&storage_server_addr, 0, sizeof(storage_server_addr));
  storage_server_addr.sin_family = AF_INET;
  inet_pton(AF_INET, argv[7], &(storage_server_addr.sin_addr));
  storage_server_addr.sin_port = htons(SSD_SEND_PORT);

  host_socket = socket(AF_INET, SOCK_STREAM, 0);
  if (host_socket == -1)
  {
    fprintf(stderr, "Error creating host socket--> %s\n", strerror(errno));
    exit(EXIT_FAILURE);
  }

  /* Connect to the storage server */
  if (connect(host_socket, (struct sockaddr *)&storage_server_addr, sizeof(struct sockaddr)) == -1)
  {
    fprintf(stderr, "Error on connect to storage server--> %s\n", strerror(errno));
    exit(EXIT_FAILURE);
  }
  /******************/

  /* Init in memory database */
  ret = sqlite3_open(":memory:", &mem_db);
  if (ret)
  {
    fprintf(stderr, "Can't open mem_db: %s\n", sqlite3_errmsg(mem_db));
    sqlite3_close(mem_db);
    return 1;
  }
  /***************************/

  /* Send Q2 to the storage server */
  len = 0;
  nbuffer = 0;
  subq_len = strlen(ndp_opts.sub_query)+1;
  char *temp_sub_query = malloc(RECV_BUF_SIZE);
  memset(temp_sub_query, 0, RECV_BUF_SIZE);
  memcpy(temp_sub_query, ndp_opts.sub_query, subq_len);

  while(nbuffer < RECV_BUF_SIZE)
  {
    len = send(host_socket, temp_sub_query + nbuffer, RECV_BUF_SIZE - nbuffer, 0);
    nbuffer += len;
    len = 0;
  }
  free(temp_sub_query);
  /*********************************/

  /* Create the producer consumer threads and buffer, init the semaphores */
  producer_args.socket = host_socket;
  consumer_args.db = mem_db;

  if (sem_init(&empty, 0, BUF_POOL_SIZE)) 
  {
    printf("Error: semaphore not initialize\n");
    return -1;
  }

  if (sem_init(&full, 0, 0)) 
  {
    printf("Error: semaphore not initialize\n");
    return -1;
  }

  if (sem_init(&host_mutex, 0, 1)) 
  {
    printf("Error: semaphore not initialize\n");
    return -1;
  }

  ret = pthread_create(&producer, NULL, producer_func, (void*) &producer_args);
  if(ret)
  {
  	fprintf(stderr, "Unable to create producer thread.\n");
  	return 1;
  }

  ret = pthread_create(&consumer, NULL, consumer_func, (void*) &consumer_args);
  if(ret)
  {
  	fprintf(stderr, "Unable to create consumer thread.\n");
  	return 1;
  }


  /***************************************************/

  /* When the producer and consumer thread signal that they are done
   * run Q1 on the temporary in memory table and return the results
   */
  pthread_join(producer, NULL);
  pthread_join(consumer, NULL);

  ret = sqlite3_exec(mem_db, ndp_opts.outer_query, callback, 0, &zErrMsg);
  /*****************************************************************/
  
  gettimeofday(&tv2, NULL);

  printf ("Total time = %f seconds\n",
         (double) (tv2.tv_usec - tv1.tv_usec) / 1000000 +
         (double) (tv2.tv_sec - tv1.tv_sec));

  sqlite3_close(mem_db);
	return 0;

usage:
  printf("\n"
      "Usage:\n"
      "ndp-proc -Q SQL_QUERY\n"
      );
  return 1;
}
