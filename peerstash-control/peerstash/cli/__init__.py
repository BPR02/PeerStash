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

from peerstash.cli import (
    cmd_backup,
    cmd_cancel,
    cmd_id,
    cmd_list,
    cmd_prune,
    cmd_register,
    cmd_schedule,
)

# Create the main cli app
cli = typer.Typer(help="PeerStash CLI Tool")
cli.command(name="id")(cmd_id.print_id)
cli.command(name="register")(cmd_register.register_peer)
cli.command(name="schedule")(cmd_schedule.schedule)
cli.command(name="backup")(cmd_backup.backup)
cli.command(name="prune")(cmd_prune.prune)
cli.command(name="cancel")(cmd_cancel.cancel)
cli.command(name="list")(cmd_list.list)
