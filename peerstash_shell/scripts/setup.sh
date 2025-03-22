#!/bin/sh

DB_PATH="/peerstash/config/users.db"
API_PORT=20461
WEB_APP_PUBKEY_PATH="/peerstash/config/web_app_public.pem"

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
echo "Starting API on port $API_PORT"
socat TCP-LISTEN:$API_PORT,fork EXEC:"/peerstash/scripts/api_handler.sh" &

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
    echo "Web app public key not received, closing API (port $API_PORT)"
    killall socat
    sleep 2
else
    echo "Web app public key received!"
fi

# Start SSH server
if [ ! -f /peerstash/config/ssh_host_rsa_key ]; then
    echo "Generating SSH host keys..."
    ssh-keygen -A
    cp /etc/ssh/ssh_host_* /peerstash/config/
else
    echo "Using existing SSH host keys..."
    cp /peerstash/config/ssh_host_* /etc/ssh/
fi
echo "Starting SSH service for remote machines..."
/usr/sbin/sshd -D
