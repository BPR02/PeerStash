#!/bin/bash

# Usage: ./register.sh <share_key> <quota_gb>

SHARE_KEY=$1
QUOTA_GB=$2

SSH_FOLDER="/var/lib/peerstash"

if [ -z $SHARE_KEY ]; then
    echo "Usage: $(basename "$0") SHARE_KEY [QUOTA_GB]" >&2
    exit 1
fi

# extract information from share key
JSON_STRING=$(echo "$SHARE_KEY" | grep -o "[^#]*$" | openssl base64 -d -A)
USERNAME=$(echo "$JSON_STRING" | jq -r ".username")
SERVER_PUBLIC_KEY=$(echo "$JSON_STRING" | jq -r ".server_public_key")
CLIENT_PUBLIC_KEY=$(echo "$JSON_STRING" | jq -r ".client_public_key")

# Set default quota
if [ -z $QUOTA_GB ]; then
    QUOTA_GB=$DEFAULT_QUOTA_GB
fi

# Convert GB to Bytes
QUOTA_BYTES=$(($QUOTA_GB * 1024 * 1024 * 1024))

# add user to SFTPGo
if curl -s --fail --request POST \
    --url http://localhost:8080/api/v2/users \
    --header 'Accept: application/json' \
    --header "X-SFTPGO-API-KEY: $API_KEY" \
    --header 'Content-Type: application/json' \
    --data "{
    \"status\": 1,
    \"username\": \"$USERNAME\",
    \"public_keys\": [\"$CLIENT_PUBLIC_KEY\"],
    \"quota_size\": $QUOTA_BYTES,
    \"permissions\": {\"/\":[\"*\"]}
}" > /dev/null; then
    echo "User $USERNAME created with ${QUOTA_GB}GB limit." >&2

    # add SFTP key to known hosts
    echo "" >> ~/.ssh/known_hosts
    echo "[peerstash-${USERNAME}]:2022 $SERVER_PUBLIC_KEY" >> ~/.ssh/known_hosts
    cp -p ~/.ssh/known_hosts $SSH_FOLDER/known_hosts

    exit 0
fi
# update SFTPGo user if already exists
if curl -s --fail --request PUT \
    --url "http://localhost:8080/api/v2/users/${USERNAME}" \
    --header 'Accept: application/json' \
    --header "X-SFTPGO-API-KEY: $API_KEY" \
    --header 'Content-Type: application/json' \
    --data "{
    \"status\": 1,
    \"username\": \"$USERNAME\",
    \"public_keys\": [\"$CLIENT_PUBLIC_KEY\"],
    \"quota_size\": $QUOTA_BYTES,
    \"permissions\": {\"/\":[\"*\"]}
}" > /dev/null; then
    echo "User $USERNAME updated with ${QUOTA_GB}GB limit." >&2

    # update SFTP key to known hosts
    sed -i "/^\[peerstash-${USERNAME}\]*/c\
        [peerstash-${USERNAME}]:2022 $SERVER_PUBLIC_KEY" ~/.ssh/known_hosts
    cp -p ~/.ssh/known_hosts $SSH_FOLDER/known_hosts

    exit 0
else
    echo "Failed to create user." >&2
    exit 1
fi
