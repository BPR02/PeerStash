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

import typer

from peerstash.cli.utils import check_setup
from peerstash.core.db import db_list_hosts

app = typer.Typer()


@app.command(name="peers")
def peers():
    """
    Lists known peers.
    """
    check_setup()
    try:
        # get hosts list
        hosts = db_list_hosts()
    except Exception as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    for host in hosts:
        typer.echo(host.hostname.removeprefix("peerstash-"))
