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

from peerstash.core.db import db_get_invite_code, db_get_user
from peerstash.core.utils import get_file_content

USER = db_get_user()


def _generate_identity_payload() -> str:
    """
    Reads keys and returns the raw base64 string
    """
    server_pub_key = get_file_content("/var/lib/sftpgo/id_ed25519.pub")
    client_pub_key = get_file_content("~/.ssh/id_ed25519.pub")
    username = USER
    invite_code = db_get_invite_code()

    if not username:
        raise ValueError("Username not found")
    if not server_pub_key:
        raise ValueError("Host keys not found (/var/lib/sftpgo/id_ed25519.pub)")
    if not client_pub_key:
        raise ValueError("User keys not found (~/.ssh/id_ed25519.pub)")
    if not invite_code:
        raise ValueError("Invite code not found. Did you run 'peerstash setup'?")

    data = {
        "username": username,
        "server_public_key": server_pub_key,
        "client_public_key": client_pub_key,
        "invite_code": invite_code,
    }

    json_bytes = json.dumps(data).encode("utf-8")
    return base64.b64encode(json_bytes, altchars=b"-_").decode("utf-8")


def generate_share_key() -> str:
    username = USER
    payload = _generate_identity_payload()

    return f"peerstash.{username}#{payload}"
