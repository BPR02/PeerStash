#!/bin/sh

DB_PATH="/peerstash/config/users.db"
WEB_API_PORT=20461
WEB_APP_PUBKEY_PATH="/peerstash/config/web_app_public.pem"
SSH_FOLDER="/peerstash/config/ssh"
API_KEYS_FOLDER="/peerstash/config/api_keys"
TAILNET_PUBLIC_API_PORT=40461
TAILNET_AUTH_API_PORT=41461

# Function to create users from the database
create_users_from_db() {
    echo "Creating users from database..."
    sqlite3 "$DB_PATH" "SELECT username, password_hash FROM users;" | while IFS='|' read -r username password_hash; do
        if id "$username" >/dev/null 2>&1; then
            echo "User $username already exists, skipping..."
        else
            echo "Creating user $username..."
            adduser -D -h /peerstash/backups/"$username" "$username"
            echo "$username:$password_hash" | chpasswd -e
        fi
    done
}

# Check if the database exists
if [ -f "$DB_PATH" ]; then
    echo "SQLite database found. Restoring users..."
    create_users_from_db
else
    echo "No database found. Creating a new empty database..."
    sqlite3 "$DB_PATH" "CREATE TABLE users (username TEXT PRIMARY KEY, password_hash TEXT NOT NULL);"
fi

# Replace passwd binary with custom wrapper
echo "Updating passwd binary..."
apk add build-base
gcc -o /usr/local/bin/passwd /peerstash/scripts/passwd.c
chown root /usr/local/bin/passwd
chmod 4755 /usr/local/bin/passwd
apk del build-base

# Replace adduser with custom version
echo "Updating adduser binary..."
cp /peerstash/scripts/adduser.sh /usr/local/bin/adduser
chown root /usr/local/bin/adduser
chmod -R 744 /usr/local/bin/adduser

# Start the API endpoint before enabling SSH
echo "Starting web app API on port $WEB_API_PORT"
socat TCP-LISTEN:$WEB_API_PORT,fork EXEC:"/peerstash/scripts/api_handler.sh" &

# Wait for the web app to send its public key before continuing
echo "Waiting for the web app public key..."
COUNT=0
ATTEMPTS=10
until [ -s "$WEB_APP_PUBKEY_PATH" ] || [ $COUNT -eq $ATTEMPTS ]; do
    COUNT=$((COUNT+1))
    echo "$COUNT..."
    sleep 1
done
if [ $COUNT -eq $ATTEMPTS ]; then
    echo "Web app public key not received, closing web app API (port $WEB_API_PORT)"
    killall socat
    sleep 2
else
    echo "Web app public key received!"
fi

# Generate tailnet API keys
if [ ! -f $API_KEYS_FOLDER/tailnet_private.pem ]; then
    echo "Generating tailnet API keys..."
    mkdir -p $API_KEYS_FOLDER
    openssl genpkey -algorithm RSA -out $API_KEYS_FOLDER/tailnet_private.pem -pkeyopt rsa_keygen_bits:4096
    openssl rsa -pubout -in $API_KEYS_FOLDER/tailnet_private.pem -out $API_KEYS_FOLDER/tailnet_public.pem
else
    echo "Using existing tailnet API keys..."
fi

# Setup tailnet API
echo "Starting tailnet public API on port $TAILNET_PUBLIC_API_PORT"
socat TCP-LISTEN:$TAILNET_PUBLIC_API_PORT,fork EXEC:"cat $API_KEYS_FOLDER/tailnet_public.pem" &

# Generate SSH keys
if [ ! -f "$SSH_FOLDER"/ssh_host_rsa_key ]; then
    echo "Generating SSH host keys..."
    ssh-keygen -A
    mkdir -p "$SSH_FOLDER"
    cp /etc/ssh/ssh_host_* "$SSH_FOLDER"/
else
    echo "Using existing SSH host keys..."
    cp "$SSH_FOLDER"/ssh_host_* /etc/ssh/
fi

# Start SSH server
echo "Starting SSH service for remote machines..."
/usr/sbin/sshd -D
