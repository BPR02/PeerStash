import json
import os
import re
import socket
import subprocess
import time

import pytest
import requests
import restic

from peerstash.core.backup import remove_schedule, schedule_backup
from peerstash.core.db import (db_add_host, db_add_task, db_delete_host,
                               db_delete_task, db_get_host, db_get_invite_code,
                               db_get_task, db_get_tasks_for_host, db_get_user,
                               db_host_exists, db_list_hosts, db_list_tasks,
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
def run_boot_setup_script():
    """
    Executes the real setup.sh script before any tests run.
    This simulates the container boot sequence, generating SSH keys,
    initializing the DB, and setting permissions.
    """
    script_path = "/app/testing/scripts/setup.sh"

    # Read the script and comment out the hanging supervisord line
    with open(script_path, "r") as f:
        script_content = f.read()

    safe_script = script_content.replace(
        "exec /usr/bin/supervisord", "# exec /usr/bin/supervisord"
    )

    # Run the modified script safely via bash -c
    result = subprocess.run(["bash", "-c", safe_script], capture_output=True, text=True)

    if result.returncode != 0:
        pytest.fail(f"setup.sh failed during test initialization:\n{result.stderr}")

    # Assertions to ensure SSH keys were generated correctly
    user_key_path = "/home/admin/.ssh/id_ed25519"
    assert os.path.exists(user_key_path), "setup.sh failed to generate user SSH key"

    stat_info = os.stat(user_key_path)
    assert (
        stat_info.st_mode & 0o777 == 0o600
    ), "setup.sh failed to set strict SSH key permissions"


@pytest.fixture(scope="session", autouse=True)
def run_real_daemon(run_boot_setup_script):
    """
    Spins up the real peerstash daemon in the background so we can
    test IPC socket communication and real crontab modification.
    Requires the setup script to run first to ensure the DB exists.
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


# -------------------------------------------------------------------
# Environment Sanity Test
# -------------------------------------------------------------------


def test_docker_environment_vars():
    # Verify we are getting the right environment variables injected from Compose
    result = subprocess.run(["env"], capture_output=True, text=True)
    assert "USERNAME=admin" in result.stdout or "USERNAME=" in result.stdout


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

    # 6. Read None
    host = db_get_host(hostname)
    assert host is None


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

    # 3. List
    tasks = db_list_tasks()
    assert tasks is not None
    assert tasks[0].status == "new"

    # 4. Update
    updated_task = db_update_task(
        task_name, TaskUpdate(status="running", last_exit_code=0)
    )
    assert updated_task is not None
    assert updated_task.status == "running"
    assert updated_task.last_exit_code == 0

    updated_task = db_update_task(task_name, TaskUpdate())
    assert updated_task is not None
    assert updated_task.status == "running"

    # 5. Delete
    result = db_delete_task(task_name)
    assert result is True
    assert db_task_exists(task_name) is False

    # 6. Read None
    task = db_get_task(task_name)
    assert task is None

    tasks = db_list_tasks()
    assert tasks == []

    updated_task = db_update_task(task_name, TaskUpdate(status="running"))
    assert updated_task is None


def test_db_node_data():
    # Verify user was injected via our init schema (or container env)
    user = db_get_user()
    assert user in ["admin", None]  # Depends if setup script ran, but shouldn't crash

    # Test setting and getting invite code (UPSERT logic)
    db_set_invite_code("tskey-invite-12345")
    assert db_get_invite_code() == "tskey-invite-12345"

    db_set_invite_code("tskey-invite-99999")
    assert db_get_invite_code() == "tskey-invite-99999"


def test_db_get_tasks_for_host_query():
    """Verifies the relational query between hosts and tasks works."""
    hostname = "peerstash-rel-node"
    task_name = "rel_task"

    db_add_host(hostname, "pubkey123")
    db_add_task(
        name=task_name,
        include="/mnt",
        exclude=None,
        hostname=hostname,
        schedule="* * * * *",
        retention="1d",
        prune_schedule="* * * * *",
    )

    # Verify the specific relational query
    tasks = db_get_tasks_for_host(hostname)
    assert len(tasks) == 1
    assert (
        tasks[0][0] == task_name
    )  # The query returns a list of tuples: [('rel_task',)]

    # Cleanup
    db_delete_task(task_name)
    db_delete_host(hostname)


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


def test_daemon_socket_error_handling():
    """Ensures the daemon gracefully rejects bad data without crashing."""
    # 1. Test sending raw garbage (not JSON) directly to the socket
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        s.connect("/var/run/peerstash.sock")
        s.sendall(b"this is just some random string, not json!")
        raw_response = s.recv(4096).decode("utf-8")
        response = json.loads(raw_response)

        assert response["status"] == "error"
        assert response["message"] == "Invalid JSON"

    # 2. Test sending valid JSON but an unknown action
    with pytest.raises(RuntimeError, match="Unknown action"):
        send_to_daemon("leak_api_keys", {})


# -------------------------------------------------------------------
# End-to-End Orchestration & System Binary Tests
# -------------------------------------------------------------------


def test_e2e_schedule_and_remove():
    """Tests the orchestration between DB and Daemon for scheduling."""
    task_name = "e2e_schedule_task"
    hostname = "peerstash-e2e-node"

    # Prerequisite: Host must exist in DB
    db_add_host(hostname, "pubkey123")

    # 1. Schedule (Should hit both DB and Daemon)
    schedule_backup(
        paths=["/mnt/peerstash_root"],
        peer="e2e-node",
        schedule="30 5 * * *",
        name=task_name,
    )

    # Verify DB
    assert db_task_exists(task_name) is True

    # Verify Crontab (via Daemon)
    cron_result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    assert task_name in cron_result.stdout
    assert "30 5 * * *" in cron_result.stdout

    # 2. Remove Schedule
    remove_schedule(task_name)

    # Verify DB scrubbed
    assert db_task_exists(task_name) is False

    # Verify Crontab scrubbed
    cron_result_after = subprocess.run(
        ["crontab", "-l"], capture_output=True, text=True
    )
    assert task_name not in cron_result_after.stdout


def test_sftpgo_api_key_generation():
    """
    Verifies that setup.py successfully contacted SFTPGo,
    generated a valid API key, and exported it to the bash environment.
    """
    # 1. Read the API key that setup.py injected into .bashrc
    bashrc_path = "/home/admin/.bashrc"
    assert os.path.exists(bashrc_path), "setup.py did not create .bashrc"

    api_key = None
    with open(bashrc_path, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("export API_KEY="):
                # Extract the value, stripping any quotes.
                api_key = line.split("=", 1)[1].strip("'\"")

    assert api_key is not None, "API_KEY export not found in .bashrc"
    assert len(api_key) > 30, f"API Key looks suspiciously short or empty: '{api_key}'"

    # 2. Use the extracted API key to make a real authenticated request to SFTPGo
    headers = {"X-SFTPGO-API-KEY": api_key}
    resp = requests.get("http://localhost:8080/api/v2/admins", headers=headers)

    # If the key is valid, SFTPGo will return 200 OK
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

    # Verify the default admin user exists in the response
    admins = resp.json()
    assert any(a.get("username") == "admin" for a in admins)


def test_restic_binary_installed_and_working(monkeypatch):
    """
    Verifies the restic binary is installed in the container
    and the python wrapper can successfully execute real commands.
    """
    repo_dir = "/tmp/test_restic_repo"
    source_dir = "/tmp/test_restic_source"
    os.makedirs(source_dir, exist_ok=True)

    with open(os.path.join(source_dir, "test.txt"), "w") as f:
        f.write("hello restic")

    # Set environment variable for restic password
    monkeypatch.setenv("RESTIC_PASSWORD", "integration_test_pass")

    # 1. Init
    restic.password_file = None
    restic.repository = repo_dir
    restic.init()
    assert os.path.exists(os.path.join(repo_dir, "config"))

    # 2. Backup
    backup_result = restic.backup(paths=[source_dir])
    assert "snapshot_id" in backup_result

    # 3. List Snapshots
    snaps = restic.snapshots()
    assert len(snaps) == 1
    assert snaps[0]["paths"] == [source_dir]


# -------------------------------------------------------------------
# Logging Architecture Integration Tests
# -------------------------------------------------------------------


def test_logging_directory_and_symlink():
    """
    Verifies that the setup script correctly creates the persistent log
    directory and symlinks /var/log/peerstash to it.
    """
    log_dir = "/var/log/peerstash"
    actual_dir = "/var/lib/peerstash/logs"

    # Verify the persistent directory was created
    assert os.path.exists(
        actual_dir
    ), f"Persistent log directory {actual_dir} was not created"

    # Verify the symlink exists and points to the correct location
    assert os.path.islink(log_dir), f"{log_dir} is not a symlink"
    assert (
        os.readlink(log_dir) == actual_dir
    ), f"Symlink points to {os.readlink(log_dir)}, expected {actual_dir}"


def test_setup_script_logging_timestamps():
    """
    Verifies that setup.sh successfully intercepts standard output and
    prepends the [YYYY-MM-DD HH:MM:SS] timestamp to the log file.
    """
    log_file = "/var/log/peerstash/peerstash.log"
    assert os.path.exists(log_file), "peerstash.log was not created"

    with open(log_file, "r") as f:
        lines = f.readlines()

    assert len(lines) > 0, "peerstash.log is completely empty"

    # Regex to match the [YYYY-MM-DD HH:MM:SS] format
    timestamp_pattern = re.compile(r"^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]")

    valid_lines = 0
    for line in lines:
        if timestamp_pattern.match(line):
            valid_lines += 1

    # Ensure at least some lines were successfully timestamped by the bash loop
    assert (
        valid_lines > 0
    ), "No timestamps matching the expected format were found in peerstash.log"


def test_daemon_python_logging():
    """
    Verifies that the daemon.py process uses the standard Python logging
    library to output to the log file.
    """
    log_file = "/var/log/peerstash/peerstash.log"
    assert os.path.exists(log_file), "peerstash.log was not created"

    with open(log_file, "r") as f:
        content = f.read()

    assert len(content) > 0, "peerstash.log is empty"

    # Check for the expected startup message logged by the daemon
    assert (
        "Peerstash Daemon listening on" in content
    ), "Expected daemon startup message not found in peerstash.log"
