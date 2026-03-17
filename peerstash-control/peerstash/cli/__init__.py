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

__version__ = "0.10.0"

from typing import Annotated

import typer

from peerstash.cli import (cmd_backup, cmd_cancel, cmd_evict, cmd_id, cmd_list,
                           cmd_mount, cmd_peers, cmd_prune, cmd_register,
                           cmd_restore, cmd_schedule, cmd_setup, cmd_snapshots,
                           cmd_unmount)


def version_callback(value: bool):
    if value:
        print(f"PeerStash {__version__}")
        raise typer.Exit()


# Create the main cli app
app = typer.Typer(help="PeerStash CLI Tool")


@app.command()
def cli(
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            callback=version_callback,
            is_eager=True,
            help="Show the version and exit.",
        ),
    ] = None,
):
    print("Use 'peerstash --help' for available commands")


# create subcommands for the main cli app
app.command(name="setup")(cmd_setup.setup)
app.command(name="id")(cmd_id.print_id)
app.command(name="register")(cmd_register.register_peer)
app.command(name="evict")(cmd_evict.evict_peer)
app.command(name="schedule")(cmd_schedule.schedule)
app.command(name="cancel")(cmd_cancel.cancel)
app.command(name="restore")(cmd_restore.restore)
app.command(name="backup")(cmd_backup.backup)
app.command(name="prune")(cmd_prune.prune)
app.command(name="list")(cmd_list.list)
app.command(name="snapshots")(cmd_snapshots.snapshots)
app.command(name="peers")(cmd_peers.peers)
app.command(name="mount")(cmd_mount.mount)
app.command(name="unmount")(cmd_unmount.unmount)


def main():
    app()
