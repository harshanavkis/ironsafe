#!/bin/bash

ssh $REMOTE_USER@$STORAGE_SERVER_IP "kill -9 \$(pgrep run_server) || true" > /dev/null 2>&1
ssh $REMOTE_USER@$STORAGE_SERVER_IP "kill -9 \$(pgrep ssd-ndp)" > /dev/null 2>&1