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
import re
from typing import Optional

from pydantic import BaseModel


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


class Retention(BaseModel):
    def __init__(self, input: str):
        values = [int(x) for x in (re.split(r"[a-z]", input)[:-1])]
        units: list[str] = re.split(r"[0-9]+", input)[1:]

        mapping = zip(values, units)
        for value, unit in mapping:
            match unit:
                case "y":
                    self.yearly = value
                case "m":
                    self.monthly = value
                case "w":
                    self.weekly = value
                case "d":
                    self.daily = value
                case "h":
                    self.hourly = value
                case "r":
                    self.recent = value
                case _:
                    raise ValueError(f"invalid input string '{input}'")

    recent: Optional[int] = None
    hourly: Optional[int] = None
    daily: Optional[int] = None
    weekly: Optional[int] = None
    monthly: Optional[int] = None
    yearly: Optional[int] = None
