#!/bin/sh

ORIGINAL_ADDUSER="/usr/sbin/adduser"
DB_PATH="/peerstash/config/users.db"

# get username
if expr "X$1" : 'X.*[-]\{1,\}' >/dev/null || [ "$#" -ne 1 ]; then
    echo "Modified version of adduser for peerstash"
    echo "usage: adduser USERNAME (consisting of [0-9a-z_])" >&2
    exit 1
fi
USERNAME=$1

# verify username
if expr "X$USERNAME" : 'X.*[^a-z0-90-9_]\{1,\}' >/dev/null; then
    echo "username must consist of [0-9a-z_]"
    exit 1
fi
if [ ${#USERNAME} -le 2 ] || [ ${#USERNAME} -ge 32 ]; then
    echo "username must be between 3 and 31 characters"
    exit 1
fi

# create user
$ORIGINAL_ADDUSER -D -h /peerstash/backups/"$USERNAME" "$USERNAME"

# generate random password
PASSWORD=$(head -c 16 /dev/urandom | base64 | tr -dc 'a-zA-Z0-9')

# save hashed password into database
PASSWORD_HASH=$(openssl passwd -6 "$PASSWORD")
sqlite3 "$DB_PATH" "INSERT INTO users (username, password_hash) VALUES ('$USERNAME','$PASSWORD_HASH');"

# update password
echo "$USERNAME:$PASSWORD_HASH" | chpasswd -e > /dev/null 2>&1

# print username and password
echo "$USERNAME:$PASSWORD"
