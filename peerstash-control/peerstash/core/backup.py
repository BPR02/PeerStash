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

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import paramiko
import restic
from oncalendar import TzIterator

from peerstash.core.db import db_add_task, db_get_host, db_get_task
from peerstash.core.utils import generate_sha1

USER = os.getenv("USER")
SFTP_PORT = 2022
QUOTA_BUFFER = 25 * 1024 * 1024 * 1024


def _get_free_space(hostname: str, port: int) -> int:
    """
    Get the amount of free bytes in the sftpgo server.
    """
    ssh = paramiko.SSHClient()

    try:
        # connect to the server (SSH keys should already be set up in ~/.ssh/)
        ssh.connect(hostname=hostname, port=port, username=USER)

        # execute the 'df' command directly in the sftp shell
        _, stdout, _ = ssh.exec_command("df")
        output = stdout.read().decode("utf-8")

        # get output
        if not output.strip():
            raise Exception("Output returned nothing.")

        # Parse output with Regex like the subprocess method
        numbers = re.findall(r"[0-9]+", output)
        if len(numbers) >= 3:
            free = numbers[2]
        else:
            raise Exception("Unable to parse output.")
    except Exception as e:
        raise RuntimeError(f"Could not get quota from SFTP server. ({e})")
    finally:
        ssh.close()

    return free


def _verify_backup_size(name: str) -> bool:
    """
    Checks if a backup will exceed the SFTPGo quota. Must be run with root permissions to access password file.
    """
    # pull info from DB
    task = db_get_task(name)
    if not task:
        raise ValueError(f"Task with name '{name}' not in DB")

    # get free space in SFTP server
    free_bytes = _get_free_space(task.hostname, SFTP_PORT)

    # get added bytes
    res = run_backup(name, True)
    added_bytes: int = res["total_bytes_processed"]

    # return true if there will be at least 25GiB of space after the backup (for pruning purposes)
    return free_bytes > (added_bytes + QUOTA_BUFFER)


def _init_repo(name: str) -> None:
    """
    Initializes a repository. Must be run with root permissions to access password file.
    """
    # pull info from DB
    task = db_get_task(name)
    if not task:
        raise ValueError(f"Task with name '{name}' not in DB")

    # initialize repo
    restic.repository = f"sftp://{USER}@{task.hostname}:{SFTP_PORT}/{task.name}"
    restic.password_file = "/tmp/peerstash/password.txt"
    restic.init()


def schedule_backup(
    paths: str | list[str],
    peer: str,
    retention: int = 8,
    schedule: str = "*-*-* 03:00:00",  # default to daily backups at 3AM (local time)
    prune_schedule: str = "Sun *-*-* 04:00:00",  # default to weekly prunes at 4AM (local time)
    exclude_patterns: Optional[str | list[str]] = None,
    name: Optional[str] = None,
) -> tuple[str, datetime]:
    """
    Schedules a recurring backup.
    """
    # generate name if not specified
    if not name:
        name = generate_sha1(f"{paths}{peer}{schedule}{retention}{datetime.now()}")

    # validate include paths
    if isinstance(paths, str):
        paths = [paths]
    resolved_paths = [
        str(Path(f"/mnt/peerstash_root/{p}").expanduser().resolve()) for p in paths
    ]
    for p in resolved_paths:
        if not p.startswith("/mnt/peerstash"):
            raise ValueError(f"invalid path included")

    # format include into a delimited string
    include = "|".join(resolved_paths)

    # format exclude into a delimited string
    if isinstance(exclude_patterns, str):
        exclude = exclude_patterns.replace("|", "_")
    elif isinstance(exclude_patterns, list):
        exclude = "|".join([x.replace("|", "_") for x in exclude_patterns])
    else:
        exclude = None

    # verify peer exists
    if db_get_host(peer) is None:
        raise ValueError(f"Peer {peer} does not exist")
    # then create standard hostname
    hostname = f"peerstash-{peer}"

    # validate schedule
    try:
        iterator = TzIterator(schedule, datetime.now().astimezone())
        next_elapse = next(iterator)
    except Exception as e:
        raise ValueError(f"schedule '{schedule}' is invalid ({e})")

    # validate retention amount
    if retention < 1:
        raise ValueError(f"retention must be 1 or more")

    # insert into db
    if db_get_task(name) is not None:
        raise ValueError(f"Backup task with name '{name}' already exists")
    db_add_task(name, include, exclude, hostname, schedule, retention, prune_schedule)

    # create systemd task
    # TODO!

    # return name and next elapse for output
    return (name, next_elapse)


def run_backup(name: str, dry_run: bool = False, init: bool = False) -> dict[str, Any]:
    """
    Runs a backup. Must be run with root permissions to access password file.
    """
    # initialize repo
    if init:
        _init_repo(name)

    # dry run first to see if there's enough storage
    if not dry_run and not _verify_backup_size(name):
        if init:
            raise RuntimeError(
                f"Not enough storage to create initial backup for task '{name}'"
            )
        # attempt to prune, leaving only 1 snapshot
        prune_repo(name, 1)
        if not _verify_backup_size(name):
            raise RuntimeError(f"Not enough storage to complete task '{name}'")

    # pull info from DB
    task = db_get_task(name)
    if not task:
        raise ValueError(f"Task with name '{name}' not in DB")

    # parse include and exclude delimited strings
    paths = task.include.split("|")
    exclude_patterns = task.exclude.split("|") if task.exclude else None

    # run backup
    restic.repository = f"sftp://{USER}@{task.hostname}:{SFTP_PORT}/{task.name}"
    restic.password_file = "/tmp/peerstash/password.txt"
    res = restic.backup(
        paths=paths,
        exclude_patterns=exclude_patterns,
        dry_run=dry_run,
        scan=dry_run,
        skip_if_unchanged=True,
    )

    if not restic.check(read_data=True):
        raise RuntimeError(f"Repository '{restic.repository}' is corrupted.")

    return res


def prune_repo(name: str, forced_retention: Optional[int] = None) -> None:
    """
    Prunes a repo according to retention policy. Must be run with root permissions to access password file.
    """
    # pull info from DB
    task = db_get_task(name)
    if not task:
        raise ValueError(f"Task with name '{name}' not in DB")

    retention = forced_retention if forced_retention else int(task.retention)

    # run forget and prune
    restic.repository = f"sftp://{USER}@{task.hostname}:{SFTP_PORT}/{task.name}"
    restic.password_file = "/tmp/peerstash/password.txt"
    restic.forget(keep_last=retention, prune=True)
