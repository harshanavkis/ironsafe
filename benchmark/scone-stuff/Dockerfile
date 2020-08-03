FROM bff40ad76f79

COPY . /sqlite-ndp
COPY openssl-src/ /openssl-src

RUN apt update
RUN apt install -y make
RUN apt install -y perl
RUN apt install -y vim
RUN apt install -y python3
RUN apt install -y python3-pip
RUN pip3 install --upgrade pip
RUN pip install pandas

WORKDIR /openssl-src
RUN ./config
RUN make clean
RUN make || true

WORKDIR /sqlite-ndp/merkle-tree/src
RUN make

WORKDIR /sqlite-ndp/host/secure
RUN make clean || true
RUN OPENSSL_SRC=/openssl-src make

WORKDIR /sqlite-ndp/benchmark/macrobenchmark

# docker build -f benchmark/scone-stuff/Dockerfile -t host-ndp .

# docker run $MOUNT_SGXDEVICE host-ndp /bin/bash -c "SCONE_VERSION=1 SCONE_HEAP=2G ./host-ndp -D .. -Q \"select * from TABLE1;\" -S \"select count(*) from lineitem;\" 172.17.0.1"
