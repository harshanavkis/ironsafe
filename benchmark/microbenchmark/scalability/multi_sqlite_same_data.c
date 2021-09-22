#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <pthread.h>
#include <sys/time.h>

#include "sec_sqlite3.h"
#include "mt_serialize.h"
#include "mt_wrapper.h"

// Needed by all threads to wait for other threads before continuing.
pthread_barrier_t barrier;

// id of the worker sqlite thread
typedef struct
{
    int id;
} worker_param;

// structure to store results of each thread
typedef struct
{
    int id;
    double time;
} worker_result;

// Global vars read only from the worker threads
char query[1000];
char db_dir[50];
char kind[15];
float scale;
char db_pwd[10];
worker_result *res;

/*
 * id: id of the copy of the database
 * db_path: dest array where abs path of the DB is written to 
*/
void gen_db_path(int id, char *db_path)
{
    char db_name[50];
    strcpy(db_path, db_dir);
    if (db_path[strlen(db_path) - 1] != '/')
    {
        strcat(db_path, "/");
    }

    if (strcmp(kind, "secure") == 0)
    {
        sprintf(db_name, "TPCH-%g-fresh-enc.db", scale);
    }
    else
    {
        sprintf(db_name, "TPCH-%g.db", scale);
    }

    strcat(db_path, db_name);
}

/*
 * id: id of the copy of the merkle tree
 * mt_path: dest array where abs path of the mt is written to 
*/
void gen_mt_path(int id, char *mt_path)
{
    char mt_name[50];
    strcpy(mt_path, db_dir);
    if (mt_path[strlen(mt_path) - 1] != '/')
    {
        strcat(mt_path, "/");
    }

    sprintf(mt_name, "merkle-tree-%g.bin", scale);
    strcat(mt_path, mt_name);
}

void *
sqlite_worker(void *params)
{
    worker_param *wp = (worker_param *)params;
    char db_path[80], mt_path[80];
    gen_db_path(wp->id, db_path);

    fprintf(stderr, "id: %d, db_path:%s\n", wp->id, db_path);

    sqlite3 *db;
    char *zErrMsg = 0;
    int rc;
    rc = sqlite3_open(db_path, &db);
    if (rc)
    {
        fprintf(stderr, "Can't open database: %s\n", sqlite3_errmsg(db));
        sqlite3_close(db);
        return NULL;
    }

    if (strcmp(kind, "secure") == 0)
    {
        gen_mt_path(wp->id, mt_path);
        fprintf(stderr, "id: %d, mt_path:%s\n", wp->id, mt_path);

        mt_obj *tree = (mt_obj *)malloc(sizeof(mt_obj));
        deserialize_init_mt(mt_path, tree);

        rc = sqlite3_key(db, db_pwd, strlen(db_pwd), tree);
        if (rc != SQLITE_OK)
        {
            fprintf(stderr, "Can't set key for database: %s\n", sqlite3_errmsg(db));
            sqlite3_close(db);
            return NULL;
        }
    }

    struct timeval tv1, tv2;
    pthread_barrier_wait(&barrier);

    gettimeofday(&tv1, NULL);
    rc = sqlite3_exec(db, query, NULL, 0, &zErrMsg);
    if (rc)
    {
        fprintf(stderr, "rc:%d, Unable to execute query, id:%d\n", rc, wp->id);
        return NULL;
    }
    gettimeofday(&tv2, NULL);

    double total_time = ((double)(tv2.tv_usec - tv1.tv_usec) / 1000000 + (double)(tv2.tv_sec - tv1.tv_sec));

    res[wp->id] = (worker_result){wp->id, total_time};

    printf("%d,%f\n", wp->id, total_time);
}

int main(int argc, char **argv)
{
    strcpy(kind, argv[1]);       // secure or non-secure
    scale = atof(argv[2]);       // scale factor of the database
    strcpy(db_dir, argv[3]);     // root dir containing DBs
    strcpy(query, argv[4]);      // query to be executed on all threads
    int threads = atoi(argv[5]); // number of sqlite workers

    // fprintf(stderr, "query: %s\n", query);

    if (strcmp(kind, "secure") == 0)
    {
        // only value if kind==secure
        strcpy(db_pwd, argv[6]);
    }

    // Barrier waits for all threads
    pthread_barrier_init(&barrier, NULL, threads);

    int id = 1;
    pthread_t *pthreads = (pthread_t *)malloc(threads * sizeof(pthread_t));
    worker_param *wp = (worker_param *)malloc(threads * sizeof(worker_param));
    res = (worker_result *)malloc(threads * sizeof(worker_result));

    for (int i = 0; i < threads; i++)
    {
        wp[i].id = id;

        pthread_create(&pthreads[i], NULL, sqlite_worker, &wp[i]);
        id += 1;
    }

    for (int i = 0; i < threads; i++)
    {
        pthread_join(pthreads[i], NULL);
    }

    free(pthreads);
}