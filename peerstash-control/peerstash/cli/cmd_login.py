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

import requests
import typer

from peerstash.core import tailscale
from peerstash.core.utils import verify_sudo_password

app = typer.Typer()


def _setup_oauth(admin_pass: str, no_policy: bool) -> tuple[str, str]:
    typer.secho("\n[!] OAuth Setup Initialized", fg=typer.colors.YELLOW, bold=True)
    typer.secho("    Make sure you have a tailscale account.", fg=typer.colors.YELLOW)
    typer.secho(
        "    You can create one for free at https://login.tailscale.com/start",
        fg=typer.colors.YELLOW,
    )

    # Step 1: temporary API access token to create tag
    if not no_policy:
        typer.secho(
            "[!] Warning: This setup will remove comments from the Access Controls policy",
            fg=typer.colors.YELLOW,
        )
        typer.secho(
            "    file. Save it now if you've modified it and want to preserve comments.",
            fg=typer.colors.YELLOW,
        )
        typer.secho("\n--- STEP 1: Bootstrap Tailnet Tag ---", fg=typer.colors.CYAN)
        typer.echo(
            "To generate the necessary OAuth scopes, your Tailnet MUST have the \n'tag:peerstash' tag created."
        )

        auto_bootstrap = typer.confirm(
            "Would you like to provide a temporary API token to do this automatically? \nThe key will be revoked after the tag is created (Recommended)",
            default=True,
        )

        if auto_bootstrap:
            typer.echo("1. Go to https://login.tailscale.com/admin/settings/keys")
            typer.echo("2. Click 'Generate access token...'")
            typer.echo("3. Click 'Generate access token'")
            api_token = typer.prompt("Paste API Access Token", hide_input=True)

            try:
                typer.echo("Bootstrapping tailnet policy...")
                tailscale.bootstrap_tag(api_token)
                typer.secho("Tag verified/added successfully.", fg=typer.colors.GREEN)
            except requests.exceptions.HTTPError as api_e:
                typer.secho(
                    f"Failed to bootstrap tag. API Error: {api_e.response.text}",
                    fg=typer.colors.RED,
                    err=True,
                )
                raise typer.Exit(code=1)

            # delete API Token
            typer.echo("Revoking temporary API token...")
            if tailscale.revoke_api_token(api_token):
                typer.secho(
                    "API token successfully revoked on Tailscale.",
                    fg=typer.colors.GREEN,
                )
            else:
                typer.secho(
                    "[!] Could not auto-revoke API token. \nPlease delete the API token manually in the admin console.",
                    fg=typer.colors.YELLOW,
                )
            del api_token
        else:
            typer.secho("\n[Manual Tag Creation]", fg=typer.colors.YELLOW)
            typer.echo("1. Go to https://login.tailscale.com/admin/acls/visual/tags")
            typer.echo(
                "2. Click '+ Create tag', name it 'peerstash', \n   and set the owner to 'autogroup:admin'."
            )
            typer.echo("3. Click 'Save tag'.")
            typer.confirm("Have you completed this step?", default=True)

    # Step 2: oauth client for permanent credentials
    typer.secho(
        "\n--- STEP 2: Generate Permanent Credentials ---", fg=typer.colors.CYAN
    )
    typer.echo("1. Go to https://login.tailscale.com/admin/settings/oauth")
    typer.echo("2. Click '+ Credential'")
    typer.echo("3. Select 'OAuth' and click 'Continue ->'")
    typer.echo("4. Select the following scopes:")
    typer.secho("   [x] Policy File (Write)", fg=typer.colors.GREEN)
    typer.secho(
        "   [x] Auth Keys (Write) -> Select 'tag:peerstash' from the dropdown",
        fg=typer.colors.GREEN,
    )
    typer.secho(
        "   [x] Device Invites (Write)",
        fg=typer.colors.GREEN,
    )
    typer.echo("5. Click 'Generate credential'.")

    client_id = typer.prompt("\nPaste OAuth Client ID")
    client_secret = typer.prompt("Paste OAuth Client Secret", hide_input=True)

    tailscale.store_credentials(admin_pass, client_id, client_secret)
    typer.secho("Credentials safely encrypted and stored.", fg=typer.colors.GREEN)

    return (client_id, client_secret)


@app.command(name="login")
def login(
    no_policy: bool = typer.Option(
        False,
        "--no-policy",
        "-p",
        help="Don't modify the policy file. This should only be used if you've ran the login command without this option before and you want to preserve the comments in the file.",
    ),
):
    """
    Initializes and authenticates the node into the distributed mesh.
    """
    typer.secho("--- Tailscale Setup ---", fg=typer.colors.MAGENTA, bold=True)
    admin_pass = typer.prompt(
        "Enter admin password (the one used to login with SSH)", hide_input=True
    )

    try:
        verify_sudo_password(admin_pass)
    except ValueError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    try:
        client_id, client_secret = tailscale.get_credentials(admin_pass)
        if typer.confirm(
            "You are already logged in. Would you like to update your credentials?",
            default=None
        ):
            client_id, client_secret = _setup_oauth(admin_pass, no_policy)
            typer.echo("Using existing credentials")
    except ValueError as e:
        if "No credentials found" in str(e):
            client_id, client_secret = _setup_oauth(admin_pass, no_policy)
        else:
            typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)

    try:
        typer.secho(
            "\n--- Applying Network Configuration ---", fg=typer.colors.CYAN, bold=True
        )

        typer.echo("Fetching OAuth token...")
        token = tailscale.get_oauth_token(client_id, client_secret)

        if not no_policy:
            typer.echo("Updating policy grants...")
            tailscale.modify_policy(token)

        typer.echo("Registering device...")
        tailscale.register_device(token, admin_pass)

        typer.secho(
            "Success",
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
