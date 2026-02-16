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
import sqlite3
from typing import Optional

from peerstash.core.db_schemas import *

DB_PATH = os.getenv("DB_PATH", "/var/lib/peerstash/peerstash.db")


def db_add_host(hostname: str, public_key: str) -> None:
    """Adds the peerstash host to the DB."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO hosts (hostname, port, public_key) VALUES (?, ?, ?)",
            (hostname, "2022", public_key),
        )
        conn.commit()
    except sqlite3.Error as e:
        raise Exception(f"Database error {e}")


def db_host_exists(hostname: str) -> bool:
    """Checks the DB to see if we know this peer."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM hosts WHERE hostname=?", (hostname,))
        return cursor.fetchone() is not None


def db_get_host(hostname: str) -> Optional[HostRead]:
    """Gets host entry from DB."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM hosts WHERE hostname=?", (hostname,))
        res = cursor.fetchone()
        if not res:
            return None
        return HostRead(
            **{key: res[i] for i, key in enumerate(HostRead.model_fields.keys())}
        )


def db_update_host(hostname: str, public_key: str) -> None:
    """Updates the peerstash host on the DB."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE hosts SET public_key = ? WHERE hostname = ?",
            (public_key, hostname),
        )
        conn.commit()
    except sqlite3.Error as e:
        raise Exception(f"Database error {e}")


def db_add_task(
    name: str,
    include: str,
    exclude: Optional[str],
    hostname: str,
    schedule: str,
    retention: int,
    prune_schedule: str,
):
    """Adds the backup task to the DB."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tasks (name, include, exclude, hostname, \
                schedule, retention, prune_schedule) \
                VALUES (?, ?, ?, ?, ?, ?, ?)",
            (name, include, exclude, hostname, schedule, retention, prune_schedule),
        )
        conn.commit()
    except sqlite3.Error as e:
        raise Exception(f"Database error {e}")


def db_task_exists(name: str) -> bool:
    """Checks the DB to see if there's already a task with this name."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM tasks WHERE name=?", (name,))
        return cursor.fetchone() is not None


def db_get_task(name: str) -> Optional[TaskRead]:
    """Checks the DB to see if there's already a task with this name."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE name=?", (name,))
        res = cursor.fetchone()
        if not res:
            return None
        return TaskRead(
            **{key: res[i] for i, key in enumerate(TaskRead.model_fields.keys())}
        )
