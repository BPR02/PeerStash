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

import subprocess
import sys

import requests
import typer

from peerstash.core import tailscale
from peerstash.core.utils import verify_sudo_password
from peerstash.core.db import db_get_invite_code, db_get_user, db_set_invite_code

app = typer.Typer()


USER = db_get_user()


def _get_sudo_password() -> str:
    """
    Reads the OS sudo password from stdin if piped,
    otherwise falls back to an interactive hidden prompt.
    """
    if not sys.stdin.isatty():
        # Read the piped input and strip any trailing newlines
        return sys.stdin.read().strip()

    # Fall back to the standard interactive hidden prompt
    return typer.prompt(f"[peerstash] enter password for {USER}", hide_input=True)


@app.command(name="login")
def setup(
    token: str = typer.Option(
        ...,
        help="API Access Token to use. Skips interactive instructions.",
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        "-o",
        help="Rerun the setup. This should only be used if you accidentally messed something up in your tailscale settings.",
    ),
):
    """
    Initializes and authenticates the node.
    """
    if not overwrite and db_get_invite_code():
        typer.secho("[!] This node is already configured.", fg=typer.colors.YELLOW)
        typer.echo(
            "Run 'peerstash id' to see your invite code or 'peerstash register' to connect a peer."
        )
        raise typer.Exit()

    typer.secho("--- Tailscale Setup ---", fg=typer.colors.MAGENTA, bold=True)
    admin_pass = _get_sudo_password()

    try:
        verify_sudo_password(admin_pass)
    except ValueError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    if not token:
        typer.secho("OAuth Setup Initialized", fg=typer.colors.CYAN, bold=True)
        typer.secho("    Make sure you have a tailscale account.", fg=typer.colors.CYAN)
        typer.secho(
            "    You can create one for free at https://login.tailscale.com/start",
            fg=typer.colors.CYAN,
        )

        typer.secho(
            "\n[!] Warning: This setup will remove comments from the Access Controls policy",
            fg=typer.colors.YELLOW,
        )
        typer.secho(
            "    file. Save it now if you've modified it and want to preserve comments.",
            fg=typer.colors.YELLOW,
        )

        typer.echo("1. Go to https://login.tailscale.com/admin/settings/keys")
        typer.echo("2. Click 'Generate access token...'")
        typer.echo("3. Click 'Generate access token'")
        api_token = typer.prompt("Paste API Access Token", hide_input=True)
    else:
        api_token = token

    try:
        typer.secho(
            "\n--- Applying Network Configuration ---", fg=typer.colors.CYAN, bold=True
        )

        typer.echo("Setting up access control policies...")
        tailscale.modify_policy(api_token)

        typer.echo("Registering device...")
        tailscale.register_device(token, admin_pass)

        typer.echo("Generating invite code...")
        invite_code = tailscale.generate_device_invite(api_token)
        if not invite_code:
            raise Exception("Failed to generate invite code.")
        db_set_invite_code(invite_code)

        typer.echo("Revoking API access token...")
        if not tailscale.revoke_api_token(api_token):
            typer.secho(
                "[!] API Token could not be automatically revoked.",
                fg=typer.colors.YELLOW,
            )
            typer.secho(
                "    You can manually revoke it in your tailscale settings.",
                fg=typer.colors.YELLOW,
            )

        typer.secho(
            "Success! Use 'peerstash id' to view your share code.",
            fg=typer.colors.GREEN,
            bold=True,
        )

    except requests.exceptions.HTTPError as e:
        typer.secho(f"\nAPI Error: {e.response.text}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    except subprocess.CalledProcessError as e:
        typer.secho(
            f"\nFailed to run tailscale command: {e.stderr.decode() if e.stderr else str(e)}",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)
    except Exception as e:
        typer.secho(
            f"\nAn unexpected error occurred: {e}", fg=typer.colors.RED, err=True
        )
        raise typer.Exit(code=1)
