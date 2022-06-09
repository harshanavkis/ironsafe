# Evaluation

## Tested configuration

### Host hardware

- Intel Core i9-10900K CPU
    - 10 cores (3.7 GHz)
    - SGX v1
- Intel XL710 40GbE controller

### Host software

- NixOS (kernel v5.11.21)

### Storage hardware

- [ClearFog CX LX2160A](https://www.solid-run.com/embedded-networking/nxp-lx2160a-family/clearfog-cx-lx2160-carrier/)
- Samsung 970 EVO Plus
1 TB NVMe drive

### Storage software

- Ubuntu 18.04 (patched kernel v5.4.3)
    - [34575e12d752c69ca6eea296e9fcec3c5aa3203a](https://github.com/SolidRun/lx2160a_build/tree/34575e12d752c69ca6eea296e9fcec3c5aa3203a)
- OP-TEE secure OS (v3.4)
- NFS server and client
    - Configure NFS by following the guide shown [here](https://www.tecmint.com/install-nfs-server-on-ubuntu/), for example.
    - Additionally, the NFS server is to be made available through the 40GbE interface.

### Interconnect

- 40GbE

## Structure of the code

## Setup

To download the code:
```
$ git clone git@github.com:harshanavkis/ironsafe.git
```

Checkout all the submodules:
```
$ git submodule update --init
```

The required dependencies are described in [shell.nix](./shell.nix). If you have [nix](https://nixos.org/download.html#nix-install-linux), you could just run the following to make sure the dependencies are available.
```
$ nix-shell
```

Alternatively, you could do the following:
```
$ sudo apt-get install libssl1.0-dev
$ sudo apt install build-essential
$ sudo apt-get install texlive texlive-science texlive-fonts-extra
```

And the following python3 packages:
```
$ python3 -m pip install pandas seaborn
```

Additionally to be able to run the **secure** experiments it is necessary to install [SCONE](https://sconedocs.github.io/installation/) and download the following images from [here](https://sconedocs.github.io/SCONE_Curated_Images/):

- registry.scontain.com:5050/sconecuratedimages/crosscompilers
    - Image ID: 05fc3462302c
- registry.scontain.com:5050/sconecuratedimages/apps:python-3.7.3-alpine3.10
    - Image ID: 2027969dbd8d

To generate the TPC-H data for both the secure and non-secure case:
```
$ ./tpch/create_db.sh [SCALE_FACTORS]
```

To build the merkle tree for the project:
```
$ cd merkle-tree
$ make
```

**SCALE_FACTORS** is either a single scale factor or a list of scale factors separated by space. This generates the following three files in ```tpch/build/``` for every sccale factor in **SCALE_FACTORS**:
- TPCH-[SCALE_FACTOR].db : database that is confidentiality, integrity or freshness protected
- TPCH-[SCALE_FACTOR]-fresh-enc.db : database whose confidentiality, integrity and freshness are protected
- merkle-tree-[SCALE_FACTOR].bin : merkle tree in binary format protecting the encrypted database

### Building the docker images

To build all the docker images for evaluation run the following script:
```
$ ./build_docker_imgs.sh
```

To build individual images only run the following:
```
$ docker build -f benchmark/scone-stuff/sec-ndp -t host-ndp .
$ docker build -f benchmark/scone-stuff/vanilla-ndp -t vanilla-ndp .
$ docker build -f benchmark/scone-stuff/pure-host -t pure-host .
$ docker build -f benchmark/scone-stuff/pure-host-sec -t pure-host-sec .
```

### Network File System

For evaluation, this project uses the Network File System (NFS) to access the database on the remote storage server. Hence, it is necessary to ensure that an NFS server has been set up on the storage server, data (database and merkle trees) is copied over to the server and a local mount point at the host is set up for the remote NFS share.

## Running the experiments

Make sure you have installed the relevant drivers by following the instructions shown [here](https://sconedocs.github.io/installation/). Additionally, follow the instructions [here](https://sconedocs.github.io/sgxinstall/#determine-sgx-device) to see how to use the sgx device. This exports two variables:
- MOUNT_SGXDEVICE
- SGXDEVICE

### Standalone host only experiments

Non-secure version is run as shown below for an example scale factor of 0.01:
```
$ docker run --mount type=bind,source=$DATA_SRC,target=/data pure-host /bin/bash -c "./hello-query /data/merkle-tree-0.01.bin /data/TPCH-0.01.db \"\" \"select count(*) from lineitem;\""
```

Secure version is run as shown below for an example scale factor of 0.01:
```
$ docker run $MOUNT_SGXDEVICE --mount type=bind,source=$DATA_SRC,target=/data pure-host-sec /bin/bash -c "SCONE_VERSION=1 SCONE_HEAP=4G ./hello-query /data/merkle-tree-0.01.bin /data/TPCH-0.01-fresh-enc.db kun \"select count(*) from lineitem;\""
```

The above two runs should output in the following format:
```
{"num_prot_pages": 3068, "query_exec_time": 0.058253, "codec_time": 0.343873, "mt_verify_time": 0.008493, "num_encryption": 0, "num_decryption": 220}
```

One thing to note here is that the **source** should point to the directory containing the TPC-H databases and the merkle tree, so make sure it is set correctly.

### Standalone NDP experiments

Non-secure version is run as shown below:

First start the storage server:
```
./ssd-ndp [NON_SECURE_DB] kun [MERKLE_TREE] out.csv
```

Run the host side application:
```
docker run vanilla-ndp /bin/bash -c "./host-ndp -D db -Q \"select count(*) from TABLE1;\" -S \"select*from lineitem;\" [STORAGE_IP]"
```

Where:
- Q : host-side query
- S : storage-side query
- STORAGE_IP : ip address at which the server-side engine listens to

Results on the storage side are present in the out.csv file in the following format:
```
0, query_exec_time, 0, 0, 0, 0, packets_sent, rows_processed
```

The secure version is run as shown below:

First start the storage server:
```
./ssd-ndp [SECURE_DB] kun [MERKLE_TREE] out.csv
```

Run the host side application:
```
docker run $MOUNT_SGXDEVICE host-ndp /bin/bash -c "SCONE_VERSION=1 SCONE_HEAP=4G ./host-ndp -D db -Q \"select count(*) from TABLE1;\" -S \"select*from lineitem;\" [STORAGE_IP]"
```

## Reproducing results

On the **storage server**, first cd into the top level source directory and create the tpch database:

```
cd $SRC
./tpch/create_db.sh 3
```

Start the nix-shell.

```
nix-shell
```

On the host, mount the storage-side directory containing the data through NFS.

### Storage-side experiments

It is important to run this before the host experiments as the host script is responsible for generating all plots.

Run the following on the storage server.

Set and export the following environment variables
- DB_DIR: $SRC/tpch/build
- SCALE_FACTOR: 3

```
cd $SRC/benchmark
./run_all_storage_experiments.sh
```

### Host-side experiments

Set and export the following environment variables:
- NVME_TCP_DIR: NFS mount point containing the tpch data and merkle trees
- SCALE_FACTOR: 3
- REMOTE_USER: Username on the storage server
- STORAGE_SERVER_IP: IP address of the 1GbE interface on the storage server
- REMOTE_NIC_IP: IP address of the 40GbE interface on the storage server
- REMOTE_SRC: Absolute path of ironsafe source on the storage server
- SCALE_FACTORS: "3 4 5"
- SPLIT_POINTS: "0.1 0.15 0.2"

```
cd $SRC/benchmark
./run_all_host_experiments.sh
```

### Plotting

All plots in the paper should be found in $SRC/paper-plots/.

### Compile the paper

```
$ cd $SRC/paper-src/
$ pdflatex main.tex
$ bibtex main
$ pdflatex main.tex
$ pdflatex main.tex
```

The paper is generated at **$SRC/paper-src/main.pdf**.
