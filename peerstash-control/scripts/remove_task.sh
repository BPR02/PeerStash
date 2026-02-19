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


if [ -z "$1" ]; then
    echo "Usage: $(basename "$0") TASK_NAME" >&2
    exit 1
fi

TASK_NAME="$1"

# validate task name
case "$TASK_NAME" in
    *[!a-zA-Z0-9_-]*|"") 
        echo "Task name contains invalid characters." >&2
        exit 1 
        ;;
esac

# Update crontab
if ! (
    # Get current crontab, hide errors if empty, and strip out existing jobs for this task
    crontab -l 2>/dev/null | grep -v "peerstash .* tester [0-9]* >> /var/log/peerstash-cron.log 2>&1$"
) | crontab - ; then
    echo "Failed to remove '$TASK_NAME' from crontab." >&2
    exit 1
fi

echo "Successfully removed '$TASK_NAME' from crontab."
