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

import json
import os
import subprocess
from typing import Optional

import commentjson
import requests

DB_PATH = os.getenv("DB_PATH", "/var/lib/peerstash/peerstash.db")
TAILSCALE_API = "https://api.tailscale.com/api/v2"


def revoke_api_token(api_token: str) -> bool:
    """Attempts to revoke the temporary API token to ensure it is immediately invalidated."""
    try:
        # Extract the ID from the token (Format: tskey-api-ID-SECRET)
        parts = api_token.split("-")
        if len(parts) >= 4 and parts[0] == "tskey" and parts[1] == "api":
            key_id = parts[2]
            url = f"{TAILSCALE_API}/tailnet/-/keys/{key_id}"

            # The token authenticates its own deletion
            response = requests.delete(url, auth=(api_token, ""))
            response.raise_for_status()
            return True
        return False
    except Exception as e:
        return False


def modify_policy(api_token: str):
    """
    Updates the Access Control policy to limit the ports viewable by peerstash machines.
    """
    base_url = f"{TAILSCALE_API}/tailnet/-/acl"
    headers = {"Accept": "application/hujson"}

    get_resp = requests.get(base_url, auth=(api_token, ""), headers=headers)
    get_resp.raise_for_status()
    etag = get_resp.headers.get("ETag")
    policy = commentjson.loads(get_resp.text)

    # add peerstash tag
    if "tagOwners" not in policy:
        policy["tagOwners"] = {}

    if "tag:peerstash" not in policy["tagOwners"]:
        policy["tagOwners"]["tag:peerstash"] = ["autogroup:admin"]

    # remove default allow-all from ACLs
    if "acls" in policy:
        policy["acls"] = [
            rule
            for rule in policy["acls"]
            if not (rule.get("src") == ["*"] and rule.get("dst") == ["*:*"])
        ]

    # remove default allow-all from grants
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

    # add new grants for proper routing
    new_grants = [
        {"src": ["autogroup:member"], "dst": ["autogroup:member"], "ip": ["*"]},
        {"src": ["autogroup:member"], "dst": ["tag:peerstash"], "ip": ["tcp:2022"]},
        {"src": ["tag:peerstash"], "dst": ["tag:peerstash"], "ip": ["tcp:2022"]},
    ]

    for rule in new_grants:
        if rule not in policy["grants"]:
            policy["grants"].append(rule)

    # push new policy
    headers["If-Match"] = etag if etag else ""
    post_data = commentjson.dumps(policy, indent=4)
    post_resp = requests.post(base_url, headers=headers, data=post_data)
    post_resp.raise_for_status()


def _generate_auth_key(api_token: str) -> str:
    """
    Generates an Auth Key to register a device.
    """
    key_url = f"{TAILSCALE_API}/tailnet/-/keys"

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

    response = requests.post(key_url, auth=(api_token, ""), json=payload)
    response.raise_for_status()
    return response.json()["key"]


def register_device(api_token: str, password: str) -> None:
    """
    Registers a device with an Auth key.
    """
    auth_key = _generate_auth_key(api_token)
    subprocess.run(
        ["sudo", "-S", "tailscale", "up", "--authkey", auth_key],
        input=f"{password}\n".encode(),
        check=True,
        capture_output=True,
    )


def _get_local_device_id() -> str:
    try:
        result = subprocess.run(
            ["tailscale", "status", "--json"],
            capture_output=True,
            text=True,
            check=True,
        )
        status_data = json.loads(result.stdout)
        device_id = status_data.get("Self", {}).get("ID")
        if not device_id:
            raise ValueError("Could not find 'ID'. Is the node connected?")
        return str(device_id)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to query local Tailscale status: {e.stderr}")


def generate_device_invite(api_token: str) -> Optional[str]:
    device_id = _get_local_device_id()
    url = f"{TAILSCALE_API}/device/{device_id}/device-invites"
    payload = {"multiUse": True}
    response = requests.post(url, auth=(api_token, ""), json=payload)
    response.raise_for_status()

    full_url: Optional[str] = response.json().get("inviteUrl")
    return full_url.split("/")[-1] if full_url else None
