FROM bff40ad76f79

COPY test/end2end/hello-app/ sec-sql

COPY openssl-src/openssl-openssl-3.0.0-alpha3/ /openssl-src

RUN apt update
RUN apt install -y make
RUN apt install -y perl


WORKDIR /sec-sql

RUN scone-gcc -o /sec-sql hello.c sqlite3.c -lpthread -ldl -lssl -lcrypto -I/openssl-src/include -L/openssl-src/

WORKDIR /