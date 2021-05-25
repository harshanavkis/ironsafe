import sys
import os
import datetime

def log_query_execution(host_query, storage_query, user_key):
    f = open(os.environ["LOG_FILE"], "a")

    log_data = "{},{},{},{}".format(
        datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S"),
        user_key,
        host_query,
        storage_query
    )

    f.write(log_data)
    f.write("\n")
    f.flush()
    os.fsync(f.fileno())

    f.close()

def main():
    host_query    = sys.argv[1]
    storage_query = sys.argv[2]
    user_key      = sys.argv[3]

    log_query_execution(host_query, storage_query, user_key)

if __name__ == "__main__":
    main()
