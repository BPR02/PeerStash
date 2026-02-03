#!/bin/sh

SSH_FOLDER="/var/lib/peerstash"

# Generate SSH keys
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
export API_KEY=$(curl -sS --request POST \
    --url http://localhost:8080/api/v2/apikeys \
    --header "Authorization: Bearer $TOKEN" \
    --data '{
        "name": "host",
        "scope": 1,
        "admin": "'"$USERNAME"'"
}') # | grep -o '"key": "[^"]*' | grep -o '[^"]*$')

echo $API_KEY

curl -sS --request PUT \
    --url http://localhost:8080/api/v2/admin/profile \
    --header "Authorization: Bearer $TOKEN" \
    --data '{"allow_api_key_auth": true}'

# Start SSH server
echo "Starting SSH service for remote machines..."
/usr/sbin/sshd -D
