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
USERNAME=$(echo "$JSON_STRING" | jq -r ".username")
SERVER_PUBLIC_KEY=$(echo "$JSON_STRING" | jq -r ".server_public_key")
CLIENT_PUBLIC_KEY=$(echo "$JSON_STRING" | jq -r ".client_public_key")

# Set default quota
if [ -z $QUOTA_GB ]; then
    QUOTA_GB=$DEFAULT_QUOTA_GB
fi

# Convert GB to Bytes
QUOTA_BYTES=$(($QUOTA_GB * 1024 * 1024 * 1024))

# check if user is in DB
EXISTS=$(sqlite3 "$DB_PATH" "SELECT EXISTS(SELECT 1 FROM hosts WHERE hostname='peerstash-${USERNAME}');")

# ask if user should be updated
if [ $EXISTS -ne 0 ]; then
    echo "User ${USERNAME} already exists. Update user? [Y/n]" >&2
    read -r OVERWRITE

    if [ "$OVERWRITE" != "y" ] && [ "$OVERWRITE" != "Y" ]; then
        echo "Aborting." >&2
        exit 1
    fi

    # update SFTPGo user
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

# (commented out because ports and hostnames are hardcoded, so they never need to be updated, left for reference)
#         # update database 
#         sqlite3 "$DB_PATH" <<EOF
# .parameter set @hostname "peerstash-$USERNAME"
# UPDATE hosts SET port='2022' WHERE hostname = @hostname;
# EOF

        exit 0
    fi

    echo "Failed to update user." >&2
    exit 1
fi

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

    # add to database
    USERNAME_CLEAN="${USERNAME//\'/\'\'}"
    sqlite3 "$DB_PATH" "INSERT INTO hosts (hostname, port) VALUES ('peerstash-${USERNAME_CLEAN}','2022');"

    exit 0
fi

echo "Failed to create user." >&2
exit 1
