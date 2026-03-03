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

import json
import os
import shutil
import socketserver
from typing import Any, Optional

from peerstash.core.db import db_get_user
from peerstash.core.utils import (update_crontab, validate_schedule,
                                  validate_task_name)

SOCKET_PATH = "/var/run/peerstash.sock"
CRON_LOG = "/var/log/peerstash-cron.log"
PEERSTASH_BIN = "/usr/local/bin/peerstash"
USER = db_get_user()


class PeerstashDaemonHandler(socketserver.BaseRequestHandler):
    def handle(self):
        try:
            data = self.request.recv(4096).decode("utf-8").strip()
            if not data:
                return

            payload: dict[str, Any] = json.loads(data)
            action = payload.get("action", "")
            kwargs = payload.get("kwargs", {})

            response = self.route_action(action, kwargs)
            self.request.sendall(json.dumps(response).encode("utf-8"))

        except json.JSONDecodeError:
            self.request.sendall(
                json.dumps({"status": "error", "message": "Invalid JSON"}).encode(
                    "utf-8"
                )
            )
        except Exception as e:
            self.request.sendall(
                json.dumps({"status": "error", "message": str(e)}).encode("utf-8")
            )

    def route_action(self, action: str, kwargs: dict[str, str] = {}) -> dict[str, str]:
        if action == "create_task":
            return self.create_task(**kwargs)
        elif action == "remove_task":
            return self.remove_task(**kwargs)
        elif action == "sync_hosts":
            return self.sync_hosts()
        else:
            return {"status": "error", "message": "Unknown action"}

    def create_task(
        self, task_name: str, schedule: str, prune_schedule: str
    ) -> dict[str, str]:
        if name_error := validate_task_name(task_name):
            return {"status": "error", "message": f"Invalid task name ({name_error})."}
        if not validate_schedule(schedule) or not validate_schedule(prune_schedule):
            return {"status": "error", "message": "Invalid schedule format."}

        backup_job = (
            f"{schedule} {PEERSTASH_BIN} backup {task_name} 10 >> {CRON_LOG} 2>&1"
        )
        prune_job = (
            f"{prune_schedule} {PEERSTASH_BIN} prune {task_name} 10 >> {CRON_LOG} 2>&1"
        )

        success, msg = update_crontab(task_name, [backup_job, prune_job])
        return {"status": "success" if success else "error", "message": msg}

    def remove_task(self, task_name: str) -> dict[str, str]:
        if name_error := validate_task_name(task_name):
            return {"status": "error", "message": f"Invalid task name ({name_error})."}

        success, msg = update_crontab(task_name)
        return {"status": "success" if success else "error", "message": msg}

    def sync_hosts(self) -> dict[str, str]:
        if not USER:
            raise ValueError("Unknown USER")
        source_file = os.path.join("/home", USER, ".ssh", "known_hosts")
        dest_file = "/root/.ssh/known_hosts"

        if not os.path.exists(source_file):
            return {"status": "error", "message": "Source known_hosts does not exist."}

        try:
            shutil.copy2(source_file, dest_file)
            os.chown(dest_file, 0, 0)
            return {"status": "success", "message": "Hosts synced successfully."}
        except Exception as e:
            return {"status": "error", "message": str(e)}


def main():
    """Entry point for the daemon."""
    # clean up stale socket file
    if os.path.exists(SOCKET_PATH):
        os.remove(SOCKET_PATH)

    # create new socket
    with socketserver.UnixStreamServer(SOCKET_PATH, PeerstashDaemonHandler) as server:
        # open socket to users
        os.chmod(SOCKET_PATH, 0o666)
        print("Peerstash Daemon listening on", SOCKET_PATH)
        server.serve_forever()


if __name__ == "__main__":
    main()
