import os
import pytest
from typer.testing import CliRunner

# We can import our app and tests using the typer runner
# from peerstash.cli import app

@pytest.fixture(autouse=True)
def mock_db_path(monkeypatch, tmp_path):
    # Use a temporary file for the sqlite DB
    db_file = tmp_path / "peerstash_test.db"
    monkeypatch.setenv("PEERSTASH_DB_PATH", str(db_file))
    return db_file

@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture
def mock_tailscale(mocker):
    # Mock requests for Tailscale API
    mocker.patch("requests.post")
    mocker.patch("requests.get")
    mocker.patch("requests.delete")
    # Alternatively mock the tailscale methods directly if preferred
    mocker.patch("peerstash.core.tailscale.modify_policy")
    mocker.patch("peerstash.core.tailscale.register_device")
    mocker.patch("peerstash.core.tailscale.generate_device_invite", return_value="test-invite-code")
    mocker.patch("peerstash.core.tailscale.revoke_api_token", return_value=True)

@pytest.fixture
def mock_restic(mocker):
    # Mocking SFTP calls via Restic
    mocker.patch("restic.repository")
    mocker.patch("restic.password_file")
    mocker.patch("restic.init")
    mocker.patch("restic.backup", return_value={"data_added": 1024})
    mocker.patch("restic.check", return_value=True)
    mocker.patch("restic.forget")
    mocker.patch("restic.restore")
    mocker.patch("subprocess.Popen")
    mocker.patch("subprocess.run")

