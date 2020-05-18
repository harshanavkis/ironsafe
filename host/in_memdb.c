#include <stdio.h>
#include <stdlib.h>
#include "sqlite3.h"
#include "globals.h"

char create_table[] = "CREATE TABLE TABLE1("
  "C_CUSTKEY INT,"
  "C_NAME TEXT,"
  "C_ADDRESS TEXT,"
  "C_NATIONKEY INT,"
  "C_PHONE TEXT,"
  "C_ACCTBAL INT,"
  "C_MKTSEGMENT TEXT,"
  "C_COMMENT TEXT,"
  "O_ORDERKEY INT,"
  "O_CUSTKEY INT,"
  "O_ORDERSTATUS TEXT,"
  "O_TOTALPRICE INT,"
  "O_ORDERDATE NUM,"
  "O_ORDERPRIORITY TEXT,"
  "O_CLERK TEXT,"
  "O_SHIPPRIORITY INT,"
  "O_COMMENT TEXT,"
  "L_ORDERKEY INT,"
  "L_PARTKEY INT,"
  "L_SUPPKEY INT,"
  "L_LINENUMBER INT,"
  "L_QUANTITY INT,"
  "L_EXTENDEDPRICE INT,"
  "L_DISCOUNT INT,"
  "L_TAX INT,"
  "L_RETURNFLAG TEXT,"
  "L_LINESTATUS TEXT,"
  "L_SHIPDATE NUM,"
  "L_COMMITDATE NUM,"
  "L_RECEIPTDATE NUM,"
  "L_SHIPINSTRUCT TEXT,"
  "L_SHIPMODE TEXT,"
  "L_COMMENT TEXT,"
  "N_NATIONKEY INT,"
  "N_NAME TEXT,"
  "N_REGIONKEY INT,"
  "N_COMMENT TEXT"
");";

static int callback(void *NotUsed, int argc, char **argv, char **azColName)
{
  int i;
  for(i=0; i<argc; i++){
    printf("%s = %s\n", azColName[i], argv[i] ? argv[i] : "NULL");
  }
  printf("\n");
  return 0;
}

int main(int argc, char **argv)
{
	int ret;
	sqlite3 *db;
	char *zErrMsg = 0;

	ret = sqlite3_open(":memory:", &db);
	ret = sqlite3_exec(db, create_table, NULL, 0, &zErrMsg);

	printf("%d\n", rootpage);

	ret = sqlite3_exec(db, "select rootpage from sqlite_master where tbl_name=\'TABLE1\'", callback, 0, &zErrMsg);
}