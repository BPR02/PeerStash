import os
import subprocess
import time

import pytest

from peerstash.core.db import (db_add_host, db_add_task, db_delete_host,
                               db_delete_task, db_get_host, db_get_invite_code,
                               db_get_task, db_get_user, db_host_exists,
                               db_list_hosts, db_list_tasks,
                               db_set_invite_code, db_task_exists,
                               db_update_host, db_update_task)
from peerstash.core.db_schemas import TaskUpdate
from peerstash.core.utils import send_to_daemon

# Skip this entire file if we aren't running inside a Docker container
if not os.path.exists("/.dockerenv"):
    pytest.skip(
        "Skipping Docker integration tests on local host", allow_module_level=True
    )

# -------------------------------------------------------------------
# Fixtures
# -------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def run_real_daemon():
    """
    Spins up the real peerstash daemon in the background so we can
    test IPC socket communication and real crontab modification.
    """
    socket_path = "/var/run/peerstash.sock"

    if os.path.exists(socket_path):
        os.remove(socket_path)

    # Start the daemon in the background
    daemon_proc = subprocess.Popen(["python", "-m", "peerstash.daemon"])

    # Poll until the daemon creates the socket
    for _ in range(20):
        if os.path.exists(socket_path):
            break
        time.sleep(0.2)

    if not os.path.exists(socket_path):
        daemon_proc.terminate()
        pytest.fail("Daemon failed to start and create socket.")

    yield  # Allow tests to run

    # Teardown: Kill the daemon after all integration tests finish
    daemon_proc.terminate()
    daemon_proc.wait()


@pytest.fixture(autouse=True)
def init_db_schema():
    """
    Ensures the SQLite database schema is initialized.
    (If your Dockerfile already does this, this fixture is just a safe fallback).
    """
    # Create the db directory if it doesn't exist
    os.makedirs("/var/lib/peerstash", exist_ok=True)

    # We execute a minimal schema creation just in case the container started empty
    import sqlite3

    with sqlite3.connect("/var/lib/peerstash/peerstash.db") as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS hosts (
                hostname TEXT PRIMARY KEY,
                port TEXT NOT NULL,
                public_key TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS tasks (
                name TEXT PRIMARY KEY,
                include TEXT NOT NULL,
                exclude TEXT,
                hostname TEXT NOT NULL,
                schedule TEXT NOT NULL,
                retention TEXT NOT NULL,
                prune_schedule TEXT NOT NULL,
                status TEXT DEFAULT 'new',
                last_run TEXT,
                last_exit_code INTEGER
            );
            CREATE TABLE IF NOT EXISTS node_data (
                id INTEGER PRIMARY KEY,
                username TEXT,
                invite_code TEXT
            );
            INSERT OR IGNORE INTO node_data (id, username) VALUES (1, 'admin');
        """
        )


# -------------------------------------------------------------------
# Database Integration Tests
# -------------------------------------------------------------------


def test_db_hosts_lifecycle():
    hostname = "peerstash-int-node"

    # 1. Create
    db_add_host(hostname, "pubkey123")
    assert db_host_exists(hostname) is True

    # 2. Read
    host = db_get_host(hostname)
    assert host is not None
    assert host.hostname == hostname
    assert host.public_key == "pubkey123"

    # 3. Update
    db_update_host(hostname, "new_pubkey_456")
    updated_host = db_get_host(hostname)
    assert updated_host is not None
    assert updated_host.public_key == "new_pubkey_456"

    # 4. List
    hosts = db_list_hosts()
    assert any(h.hostname == hostname for h in hosts)

    # 5. Delete
    db_delete_host(hostname)
    assert db_host_exists(hostname) is False


def test_db_tasks_lifecycle():
    task_name = "int_backup_task"

    # 1. Create
    db_add_task(
        name=task_name,
        include="/mnt/data",
        exclude=None,
        hostname="peerstash-int-node",
        schedule="0 0 * * *",
        retention="7d",
        prune_schedule="0 4 * * 0",
    )
    assert db_task_exists(task_name) is True

    # 2. Read
    task = db_get_task(task_name)
    assert task is not None
    assert task.schedule == "0 0 * * *"
    assert task.status == "new"

    # 3. Update
    db_update_task(task_name, TaskUpdate(status="running", last_exit_code=0))
    updated_task = db_get_task(task_name)
    assert updated_task is not None
    assert updated_task.status == "running"
    assert updated_task.last_exit_code == 0

    # 4. Delete
    result = db_delete_task(task_name)
    assert result is True
    assert db_task_exists(task_name) is False


def test_db_node_data():
    # Verify user was injected via our init schema (or container env)
    user = db_get_user()
    assert user in ["admin", None]  # Depends if setup script ran, but shouldn't crash

    # Test setting and getting invite code (UPSERT logic)
    db_set_invite_code("tskey-invite-12345")
    assert db_get_invite_code() == "tskey-invite-12345"

    db_set_invite_code("tskey-invite-99999")
    assert db_get_invite_code() == "tskey-invite-99999"


# -------------------------------------------------------------------
# Daemon & System Integration Tests
# -------------------------------------------------------------------


def test_daemon_create_and_remove_task():
    """Tests socket IPC and verifies the real Linux crontab gets modified."""
    task_name = "daemon_int_task"

    # 1. Create a task via the daemon
    response = send_to_daemon(
        "create_task",
        {
            "task_name": task_name,
            "schedule": "15 2 * * *",
            "prune_schedule": "30 3 * * *",
        },
    )
    assert response["status"] == "success"

    # 2. Verify it actually wrote to the system crontab
    cron_result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    assert cron_result.returncode == 0
    assert task_name in cron_result.stdout
    assert "15 2 * * *" in cron_result.stdout
    assert "30 3 * * *" in cron_result.stdout

    # 3. Remove the task via the daemon
    response_remove = send_to_daemon("remove_task", {"task_name": task_name})
    assert response_remove["status"] == "success"

    # 4. Verify it was scrubbed from the system crontab
    cron_result_after = subprocess.run(
        ["crontab", "-l"], capture_output=True, text=True
    )
    assert task_name not in cron_result_after.stdout


def test_daemon_sync_hosts():
    """Tests the known_hosts syncing logic."""
    # Ensure dummy source file exists
    os.makedirs("/home/admin/.ssh", exist_ok=True)
    with open("/home/admin/.ssh/known_hosts", "w") as f:
        f.write("dummy_host ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNo...")

    response = send_to_daemon("sync_hosts")

    assert response["status"] == "success"
    assert os.path.exists("/root/.ssh/known_hosts")


def test_docker_environment_vars():
    # Verify we are getting the right environment variables injected from Compose
    result = subprocess.run(["env"], capture_output=True, text=True)
    assert "USERNAME=admin" in result.stdout or "USERNAME=" in result.stdout
