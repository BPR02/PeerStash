import subprocess
import pytest

# These tests will run *inside* the docker container as specified in docker-compose-test.yml

def test_docker_environment_vars():
    # Verify we are getting the right environment variables injected from Compose
    result = subprocess.run(["env"], capture_output=True, text=True)
    assert "USERNAME=admin" in result.stdout or "USERNAME=" in result.stdout

def test_cli_execution_in_docker():
    # The actual peerstash CLI should be available in the container's path, or we can invoke it via python
    # For now we'll just check if the CLI is importable and runs
    from typer.testing import CliRunner
    from peerstash.cli import app

    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "PeerStash" in result.stdout

# Future tests here will use the mocker fixture to patch the internal peerstash functions
# that call restic / tailscale, allowing us to simulate interactions.
