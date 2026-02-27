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

from datetime import datetime

import typer

from peerstash.cli.utils import check_setup
from peerstash.core.backup import get_snapshots

app = typer.Typer()


@app.command(name="snapshots")
def snapshots(
    name: str = typer.Argument(
        ..., help="Name of the backup task to get snapshots from."
    ),
    snapshot: str = typer.Argument(None, help="Snapshot ID to get info from."),
    json: bool = typer.Option(False, "--json", "-j", help="Format in JSON"),
):
    """
    Lists the snapshots taken for a task.
    """
    check_setup()
    try:
        snapshot_list = get_snapshots(name, snapshot)
    except Exception as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    final_list: list[dict[str, str | list[str]]] = []

    for s in snapshot_list:
        date = datetime.fromisoformat(s["time"].replace(" ", ""))
        if json:
            final_list.append(
                {
                    "short_id": s["short_id"],
                    "id": s["id"],
                    "date": f"{date}",
                    "includes": s["paths"],
                }
            )
        else:
            typer.secho(s["id"], fg=typer.colors.BRIGHT_WHITE)
            typer.secho(
                f"    Short ID: {s['short_id']}", fg=typer.colors.BRIGHT_MAGENTA
            )
            typer.secho(
                f"    Date:     {date.strftime("%d %B %Y %I:%M:%S %p %Z")}",
                fg=typer.colors.CYAN,
            )
            typer.secho(f"    Includes: ", fg=typer.colors.BRIGHT_GREEN)
            for p in s["paths"]:
                typer.secho(f"      - {p}", fg=typer.colors.GREEN)

    if json:
        typer.echo(f"{final_list}")
