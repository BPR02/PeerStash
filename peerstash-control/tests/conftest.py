import logging
import os
from pathlib import Path

import pytest
from pytest import MonkeyPatch
from pytest_mock import MockerFixture
from typer.testing import CliRunner


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


pytest_plugins = [
    "tests.mocks.tailscale_mock",
    "tests.mocks.sftpgo_mock",
    "tests.mocks.restic_mock",
    "tests.mocks.subprocess_mock",
    "tests.mocks.db_mock",
]

# prevent logging from running in unit tests
logging.FileHandler = logging.NullHandler  # type: ignore
_original_makedirs = os.makedirs
def _mock_makedirs(name, mode=0o777, exist_ok=False):
    if str(name).startswith("/var/log/peerstash"):
        return
    _original_makedirs(name, mode, exist_ok)
os.makedirs = _mock_makedirs


@pytest.fixture(autouse=True)
def mock_setup(mocker: MockerFixture) -> None:
    # List of all CLI command modules
    cli_commands = [
        "backup",
        "cancel",
        "evict",
        "id",
        "list",
        "mount",
        "peers",
        "prune",
        "register",
        "restore",
        "schedule",
        "setup",
        "snapshots",
        "unmount",
    ]

    # Patch check_setup wherever it was imported
    for cmd in cli_commands:
        mocker.patch(
            f"peerstash.cli.cmd_{cmd}.check_setup", return_value=True, create=True
        )


@pytest.fixture
def mock_daemon_and_locks(mocker: MockerFixture):
    # Helper to patch functions that are imported directly via "from module import func"
    def multi_patch(func_name, target_modules, **kwargs):
        for mod in target_modules:
            mocker.patch(f"{mod}.{func_name}", create=True, **kwargs)

    # don't run daemon calls
    multi_patch(
        "send_to_daemon",
        [
            "peerstash.core.utils",
            "peerstash.core.backup",
            "peerstash.core.registration",
        ],
    )

    # don't run lock calls
    multi_patch(
        "acquire_task_lock",
        ["peerstash.core.utils", "peerstash.core.backup"],
        return_value="mock_lock",
    )
    multi_patch("release_lock", ["peerstash.core.utils", "peerstash.core.backup"])

    # mock destructive filesystem/network calls
    mocker.patch("peerstash.core.backup._sftp_recursive_remove")
    mocker.patch("peerstash.core.backup.shutil.rmtree")
    mocker.patch("peerstash.core.backup.shutil.move")
    mocker.patch("os.makedirs", return_value=True)
    mocker.patch("os.mkdir")
    mocker.patch("os.rmdir")
