#!/bin/bash

if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ]
then
   echo "get_quota.sh SFTP_USER SFTP_HOST SFTP_PORT" >&2;
   exit 1
fi

/srv/peerstash/scripts/run_df.sh $1 $2 $3 | grep -o "[0-9]*" | grep -m 2 ".*"
