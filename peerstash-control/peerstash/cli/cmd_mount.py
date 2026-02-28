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
from peerstash.core.backup import mount_task

app = typer.Typer()


@app.command(name="mount")
def mount(
    name: str = typer.Argument(..., help="Name of the backup task to mount."),
):
    """
    Mounts the repo for a backup task. Uncomment "user_allow_other" on your host /etc/fuse.conf file to view the FUSE mount on your host machine.
    """
    check_setup()
    try:
        mount_task(name)
        typer.secho(
            f"Repo for task '{name}' mounted in mounts folder.",
            fg=typer.colors.GREEN,
        )
        typer.secho(
            f"Use 'peerstash unmount {name}' to unmount the repo.",
            fg=typer.colors.YELLOW,
        )
    except ValueError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.secho(f"System Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
