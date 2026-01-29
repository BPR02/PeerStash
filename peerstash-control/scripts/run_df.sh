#!/bin/bash

if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ]
then
   echo "run_df.sh SFTP_USER SFTP_HOST SFTP_PORT" >&2;
   exit 1
fi

SFTP_USER=$1
SFTP_HOST=$2
SFTP_PORT=$3

# Run df -h on the SFTP server
sftp -P $SFTP_PORT $SFTP_USER@$SFTP_HOST <<EOF
df
quit
EOF
