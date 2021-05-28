import os

def main():
    log_file = os.environ["LOG_FILE"]
    f = open(log_file)
    print(f.read())

if __name__ == "__main__":
    main()