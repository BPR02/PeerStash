#!/bin/bash

# Usage: ./register.sh <share_key> <quota_gb>

SHARE_KEY=$1
QUOTA_GB=$2

if [ -z $SHARE_KEY ]; then
    echo "Usage: $(basename "$0") SHARE_KEY [QUOTA_GB]" >&2
    exit 1
fi

# extract information from share key
JSON_STRING=$(echo "$SHARE_KEY" | grep -o "[^#]*$" | openssl base64 -d -A)
USERNAME=$(echo "$JSON_STRING" | jq ".username")
SERVER_PUBLIC_KEY=$(echo "$JSON_STRING" | jq ".server_public_key")
CLIENT_PUBLIC_KEY=$(echo "$JSON_STRING" | jq ".client_public_key")

# Set default quota
if [ -z $QUOTA_GB ]; then
    QUTOA_GB=$DEFAULT_QUOTA_GB
fi

# check if user is already in DB

# Convert GB to Bytes
QUOTA_BYTES=$(($QUOTA_GB * 1024 * 1024 * 1024))

# add SFTP key to known hosts
echo "" >> ~/.ssh/known_hosts
echo "[peerstash-$USERNAME]:2022 $SERVER_PUBLIC_KEY" >> ~/.ssh/known_hosts

# add user to SFTPGo
curl -sS --request POST \
    --url http://localhost:8080/api/v2/users \
    --header 'Accept: application/json' \
    --header "X-SFTPGO-API-KEY: $API_KEY" \
    --header 'Content-Type: application/json' \
    --data '{
    "status": 1,
    "username": "'"$USERNAME"'",
    "public_keys": ["'"$CLIENT_PUBLIC_KEY"'"],
    "quota_size": "'"$QUOTA_BYTES"'",
    "permissions": {"/":["*"]}
}'

echo "User $USERNAME created with ${QUOTA_GB}GB limit."

# add user to DB
