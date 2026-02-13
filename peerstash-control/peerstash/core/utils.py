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

import hashlib
import os
from typing import Optional


def get_file_content(filepath: str) -> Optional[str]:
    """Reads file content safely, handling ~ expansion and errors."""
    try:
        full_path = os.path.expanduser(filepath)
        if not os.path.exists(full_path):
            return None
        with open(full_path, "r") as f:
            content = f.read().strip()
            return content if content else None
    except Exception:
        return None


def generate_sha1(input: str) -> str:
    """Generates the SHA-1 hexadecimal hash of a given string."""
    # Create a new sha1 hash object
    sha1_hash = hashlib.sha1()

    # update the hash object with the input string encoded to bytes
    sha1_hash.update(input.encode("utf-8"))

    # return the hexadecimal digest of the hash
    return sha1_hash.hexdigest()
