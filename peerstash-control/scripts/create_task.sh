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


if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ]; then
    echo "Usage: $(basename "$0") TASK_NAME SCHEDULE PRUNE_SCHEDULE" >&2
    exit 1
fi

TASK_NAME=$1
SCHEDULE=$2
PRUNE_SCHEDULE=$3

# validate task name
if ! expr "$TASK_NAME" : '^[a-zA-Z0-9_-]+$' >/dev/null; then
    echo "Task name contains invalid characters" >&2
    exit 1
fi

# soft validate cron expression (error if any potentially malicious characters exist)
if echo "$SCHEDULE" | grep -q "[a-z|&><]"; then
    echo "Schedule contains invalid characters" >&2
    exit 1
fi

# soft validate cron expression (error if any potentially malicious characters exist)
if echo "$PRUNE_SCHEDULE" | grep -q "[a-z|&><]"; then
    echo "Prune schedule contains invalid characters" >&2
    exit 1
fi

# Define the cron jobs, randomize jobs by up to 10 minutes
BACKUP_JOB="$SCHEDULE sleep \$(od -vAn -N2 -tu2 < /dev/urandom | awk '{print \$1 % 600}') && peerstash backup $TASK_NAME"
PRUNE_JOB="$PRUNE_SCHEDULE sleep \$(od -vAn -N2 -tu2 < /dev/urandom | awk '{print \$1 % 600}') && peerstash prune $TASK_NAME"

# Append the new jobs to the current crontab
(crontab -l 2>/dev/null; echo "$BACKUP_JOB"; echo "$PRUNE_JOB") | crontab -

echo "Successfully scheduled '$TASK_NAME' in crontab."
