#!/bin/sh

SSH_FOLDER="/var/lib/peerstash"

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

# make a dummy user
adduser -D "$USERNAME"
echo "$USERNAME:$PASSWORD" | chpasswd

# Start SSH server
echo "Starting SSH service for remote machines..."
/usr/sbin/sshd -D
