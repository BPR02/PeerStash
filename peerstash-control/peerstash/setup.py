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
import sys
import time
import sqlite3
import socket
from typing import Any

import requests

from peerstash.core.utils import update_crontab

USERNAME = os.getenv("USERNAME", "")
PASSWORD = os.getenv("PASSWORD", "")
DEFAULT_QUOTA_GB = os.getenv("DEFAULT_QUOTA_GB", "10")
PEERSTASH_BIN = "/usr/local/bin/peerstash"
CRON_LOG = "/var/log/peerstash-cron.log"
DB_PATH = "/var/lib/peerstash/peerstash.db"
SFTPGO_URL = "http://localhost:8080/api/v2"


def init_db_and_restore():
    """Initializes the database or restores tasks/hosts if it exists."""
    db_exists = os.path.exists(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if db_exists:
        print("SQLite database found. Restoring tasks and known_hosts...")

        # Restore known_hosts
        known_hosts_path = f"/home/{USERNAME}/.ssh/known_hosts"
        cursor.execute("SELECT hostname, port, public_key FROM hosts")
        with open(known_hosts_path, "a") as f:
            for hostname, port, public_key in cursor.fetchall():
                f.write(f"\n[{hostname}]:{port} {public_key}\n")

        # Restore crontab tasks
        cursor.execute("SELECT name, schedule, prune_schedule FROM tasks")
        for name, schedule, prune_schedule in cursor.fetchall():
            backup_job = (
                f"{schedule} {PEERSTASH_BIN} backup {name} 10 >> {CRON_LOG} 2>&1"
            )
            prune_job = f"{prune_schedule} {PEERSTASH_BIN} prune {name} 10 >> {CRON_LOG} 2>&1"
            update_crontab(name, [backup_job, prune_job])

    else:
        print("No database found. Creating a new empty database...")
        cursor.executescript(
            f"""
            CREATE TABLE hosts (
                hostname TEXT PRIMARY KEY,
                port INTEGER DEFAULT 2022,
                public_key TEXT NOT NULL,
                last_seen DATETIME
            );
            CREATE TABLE tasks (
                name TEXT PRIMARY KEY,
                include TEXT NOT NULL,
                exclude TEXT,
                hostname TEXT NOT NULL,
                schedule TEXT NOT NULL,
                retention TEXT NOT NULL,
                prune_schedule TEXT NOT NULL,
                last_run DATETIME,
                last_exit_code INTEGER,
                status TEXT DEFAULT 'new',
                FOREIGN KEY (hostname) REFERENCES hosts(hostname)
            );
            CREATE TABLE node_data (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                username TEXT DEFAULT '{USERNAME}',
                invite_code TEXT
            );
            INSERT INTO node_data (id, username) VALUES (1, '{USERNAME}');
        """
        )

        # Set proper ownership for the new database
        os.chown(
            DB_PATH,
            int(os.popen(f"id -u {USERNAME}").read().strip()),
            int(os.popen(f"id -g {USERNAME}").read().strip()),
        )
        os.chmod(DB_PATH, 0o700)

    conn.commit()
    conn.close()


def wait_for_sftpgo(port=8080, timeout=60):
    """Blocks until the SFTPGo port is actively accepting connections."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection(("localhost", port), timeout=1):
                return
        except (ConnectionRefusedError, socket.timeout, OSError):
            time.sleep(1)

    print(f"Error: SFTPGo port {port} could not be reached within {timeout} seconds.")
    sys.exit(1)


def setup_sftpgo():
    """Configures SFTPGo API keys and authentication."""
    # get jwt
    resp = requests.get(f"{SFTPGO_URL}/token", auth=(USERNAME, PASSWORD))
    resp.raise_for_status()
    token: str = resp.json()["access_token"]
    if not token:
        print("Error: Authentication failed to get JWT.")
        sys.exit(1)
    headers = {"Authorization": f"Bearer {token}"}

    # delete existing 'host' API keys
    resp = requests.get(f"{SFTPGO_URL}/apikeys", headers=headers)
    resp.raise_for_status()
    keys: list[dict[str, Any]] = resp.json()
    for key in keys:
        if key.get("name") == "host":
            resp = requests.delete(f"{SFTPGO_URL}/apikeys/{key.get("id")}", headers=headers)
            resp.raise_for_status()

    # create new API key
    data = {"name": "host", "scope": 1, "admin": USERNAME}
    resp = requests.post(f"{SFTPGO_URL}/apikeys", headers=headers, json=data)
    resp.raise_for_status()
    api_key: str = resp.json()["key"]

    # enable API key auth
    data = {"allow_api_key_auth": True}
    resp = requests.put(f"{SFTPGO_URL}/admin/profile", headers=headers, json=data)
    resp.raise_for_status()

    return api_key


def main():
    if USERNAME == "":
        print("USERNAME not set in environment")
        sys.exit(1)
    if PASSWORD == "":
        print("PASSWORD not set in environment")
        sys.exit(1)

    init_db_and_restore()
    wait_for_sftpgo()
    api_key = setup_sftpgo()

    # set environment variables
    with open(f"/home/{USERNAME}/.bashrc", "a") as f:
        f.write(f"\nexport API_KEY='{api_key}'\n")
        f.write(f"export DEFAULT_QUOTA_GB='{DEFAULT_QUOTA_GB}'\n")

    print("Python initialization complete.")


if __name__ == "__main__":
    main()
