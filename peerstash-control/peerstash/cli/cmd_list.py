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

import re

import typer

from peerstash.core.db import db_list_tasks

app = typer.Typer()


@app.command(name="list")
def list(
    name: str = typer.Argument(
        None, help="Name of the task(s) to list. Supports regex."
    ),
    long: bool = typer.Option(False, "--long", "-l", help="List attributes"),
    all: bool = typer.Option(False, "--all", "-a", help="Show all attributes"),
    human_readable: bool = typer.Option(
        False, "--human_readable", "-h", help="List attributes"
    ),
):
    """
    Lists scheduled backup tasks.
    """
    try:
        # update or insert peer
        tasks = db_list_tasks()
    except Exception as e:
        typer.secho(f"System Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    if name:
        tasks = [t for t in tasks if re.match(name, t.name)]

    for task in tasks:
        if not long:
            typer.secho(
                f"{task.name}",
                fg=(
                    typer.colors.WHITE if task.is_locked else typer.colors.BRIGHT_WHITE
                ),
            )
            continue

        if not human_readable:
            parsed: str = ""
            parsed += "[X]" if task.is_locked else ""
            parsed += task.name
            parsed += f" | {task.hostname.removeprefix('peerstash-')}"
            parsed += f' "{task.schedule}"'
            parsed += f" +[{task.include}]"
            parsed += f" -[{task.exclude}]"
            parsed += f' "{task.prune_schedule}"'
            parsed += f" {task.retention}"
            if all:
                parsed += f" {task.last_run} ({task.last_exit_code})"
                parsed += f" [{task.last_snapshot_id}]"
            typer.secho(
                f"{parsed}",
                fg=(
                    typer.colors.WHITE if task.is_locked else typer.colors.BRIGHT_WHITE
                ),
            )
            continue

        typer.secho(
            f'{task.name}{" [LOCKED]" if all and task.is_locked else ""}',
            fg=(typer.colors.WHITE if task.is_locked else typer.colors.BRIGHT_WHITE),
        )
        typer.secho(
            f'    peer=       {task.hostname.removeprefix("peerstash-")}',
            fg=typer.colors.BRIGHT_WHITE,
        )
        typer.secho(f"    schedule=   {task.schedule}", fg=typer.colors.CYAN)
        typer.secho(f"    includes=   {task.include}", fg=typer.colors.BRIGHT_GREEN)
        typer.secho(f"    exclusions= {task.exclude}", fg=typer.colors.BRIGHT_RED)
        typer.secho(f"    prune=      {task.prune_schedule}", fg=typer.colors.YELLOW)
        typer.secho(f"    retention=  {task.retention}", fg=typer.colors.BRIGHT_YELLOW)
        if all:
            typer.secho(
                f"    last run=   {task.last_run} ({task.last_exit_code})",
                fg=(
                    typer.colors.GREEN if task.last_exit_code == 0 else typer.colors.RED
                ),
            )
            typer.secho(
                f"    last id=    {task.last_snapshot_id}",
                fg=typer.colors.MAGENTA,
            )
