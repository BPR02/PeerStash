import subprocess

# These tests will run *inside* the docker container as specified in docker-compose-test.yml

def test_docker_environment_vars():
    # Verify we are getting the right environment variables injected from Compose
    result = subprocess.run(["env"], capture_output=True, text=True)
    assert "USERNAME=admin" in result.stdout or "USERNAME=" in result.stdout

def test_cli_execution_in_docker():
    from typer.testing import CliRunner

    from peerstash.cli import app

    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "PeerStash" in result.stdout
