#!/bin/bash

MAX_RETRIES=3
RETRY_DELAY=1  # in seconds

# input validation
if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ]; then
   echo "Usage: $(basename "$0") SFTP_USER SFTP_HOST SFTP_PORT" >&2
   exit 1
fi

SFTP_USER=$1
SFTP_HOST=$2
SFTP_PORT=$3

# attempt to connect multiple times
ATTEMPT=1
SUCCESS=false
while [ $ATTEMPT -le $MAX_RETRIES ]; do
    # run df on sftp server
    SFTP_OUTPUT=$(sftp -P "$SFTP_PORT" "$SFTP_USER@$SFTP_HOST" <<EOF
df
bye
EOF
    )

    # Check if successful (Exit code 0 AND output is not empty)
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 0 ] && [ -n "$SFTP_OUTPUT" ]; then
        SUCCESS=true
        break
    else
        # retry if failed
        if [ $ATTEMPT -lt $MAX_RETRIES ]; then
            echo "Attempt $ATTEMPT/$MAX_RETRIES failed. Retrying in ${RETRY_DELAY}s..." >&2
            sleep $RETRY_DELAY
        fi
        ATTEMPT=$((ATTEMPT + 1))
    fi
done

# check success
if [ "$SUCCESS" = false ]; then
    echo "Error: Failed to retrieve quota after $MAX_RETRIES attempts." >&2
    exit 2
fi

# parse output
NUMBERS=$(echo "$SFTP_OUTPUT" | grep -o "[0-9]*" | head -n 2)

read -r AVAIL <<< $(echo "$NUMBERS" | sed -n '1p')
read -r USED <<< $(echo "$NUMBERS" | sed -n '2p')

# validate result
if [ -z "$USED" ] || [ -z "$AVAIL" ]; then
    echo "Error: Connection successful, but could not parse quota numbers." >&2
    exit 3
fi

# print quota
echo "$USED / $AVAIL"
