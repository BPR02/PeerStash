#!/bin/bash

# Peerstash
# Copyright (C) 2026 BPR02

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


PEERSTASH_CONFIG="/var/lib/peerstash"
chown "$USERNAME":"$USERNAME" $PEERSTASH_CONFIG

# set up logging
LOG_DIR="/var/log/peerstash"
mkdir -p "$LOG_DIR"

BIND_LOG_DIR="$PEERSTASH_CONFIG/logs"
mkdir -p "$BIND_LOG_DIR"

if [ ! -L "$LOG_DIR" ]; then
    # symlink logs to bind mount
    rm -rf "$LOG_DIR"
    ln -s "$BIND_LOG_DIR" "$LOG_DIR"
fi

LOG_FILE="$LOG_DIR/peerstash.log"

touch "$LOG_DIR/supervisord.log"
touch "$LOG_DIR/sshd.log"
touch "$LOG_FILE"
chmod 666 "$LOG_FILE"

# Prepend timestamp and log to both stdout and the log file
exec 3>&1 4>&2
exec > >(while IFS= read -r line; do echo "[$(date '+%Y-%m-%d %H:%M:%S')] $line"; done | tee -a "$LOG_FILE") 2>&1

# Generate SSH host keys
mkdir -p /var/run/sshd

if [ ! -f "$PEERSTASH_CONFIG"/ssh_host_rsa_key ]; then
    echo "Generating SSH host keys..."
    ssh-keygen -A
    cp /etc/ssh/ssh_host_* "$PEERSTASH_CONFIG"/
else
    echo "Using existing SSH host keys..."
    cp "$PEERSTASH_CONFIG"/ssh_host_* /etc/ssh/
fi

# create admin user
useradd -m -s /bin/bash "$USERNAME"
echo "$USERNAME:$PASSWORD" | chpasswd
adduser "$USERNAME" sudo

# Generate SSH user keys
mkdir -p /home/"$USERNAME"/.ssh

if [ ! -f "$PEERSTASH_CONFIG"/id_ed25519 ]; then
    echo "Generating SSH user keys..." >&2
    if [ ! -f /home/"$USERNAME"/.ssh/id_ed25519 ]; then
        ssh-keygen -t ed25519 -N "" -f /home/"$USERNAME"/.ssh/id_ed25519 -C "$USERNAME"
    fi
    cp /home/"$USERNAME"/.ssh/id_* $PEERSTASH_CONFIG/
else
    echo "Using existing SSH user keys..." >&2
    cp $PEERSTASH_CONFIG/id_* /home/"$USERNAME"/.ssh/
fi
{
    echo "" 
    echo "Host *" 
    echo "	IdentityFile /home/$USERNAME/.ssh/id_ed25519"
} > /home/"$USERNAME"/.ssh/config
echo "" > /home/"$USERNAME"/.ssh/known_hosts
chown -R "$USERNAME":"$USERNAME" /home/"$USERNAME"/.ssh


# prevent indexing FUSE mounts
touch /tmp/peerstash_mnt/.nomedia
touch /tmp/peerstash_mnt/.trackerignore
touch /tmp/peerstash_mnt/.hidden

# Run the python init script as root before starting services
echo "Updating SFPTGo and Database..."
/usr/local/bin/peerstash-init

# copy user ssh keys to root user
mkdir -p /root/.ssh
cp /home/"$USERNAME"/.ssh/config /root/.ssh/config
cp /home/"$USERNAME"/.ssh/known_hosts /root/.ssh/known_hosts

# clear password from environment
unset PASSWORD

# start supervisord management
echo "Starting Supervisord..."
exec 1>&3 2>&4
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
