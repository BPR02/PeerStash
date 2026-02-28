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

from peerstash.cli.utils import check_setup
from peerstash.core import registration
from peerstash.core.db import db_host_exists

DEFAULT_QUOTA_GB = os.getenv("DEFAULT_QUOTA_GB", "10")

app = typer.Typer()


@app.command(name="evict")
def evict_peer(
    username: str = typer.Argument(..., help="Name of the peer to evict"),
    force: bool = typer.Option(
        False, "--force", "-f", help="Evict peer without prompting"
    ),
):
    """
    Removes a peer entirely.
    """
    check_setup()
    try:
        if not db_host_exists(f"peerstash-{username}"):
            typer.secho(f"Unknown peer", fg=typer.colors.RED, err=True)
            raise typer.Exit(1)

        # verify the action should be taken
        if not force:
            confirm = typer.confirm(
                f"Are you sure you want to evict '{username}'? This will delete their stored backups.",
                default=False,
            )
            if not confirm:
                raise typer.Abort("Aborted peer eviction.")

        # update or insert peer
        registration.delete_peer(username)

        typer.secho(
            f"Deleted data for '{username}' and removed from peers list.",
            fg=typer.colors.BRIGHT_RED,
            bold=True,
        )

    except RuntimeError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    except ValueError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.secho(f"System Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
