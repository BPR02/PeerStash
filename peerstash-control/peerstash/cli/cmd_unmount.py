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
from peerstash.core.backup import unmount_task

app = typer.Typer()


@app.command(name="unmount")
def unmount(
    name: str = typer.Argument(..., help="Name of the backup task to unmount."),
):
    """
    Unmounts the repo for a backup task.
    """
    check_setup()
    try:
        unmount_task(name)
        typer.secho(
            f"Repo for task '{name}' unmounted.",
            fg=typer.colors.GREEN,
        )
    except ValueError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.secho(f"System Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
