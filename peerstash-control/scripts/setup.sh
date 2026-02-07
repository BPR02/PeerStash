#!/bin/sh

SSH_FOLDER="/var/lib/peerstash"
DB_PATH="/var/lib/peerstash/peerstash.db"

# Generate SSH host keys
mkdir -p /var/run/sshd

if [ ! -f "$SSH_FOLDER"/ssh_host_rsa_key ]; then
    echo "Generating SSH host keys..."
    ssh-keygen -A
    cp /etc/ssh/ssh_host_* "$SSH_FOLDER"/
else
    echo "Using existing SSH host keys..."
    cp "$SSH_FOLDER"/ssh_host_* /etc/ssh/
fi

# create admin user
useradd -m -s /bin/bash "$USERNAME"
echo "$USERNAME:$PASSWORD" | chpasswd

# Generate SSH user keys
mkdir -p /home/"$USERNAME"/.ssh

if [ ! -f "$SSH_FOLDER"/id_ed25519 ]; then
    echo "Generating SSH user keys..." >&2
    if [ ! -f /home/"$USERNAME"/.ssh/id_ed25519 ]; then
        ssh-keygen -t ed25519 -N "" -f /home/"$USERNAME"/.ssh/id_ed25519 -C "$USER"
    fi
    cp /home/"$USERNAME"/.ssh/id_* $SSH_FOLDER/
    { 
        echo "" 
        echo "Host *" 
        echo "	IdentityFile /home/"$USERNAME"/.ssh/id_ed25519"
    } >> /home/"$USERNAME"/.ssh/config
    touch /home/"$USERNAME"/.ssh/known_hosts
    chown -R "$USERNAME":"$USERNAME" /home/"$USERNAME"/.ssh
    cp -p /home/"$USERNAME"/.ssh/config $SSH_FOLDER/config
    cp -p /home/"$USERNAME"/.ssh/known_hosts $SSH_FOLDER/known_hosts
else
    echo "Using existing SSH user keys..." >&2
    cp $SSH_FOLDER/id_* /home/"$USERNAME"/.ssh/
    cp $SSH_FOLDER/config /home/"$USERNAME"/.ssh/config
    cp $SSH_FOLDER/known_hosts /home/"$USERNAME"/.ssh/known_hosts
    chown -R "$USERNAME":"$USERNAME" /home/"$USERNAME"/.ssh
fi

# Check if the database exists
if [ -f "$DB_PATH" ]; then
    echo "SQLite database found. Restoring backup tasks..."
    echo "TODO!"
else
    echo "No database found. Creating a new empty database..."
    sqlite3 "$DB_PATH" "CREATE TABLE hosts (\
        hostname TEXT PRIMARY KEY,\
        port INTEGER DEFAULT 2022,\
        last_seen DATETIME\
    );"
    sqlite3 "$DB_PATH" "CREATE TABLE tasks (\
        id INTEGER PRIMARY KEY AUTOINCREMENT,\
        name TEXT NOT NULL UNIQUE,\
        include TEXT NOT NULL,\
        exclude TEXT,\
        hostname TEXT NOT NULL,\
        schedule TEXT NOT NULL,\
        retention_policy TEXT NOT NULL,\
        last_run DATETIME,\
        last_exit_code INTEGER,\
        last_snapshot_id TEXT,\
        is_locked BOOLEAN DEFAULT 0,\
        FOREIGN KEY (hostname) REFERENCES hosts(hostname)\
    );"
    chown "$USERNAME":"$USERNAME" "$DB_PATH"
    chmod 700 "$DB_PATH"
fi

# get SFTPGo JWT
TOKEN=$(curl -sS -u "$USERNAME:$PASSWORD" \
    "http://localhost:8080/api/v2/token" | grep -o '"access_token":"[^"]*' | grep -o '[^"]*$')

if [ -z "$TOKEN" ]; then
    echo "Error: Authentication failed."
    exit 1
fi

# delete existing SFTPGo API keys
KEYS=$(curl -sS --request GET \
    --url http://localhost:8080/api/v2/apikeys \
    --header "Authorization: Bearer $TOKEN")

for row in $(echo "$KEYS" | jq -c '.[]'); do
    id=$(echo "${row}" | jq -r '.id')
    name=$(echo "${row}" | jq -r '.name')

    if [ "$name" = "host" ]; then
        curl -sS --request DELETE \
            --url "http://localhost:8080/api/v2/apikeys/${id}" \
            --header "Authorization: Bearer $TOKEN"
    fi
done

# create new SFTPGo API key
API_KEY=$(curl -sS --request POST \
    --url http://localhost:8080/api/v2/apikeys \
    --header "Authorization: Bearer $TOKEN" \
    --data '{
        "name": "host",
        "scope": 1,
        "admin": "'"$USERNAME"'"
}' | grep -o '"key":"[^"]*' | grep -o '[^"]*$')

# enable API key auth
curl -sS --request PUT \
    --url http://localhost:8080/api/v2/admin/profile \
    --header "Authorization: Bearer $TOKEN" \
    --data '{"allow_api_key_auth": true}'

# share environment variables
echo "export API_KEY=$API_KEY" >> /home/"$USERNAME"/.bashrc
echo "export DEFAULT_QUOTA_GB=$DEFAULT_QUOTA_GB" >> /home/"$USERNAME"/.bashrc
echo "export SSH_FOLDER=/var/lib/peerstash" >> /home/"$USERNAME"/.bashrc
echo "export DB_PATH=/var/lib/peerstash/peerstash.db" >> /home/"$USERNAME"/.bashrc

# Start SSH server
echo "Starting SSH service for remote machines..."
/usr/sbin/sshd -D
