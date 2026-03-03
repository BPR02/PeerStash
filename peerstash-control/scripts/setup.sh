#!/bin/sh

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


SSH_FOLDER="/var/lib/peerstash"


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
adduser "$USERNAME" sudo

# Generate SSH user keys
mkdir -p /home/"$USERNAME"/.ssh

if [ ! -f "$SSH_FOLDER"/id_ed25519 ]; then
    echo "Generating SSH user keys..." >&2
    if [ ! -f /home/"$USERNAME"/.ssh/id_ed25519 ]; then
        ssh-keygen -t ed25519 -N "" -f /home/"$USERNAME"/.ssh/id_ed25519 -C "$USERNAME"
    fi
    cp /home/"$USERNAME"/.ssh/id_* $SSH_FOLDER/
else
    echo "Using existing SSH user keys..." >&2
    cp $SSH_FOLDER/id_* /home/"$USERNAME"/.ssh/
fi
{
    echo "" 
    echo "Host *" 
    echo "	IdentityFile /home/$USERNAME/.ssh/id_ed25519"
} > /home/"$USERNAME"/.ssh/config
echo "" > /home/"$USERNAME"/.ssh/known_hosts
chown -R "$USERNAME":"$USERNAME" /home/"$USERNAME"/.ssh

# set up logging
touch /var/log/peerstash-cron.log

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
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
