from typer.testing import CliRunner

from peerstash.cli import app


def test_app_help(runner: CliRunner):
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "PeerStash" in result.stdout
