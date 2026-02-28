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
from contextlib import closing
from typing import Any, Optional

from peerstash.core.db_schemas import *

DB_PATH = os.getenv("DB_PATH", "/var/lib/peerstash/peerstash.db")


def db_add_host(hostname: str, public_key: str) -> None:
    """Adds the peerstash host to the DB."""
    with closing(sqlite3.connect(DB_PATH)) as conn:
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO hosts (hostname, port, public_key) VALUES (?, ?, ?)",
                (hostname, "2022", public_key),
            )


def db_host_exists(hostname: str) -> bool:
    """Checks the DB to see if we know this peer."""
    with closing(sqlite3.connect(DB_PATH)) as conn:
        with conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM hosts WHERE hostname=?", (hostname,))
            return cursor.fetchone() is not None


def db_get_host(hostname: str) -> Optional[HostRead]:
    """Gets host entry from DB."""
    with closing(sqlite3.connect(DB_PATH)) as conn:
        with conn:
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
    with closing(sqlite3.connect(DB_PATH)) as conn:
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE hosts SET public_key = ? WHERE hostname = ?",
                (public_key, hostname),
            )


def db_delete_host(hostname: str) -> None:
    """Deletes the peerstash host from the DB."""
    with closing(sqlite3.connect(DB_PATH)) as conn:
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE hosts WHERE hostname = ?",
                (hostname),
            )


def db_list_hosts() -> list[HostRead]:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        with conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM hosts")
            results = cursor.fetchall()

    return [
        HostRead(**{key: res[i] for i, key in enumerate(HostRead.model_fields.keys())})
        for res in results
    ]


def db_add_task(
    name: str,
    include: str,
    exclude: Optional[str],
    hostname: str,
    schedule: str,
    retention: str,
    prune_schedule: str,
):
    """Adds the backup task to the DB."""
    with closing(sqlite3.connect(DB_PATH)) as conn:
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO tasks 
                   (name, include, exclude, hostname, schedule, retention, prune_schedule) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (name, include, exclude, hostname, schedule, retention, prune_schedule),
            )


def db_task_exists(name: str) -> bool:
    """Checks the DB to see if there's already a task with this name."""
    with closing(sqlite3.connect(DB_PATH)) as conn:
        with conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM tasks WHERE name=?", (name,))
            return cursor.fetchone() is not None


def db_get_task(name: str) -> Optional[TaskRead]:
    """Checks the DB to see if there's already a task with this name."""
    with closing(sqlite3.connect(DB_PATH)) as conn:
        with conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE name=?", (name,))
            res = cursor.fetchone()
            if not res:
                return None
            return TaskRead(
                **{key: res[i] for i, key in enumerate(TaskRead.model_fields.keys())}
            )


def db_update_task(name: str, data: TaskUpdate) -> Optional[TaskRead]:
    """Updates the task in the DB."""
    model_dump: dict[str, Any] = data.model_dump(
        exclude_none=True, exclude_defaults=True
    )
    if not model_dump:
        return db_get_task(name)

    fields = []
    values = list(model_dump.values())
    values.append(name)
    for key in model_dump.keys():
        fields.append(f"{key} = ?")

    with closing(sqlite3.connect(DB_PATH)) as conn:
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE tasks SET {', '.join(fields)} WHERE name = ? RETURNING *;",
                values,
            )
            res = cursor.fetchone()
            if not res:
                return None
            return TaskRead(
                **{key: res[i] for i, key in enumerate(TaskRead.model_fields.keys())}
            )


def db_delete_task(name: str) -> bool:
    """Removes the task from the DB."""
    with closing(sqlite3.connect(DB_PATH)) as conn:
        with conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tasks WHERE name = ? RETURNING name", (name,))
            res = cursor.fetchone()
            return res is not None


def db_list_tasks() -> list[TaskRead]:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        with conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks")
            results = cursor.fetchall()

    return [
        TaskRead(**{key: res[i] for i, key in enumerate(TaskRead.model_fields.keys())})
        for res in results
    ]


def db_get_user() -> Optional[str]:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        with conn:
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM node_data WHERE id = 1")
            res = cursor.fetchone()

    return res[0] if res else None


def db_get_invite_code() -> Optional[str]:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        with conn:
            cursor = conn.cursor()
            cursor.execute("SELECT invite_code FROM node_data WHERE id = 1")
            res = cursor.fetchone()

    return res[0] if res else None


def db_set_invite_code(code: str) -> None:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        with conn:
            conn.execute(
                """
                INSERT INTO node_data (id, invite_code)
                VALUES (1, ?)
                ON CONFLICT(id) DO UPDATE SET invite_code=excluded.invite_code
            """,
                (code,),
            )
