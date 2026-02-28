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

import fcntl
import hashlib
import os
import re
import subprocess
from enum import StrEnum
from io import TextIOWrapper
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, model_validator


def get_disk_usage(user, hostname: str, port: int) -> tuple[int,int,int]:
    """
    Get the amount of total, used, and free bytes in a sftp server.
    Written to work with `df` sftp command used by SFTPGo and may not work
    with other SFTP servers that return information in different formats.
    """
    try:
        # connect to the server (SSH keys should already be set up in ~/.ssh/)
        process = subprocess.run(
            ["sftp", "-P", f"{port}", f"{user}@{hostname}"],
            input="df\nbye\n",
            capture_output=True,
            text=True,
            check=True,
        )
        output = process.stdout

        # get output
        if not output.strip():
            raise Exception("Output returned nothing.")

        # Parse output with Regex like the subprocess method
        numbers = re.findall(r"[0-9]+", output)
        if len(numbers) >= 3:
            # get values in bytes (SFTPGo formats the values in KiB)
            total = int(numbers[0]) * 1024
            used = int(numbers[1]) * 1024
            free = int(numbers[2]) * 1024
        else:
            raise Exception("Unable to parse output.")
    except Exception as e:
        raise RuntimeError(f"Could not get quota from SFTP server. ({e})")

    return (total, used, free)


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


class RetentionUnit(StrEnum):
    YEAR = "y"
    MONTH = "m"
    WEEK = "w"
    DAY = "d"
    HOUR = "h"
    RECENT = "r"


RETENTION_PATTERN = re.compile(r"(?P<value>\d+)(?P<unit>[ymwdhr])")


class Retention(BaseModel):
    recent: Optional[int] = None
    hourly: Optional[int] = None
    daily: Optional[int] = None
    weekly: Optional[int] = None
    monthly: Optional[int] = None
    yearly: Optional[int] = None

    @model_validator(mode="before")
    @classmethod
    def parse_string(cls, value):
        if isinstance(value, str):
            matches = list(RETENTION_PATTERN.finditer(value))

            if not matches or "".join(m.group(0) for m in matches) != value:
                raise ValueError(f"Invalid retention string '{value}'")

            field_map: dict[RetentionUnit, str] = {
                RetentionUnit.YEAR: "yearly",
                RetentionUnit.MONTH: "monthly",
                RetentionUnit.WEEK: "weekly",
                RetentionUnit.DAY: "daily",
                RetentionUnit.HOUR: "hourly",
                RetentionUnit.RECENT: "recent",
            }

            data: dict[str, int] = {}

            for match in matches:
                amount = int(match.group("value"))
                unit_str = match.group("unit")

                if unit_str not in field_map:
                    raise ValueError(f"Invalid unit '{unit_str}'")

                unit = RetentionUnit(unit_str)
                field_name = field_map[unit]

                if field_name in data:
                    raise ValueError(f"Duplicate unit '{unit}'")

                data[field_name] = amount

            return data

        return value

    @classmethod
    def from_string(cls, value: str) -> "Retention":
        return cls.model_validate(value)


def acquire_task_lock(name: str) -> TextIOWrapper:
    """
    Attempts to acquire an exclusive, non-blocking lock for a specific backup task.
    Raises error if the lock is already held by another process.
    """
    # Create a unique lock file for this specific task
    lock_file_path = f"/tmp/peerstash/task_{name}.lock"

    # Open the file. We must keep this file object open for the duration
    # of the backup, so we return it to prevent Python from garbage collecting it.
    lock_file = open(lock_file_path, "w")

    try:
        # LOCK_EX: Exclusive lock (only one process can hold it)
        # LOCK_NB: Non-blocking (fail immediately instead of waiting in line)
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)

        # Write the current Process ID (PID) into the lock file for debugging
        lock_file.write(str(os.getpid()))
        lock_file.flush()

        return lock_file

    except BlockingIOError:
        # If we hit this block, another process has the lock.
        raise RuntimeError(
            f"Backup task '{name}' is already running in another process."
        )


def release_lock(lock_file: TextIOWrapper) -> None:
    fcntl.flock(lock_file, fcntl.LOCK_UN)
    lock_file.close()


def verify_sudo_password(password: str):
    """Verifies the sudo password without executing a persistent command."""
    try:
        # -k invalidates the user's cached sudo credentials
        subprocess.run(["sudo", "-k"], capture_output=True)

        # -S reads from stdin, -v validates the user's credentials
        subprocess.run(
            ["sudo", "-S", "-v"],
            input=f"{password}\n".encode(),
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError:
        raise ValueError("Invalid admin password.")


def gen_restic_pass(username: str, admin_pass: str) -> None:
    """
    Deterministically generates the restic password and securely stores it
    in a read-only file for resticpy and crontab to use.
    """
    # hash the password with username as salt (i.e. deterministic)
    raw_material = f"{username}:{admin_pass}".encode("utf-8")
    restic_password = hashlib.sha256(raw_material).hexdigest()

    # write to permanent storage
    pass_file = Path("/var/lib/peerstash/restic_password")
    pass_file.unlink(missing_ok=True)
    pass_file.write_text(f"---DO NOT SHARE---\n{restic_password}\nTHIS PASSWORD WAS GENERATED BY PEERSTASH\n")

    # set permissions
    os.chmod(pass_file, 0o400)


def sizeof_fmt(num: float, suffix="B") -> str:
    """
    Formats number of bytes to be human readable
    
    Source - https://stackoverflow.com/a/1094933
    Posted by Sridhar Ratnakumar, modified by community. See post 'Timeline' for change history
    Retrieved 2026-02-28, License - CC BY-SA 4.0
    """
    for unit in ("", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"):
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"

