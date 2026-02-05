#!/bin/bash

SSH_FOLDER="/var/lib/peerstash"

# get ssh keys
SERVER_PUBLIC_KEY=$(cat /var/lib/sftpgo/id_ed25519.pub)
CLIENT_PUBLIC_KEY=$(cat ~/.ssh/id_ed25519.pub)

# validate variables
if [ -z "$USER" ]; then
    echo "Error: Username not found" >&2
    exit 1
fi

if [ -z "$SERVER_PUBLIC_KEY" ]; then
     echo "Error: Host keys not found." >&2
    exit 1
fi

if [ -z "$CLIENT_PUBLIC_KEY" ]; then
    echo "Error: User keys not found." >&2
    exit 1
fi

# generate encoded string
JSON_STRING=$( jq -n \
                  --arg u "$USER" \
                  --arg s "$SERVER_PUBLIC_KEY" \
                  --arg c "$CLIENT_PUBLIC_KEY" \
                  '{username: $u, server_public_key: $s, client_public_key: $c}' )

ENCODED=$(echo $JSON_STRING | openssl enc -base64 -A)
echo "peerstash#$ENCODED"
