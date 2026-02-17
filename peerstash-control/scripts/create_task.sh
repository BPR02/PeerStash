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

TASK_NAME="$1"
SCHEDULE="$2"
PRUNE_SCHEDULE="$3"

# validate task name
case "$TASK_NAME" in
    *[!a-zA-Z0-9_-]*|"") 
        echo "Task name contains invalid characters." >&2
        exit 1 
        ;;
esac

# validate cron expressions (Whitelist: 0-9, space, *, /, ,, -)
case "$SCHEDULE" in
    *[!0-9\ */,-]*|"")
        echo "Schedule contains invalid characters." >&2
        exit 1
        ;;
esac

case "$PRUNE_SCHEDULE" in
    *[!0-9\ */,-]*|"")
        echo "Prune schedule contains invalid characters." >&2
        exit 1
        ;;
esac

# Define the cron jobs, randomize jobs by up to 10 minutes
BACKUP_JOB="$SCHEDULE sleep \$(od -vAn -N2 -tu2 < /dev/urandom | awk '{print \$1 % 600}') && peerstash backup $TASK_NAME"
PRUNE_JOB="$PRUNE_SCHEDULE sleep \$(od -vAn -N2 -tu2 < /dev/urandom | awk '{print \$1 % 600}') && peerstash prune $TASK_NAME"

# Update crontab (removes old entries for this task to prevent duplicates)
(
    # Get current crontab, hide errors if empty, and strip out existing jobs for this task
    crontab -l 2>/dev/null | grep -v "peerstash .* $TASK_NAME$"
    # Append the new jobs
    echo "$BACKUP_JOB"
    echo "$PRUNE_JOB"
) | crontab -

echo "Successfully scheduled '$TASK_NAME' in crontab."
