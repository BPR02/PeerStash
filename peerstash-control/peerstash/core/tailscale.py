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
import subprocess
from contextlib import closing

import commentjson
import requests
from cryptography.fernet import Fernet

from peerstash.core.utils import derive_key

DB_PATH = os.getenv("DB_PATH", "/var/lib/peerstash/peerstash.db")
TAILSCALE_API = "https://api.tailscale.com/api/v2"


def store_credentials(plaintext_password: str, client_id: str, client_secret: str):
    """
    Stores encrypted Client ID and Secret in the database.
    """
    salt = os.urandom(16)
    key = derive_key(plaintext_password, salt)
    fernet = Fernet(key)

    enc_client_id = fernet.encrypt(client_id.encode())
    enc_client_secret = fernet.encrypt(client_secret.encode())

    with closing(sqlite3.connect(DB_PATH)) as conn:
        with conn:
            conn.execute(
                """
                INSERT INTO tailscale_auth (id, salt, encrypted_client_id, encrypted_client_secret)
                VALUES (1, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    salt=excluded.salt,
                    encrypted_client_id=excluded.encrypted_client_id,
                    encrypted_client_secret=excluded.encrypted_client_secret
            """,
                (salt, enc_client_id, enc_client_secret),
            )


def get_credentials(plaintext_password: str) -> tuple[str, str]:
    """
    Pulls decrypted Client ID and Secret from the database.
    """
    if not os.path.exists(DB_PATH):
        raise ValueError("No credentials found in the database.")

    try:
        with closing(sqlite3.connect(DB_PATH)) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT salt, encrypted_client_id, encrypted_client_secret FROM tailscale_auth WHERE id = 1"
            )
            row = cursor.fetchone()
    except sqlite3.OperationalError:
        raise ValueError("No credentials found in the database.")

    if not row:
        raise ValueError("No credentials found in the database.")

    salt, enc_client_id, enc_client_secret = row

    try:
        key = derive_key(plaintext_password, salt)
        fernet = Fernet(key)
        return (
            fernet.decrypt(enc_client_id).decode(),
            fernet.decrypt(enc_client_secret).decode(),
        )
    except Exception as e:
        raise ValueError(
            "Decryption failed. Invalid admin password or corrupted data."
        ) from e


def bootstrap_tag(api_token: str):
    """
    Creates the peerstash tag via a Tailscale API access token.
    """
    base_url = f"{TAILSCALE_API}/tailnet/-/acl"
    auth = (api_token, "")
    headers = {"Accept": "application/hujson"}

    get_resp = requests.get(base_url, auth=auth, headers=headers)
    get_resp.raise_for_status()
    etag = get_resp.headers.get("ETag")
    policy = commentjson.loads(get_resp.text)

    if "tagOwners" not in policy:
        policy["tagOwners"] = {}

    # If it doesn't exist, add it and push
    if "tag:peerstash" not in policy["tagOwners"]:
        policy["tagOwners"]["tag:peerstash"] = ["autogroup:admin"]
        headers = {"If-Match": etag}
        post_data = commentjson.dumps(policy, indent=4)
        post_resp = requests.post(base_url, auth=auth, headers=headers, data=post_data)
        post_resp.raise_for_status()


def get_oauth_token(client_id: str, client_secret: str) -> str:
    """
    Generates an OAuth token from the OAuth Client.
    """
    auth_url = f"{TAILSCALE_API}/oauth/token"
    response = requests.post(
        auth_url,
        auth=(client_id, client_secret),
        data={"grant_type": "client_credentials"},
    )
    response.raise_for_status()
    return response.json()["access_token"]


def modify_policy(token: str):
    """
    Updates the Access Control policy to limit the ports viewable by peerstash machines.
    """
    base_url = f"{TAILSCALE_API}/tailnet/-/acl"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/hujson"}

    get_resp = requests.get(base_url, headers=headers)
    get_resp.raise_for_status()
    etag = get_resp.headers.get("ETag")
    policy = commentjson.loads(get_resp.text)

    if "acls" in policy:
        policy["acls"] = [
            rule
            for rule in policy["acls"]
            if not (rule.get("src") == ["*"] and rule.get("dst") == ["*:*"])
        ]

    if "grants" in policy:
        policy["grants"] = [
            rule
            for rule in policy["grants"]
            if not (
                rule.get("src") == ["*"]
                and rule.get("dst") == ["*"]
                and rule.get("ip") == ["*"]
            )
        ]
    else:
        policy["grants"] = []

    new_grants = [
        {"src": ["autogroup:member"], "dst": ["autogroup:member"], "ip": ["*"]},
        {"src": ["autogroup:member"], "dst": ["tag:peerstash"], "ip": ["tcp:2022"]},
        {"src": ["tag:peerstash"], "dst": ["tag:peerstash"], "ip": ["tcp:2022"]},
    ]

    for rule in new_grants:
        if rule not in policy["grants"]:
            policy["grants"].append(rule)

    headers["If-Match"] = etag if etag else ""
    post_data = commentjson.dumps(policy, indent=4)
    post_resp = requests.post(base_url, headers=headers, data=post_data)
    post_resp.raise_for_status()


def _generate_auth_key(token: str) -> str:
    """
    Generates an Auth Key to register a device.
    """
    key_url = f"{TAILSCALE_API}/tailnet/-/keys"
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "capabilities": {
            "devices": {
                "create": {
                    "reusable": False,
                    "ephemeral": False,
                    "preauthorized": True,
                    "tags": ["tag:peerstash"],
                }
            }
        }
    }

    response = requests.post(key_url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()["key"]


def register_device(token: str):
    """
    Registers a device with an Auth key.
    """
    auth_key = _generate_auth_key(token)
    subprocess.run(
        ["tailscale", "up", "--authkey", auth_key], check=True, capture_output=True
    )
