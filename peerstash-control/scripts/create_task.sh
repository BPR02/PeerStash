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


if [ -z $1 ] || [ -z $2 ] || [ -z $3 ]; then
    echo "Usage: $(basename "$0") TASK_NAME SCHEDULE PRUNE_SCHEDULE" >&2
    exit 1
fi

TASK_NAME=$1
SCHEDULE=$2
PRUNE_SCHEDULE=$3

# validate task name
if ! expr "$TASK_NAME" : '^[a-zA-Z-_0-9]+$' >/dev/null; then
    echo "Task name contains invalid characters" >&2
fi

# create scheduled backup
{
    echo "[Unit]"
    echo "Description=Peerstash Backup - $TASK_NAME"
    echo ""

    echo "[Service]"
    echo "ExecStart=peerstash backup $TASK_NAME"
} >> /etc/systemd/system/"peerstash_backup-$TASK_NAME.service"

{
    echo "[Unit]"
    echo "Description=Peerstash Backup - $TASK_NAME"
    echo ""

    echo "[Timer]"
    echo "OnCalendar=$SCHEDULE"
    echo "RandomizedDelaySec=600"
    echo ""

    echo "[Install]"
    echo "WantedBy=timers.target"
} >> /etc/systemd/system/"peerstash_backup-$TASK_NAME.timer"


# create scheduled prune
{
    echo "[Unit]"
    echo "Description=Peerstash Prune - $TASK_NAME"
    echo ""

    echo "[Service]"
    echo "ExecStart=peerstash prune $TASK_NAME"
} >> /etc/systemd/system/"peerstash_prune-$TASK_NAME.service"

{
    echo "[Unit]"
    echo "Description=Peerstash Prune - $TASK_NAME"
    echo ""

    echo "[Timer]"
    echo "OnCalendar=$PRUNE_SCHEDULE"
    echo "RandomizedDelaySec=600"
    echo ""

    echo "[Install]"
    echo "WantedBy=timers.target"
} >> /etc/systemd/system/"peerstash_prune-$TASK_NAME.timer"

# start services
systemctl daemon-reload
systemctl start "peerstash_backup-$TASK_NAME"
systemctl start "peerstash_prune-$TASK_NAME"
systemctl enable "peerstash_backup-$TASK_NAME"
systemctl enable "peerstash_prune-$TASK_NAME"
