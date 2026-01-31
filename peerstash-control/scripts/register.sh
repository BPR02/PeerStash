#!/bin/bash

# check if user is already in DB

# add SFTP key to known hosts
echo "" >> ~/.ssh/known_hosts
echo "[$HOSTNAME]:$PORT $SERVER_PUBLIC_KEY" >> ~/.ssh/known_hosts

# get JWT for SFTPGo
curl --request GET \
  --url http://localhost:8080/api/v2/token \
  --header 'Accept: application/json' \
  --header 'Authorization: Basic <username:password encoded in base64>' \
  --header 'X-SFTPGO-OTP: '

# add user to SFTPGo
curl --request POST \
  --url http://localhost:8080/api/v2/users \
  --header 'Accept: application/json' \
  --header 'Authorization: Bearer <JWT>' \
  --header 'Content-Type: application/json' \
  --data "{
  'status': 1,
  'username': $USERNAME,
  'public_keys': [$CLIENT_PUBLIC_KEY],
  'quota_size': $QUOTA_BYTES,
  'permissions': {'/':['*']}
}"

# add user to DB
