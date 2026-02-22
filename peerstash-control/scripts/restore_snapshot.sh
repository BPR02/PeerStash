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
    echo "Usage: $(basename "$0") REPO SNAPSHOT FOLDER" >&2
    exit 1
fi

REPO="$1"
SNAPSHOT="$2"
FOLDER="$3"

# restore into temporary location
if ! restic restore "$SNAPSHOT" -r "$REPO" --password-file /tmp/peerstash/password.txt --target /tmp/peerstash/restore; then
    exit 2
fi

# move to bind mount
if ! mv /tmp/peerstash/restore/mnt/peerstash_root /mnt/peerstash_restore/"$FOLDER"; then
    exit 3
fi

if ! rm -rf /tmp/peerstash/restore; then
    exit 3
fi
