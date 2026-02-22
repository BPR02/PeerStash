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

import base64
import json
import os
import subprocess
from typing import Dict

import requests

from peerstash.core.db import db_add_host, db_host_exists, db_update_host

SSH_FOLDER = os.getenv("SSH_FOLDER", "~/.ssh")
DB_PATH = os.getenv("DB_PATH", "/var/lib/peerstash/peerstash.db")
SFTPGO_URL = "http://localhost:8080/api/v2"
API_KEY = os.getenv("API_KEY", "")


class PeerExistsError(Exception):
    """Raised when trying to register a peer that already exists."""

    pass


def _update_known_hosts(
    username: str, server_public_key: str, replace: bool = False
) -> None:
    """
    Updates ~/.ssh/known_hosts.
    """
    hosts_file = os.path.expanduser("~/.ssh/known_hosts")
    host_entry = f"[peerstash-{username}]:2022 {server_public_key}"

    # ensure directory exists
    os.makedirs(os.path.dirname(hosts_file), exist_ok=True)

    # create file if it doesn't exist
    if not os.path.exists(hosts_file):
        with open(hosts_file, "w") as f:
            pass

    if replace:
        # get each line of hosts file
        with open(hosts_file, "r") as f:
            lines = f.readlines()

        # write back, replacing the specific host line
        with open(hosts_file, "w") as f:
            for line in lines:
                if line.strip().startswith(f"[peerstash-{username}]"):
                    f.write(f"{host_entry}\n")
                else:
                    f.write(line)

    else:
        # append a new line into the hosts file
        with open(hosts_file, "a") as f:
            f.write(f"\n{host_entry}\n")

    # sync to root user
    subprocess.run("/srv/peerstash/bin/sync_hosts")


def parse_share_key(share_key: str) -> Dict[str, str]:
    """Decodes the base64 share key."""
    try:
        # decode base64 string
        check, clean_key = share_key.split("#")
        check_username = check.split(".")[-1]
        decoded_json = base64.b64decode(clean_key, altchars=b"-_").decode("utf-8")
        data = json.loads(decoded_json)
        # check if username in key matches in username data
        if data["username"] != check_username:
            raise Exception(f"username does not match hash")

        return data
    except Exception as e:
        raise ValueError(f"Invalid share key: {e}")


def upsert_peer(user_data: Dict[str, str], quota_gb: int, allow_update: bool = False):
    """
    Creates or Updates a peer in SFTPGo and the System.
    """
    username = user_data["username"]

    # check if this peer already exists (DB-SFTPGo desync, requires manual fix)
    if db_host_exists(f"peerstash-{username}") and not allow_update:
        raise PeerExistsError(f"User {username} already exists.")

    # set up sftpgo request
    quota_bytes = quota_gb * 1024 * 1024 * 1024
    payload = {
        "status": 1,
        "username": username,
        "public_keys": [user_data["client_public_key"]],
        "quota_size": quota_bytes,
        "permissions": {"/": ["*"]},
    }
    headers = {"X-SFTPGO-API-KEY": API_KEY}

    # make sftpgo api request
    method = requests.put if allow_update else requests.post
    url = f"{SFTPGO_URL}/users/{username}" if allow_update else f"{SFTPGO_URL}/users"

    resp = method(url, json=payload, headers=headers)
    if resp.status_code == 409:
        # DB-SFTPGo desync, requires manual fix
        raise RuntimeError(
            f"User '{username}' already exists in SFTPGo. Database might be corrupted."
        )
    else:
        resp.raise_for_status()

    # update known_hosts file for ssh
    _update_known_hosts(username, user_data["server_public_key"], allow_update)

    # update hosts table
    if not allow_update:
        db_add_host(f"peerstash-{username}", user_data["server_public_key"])
    else:
        db_update_host(f"peerstash-{username}", user_data["server_public_key"])

    return True
