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

import typer

from peerstash.core import registration
from peerstash.core.db import db_host_exists

DEFAULT_QUOTA_GB = os.getenv("DEFAULT_QUOTA_GB", "10")

app = typer.Typer()


@app.command(name="register")
def register_peer(
    share_key: str = typer.Argument(..., help="The share key provided by the peer"),
    quota_gb: int = typer.Argument(DEFAULT_QUOTA_GB, help="Quota in GiB"),
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Overwrite existing user without prompting"
    ),
):
    """
    Register a new peer using their Share Key.
    """
    try:
        # get username from share key
        user_data = registration.parse_share_key(share_key)
        username = user_data["username"]

        exists = db_host_exists(f"peerstash-{username}")

        # ask if overwriting is okay if host exists already
        if exists:
            if not yes:
                confirm = typer.confirm(
                    f"User '{username}' already exists. Do you want to overwrite their keys and quota?",
                    default=False,
                )
                if not confirm:
                    raise typer.Abort("Aborted user update.")

            typer.secho(f"Updating user {username}...", fg=typer.colors.YELLOW)
        else:
            typer.secho(f"Creating new user {username}...", fg=typer.colors.GREEN)

        # update or insert peer
        registration.upsert_peer(user_data, quota_gb, allow_update=exists)

        typer.secho(
            f"Success! User {username} created with quota of {quota_gb} GiB",
            fg=typer.colors.GREEN,
            bold=True,
        )

        # open invite url
        invite_code = user_data["invite_code"]
        invite_url = f"https://login.tailscale.com/admin/invite/{invite_code}"
        typer.secho(
            f"Accept the tailscale invite at {invite_url}.",
            fg=typer.colors.YELLOW
        )
        typer.launch(invite_url)

    except RuntimeError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    except ValueError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.secho(f"System Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
