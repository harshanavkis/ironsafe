# NDP

This is a crude documentation, steps to get started:
- change SSD_ADDRESS to the ip address of storage server
- run make in both host and storage folders

```
cd host

./host-ndp -D ../../TPC-H.db -Q "SELECT C_CUSTKEY, C_NAME, SUM(L_EXTENDEDPRICE*(1-L_DISCOUNT)) AS REVENUE, C_ACCTBAL, N_NAME, C_AD
 -S "SELECT * FROM CUSTOMER, ORDERS, LINEITEM, NATION WHERE C_CUSTKEY = O_CUSTKEY AND L_ORDERKEY = O_ORDERKEY AND O_ORDERDATE>= '1993-10-01'
```

```
cd storage

./ssd_ndp TPC-H.db
```

## Sample Database

A sample TPC-H database, scale factor of 1 can be downloaded from [here](https://drive.google.com/file/d/1AkKBnl2OuyouC7PrWDp6-CzjPg57x2ng/view?usp=sharing).

## TODO

- [ ] NVMe extension
- [ ] Code binary offload, currently only query is offloaded
- [ ] Fix producer consumer circular array buffer overflow(will occur when we move to a larger database size
- [ ] Fine grained tests, currently only end-to-end i.e result based tests have been performed.

## Possible bugs

- [ ] If number of packets/rows is high some loss is observed
