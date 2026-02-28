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
from peerstash.core.db import db_get_user, db_list_hosts
from peerstash.core.utils import get_disk_usage, sizeof_fmt

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

    user = db_get_user()
    if not user:
        typer.secho(f"Error: unknown user.", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    for host in hosts:
        total, used, _ = get_disk_usage(user, host.hostname, 2022)
        typer.echo(f"{host.hostname.removeprefix("peerstash-")} ({sizeof_fmt(used)} used / {sizeof_fmt(total)})")
