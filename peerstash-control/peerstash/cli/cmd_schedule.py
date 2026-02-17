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

from typing import Annotated, Optional

import typer

from peerstash.core.backup import schedule_backup

app = typer.Typer()


@app.command(name="schedule")
def schedule(
    peer: str = typer.Argument(..., help="Peer to send the backup to."),
    name: Optional[str] = typer.Option(None, help="Name of the backup task."),
    include: Annotated[
        list[str],
        typer.Option(
            help="A file or directory to include in the backup. Use this option multiple times to specify multiple files or directories."
        ),
    ] = ["."],
    schedule: str = typer.Option(
        "0 3 * * *", help="A cron expression to schedule backups."
    ),
    retention: int = typer.Option(
        8, help="Number of backup snapshots to keep after pruning."
    ),
    prune_schedule: str = typer.Option(
        "0 4 * * 0", help="A cron expression to schedule pruning."
    ),
    exclude: Annotated[
        list[str] | None,
        typer.Option(
            help="An exclusion regex pattern to ignore in the backup. Use this option multiple times to set multiple exclusion patterns."
        ),
    ] = None,
):
    """
    Schedules a new backup task.
    """
    try:
        if not include:
            raise typer.Abort(
                "At least one file or directory must be included. Use --include <directory or file name>"
            )
        task_name = schedule_backup(
            include, peer, retention, schedule, prune_schedule, exclude, name
        )
        typer.secho(
            f"Backup task '{task_name}' created.",
            fg=typer.colors.GREEN,
        )
    except ValueError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.secho(f"System Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
