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
useradd -rm -d /home/$USERNAME -s /bin/bash -g root -G sudo -u 1000 $USERNAME
echo "$USERNAME:$PASSWORD" | chpasswd

# Start SSH server
echo "Starting SSH service for remote machines..."
/usr/sbin/sshd -D
