#!/bin/bash

SSH_FOLDER="/var/lib/peerstash"

# set up SSH user keys
if [ ! -f ~/.ssh/id_ed25519 ]; then
    mkdir -p ~/.ssh
    # copy or generate keys
    if [ ! -f $SSH_FOLDER/id_ed25519 ]; then
        echo "Generating SSH user keys..." >&2
        ssh-keygen -t ed25519 -N "" -f ~/.ssh/id_ed25519 -C "$USER"
        cp ~/.ssh/id_* $SSH_FOLDER/
    else
        echo "Pulling SSH user keys from bind mount..." >&2
        cp $SSH_FOLDER/id_* ~/.ssh/
    fi

    # use generated key for all SSH/SFTP connections
    { 
        echo "" 
        echo "Host *" 
        echo "	IdentityFile ~/.ssh/id_ed25519"
    } >> ~/.ssh/config
fi

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
