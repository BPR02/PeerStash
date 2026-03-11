import json
import subprocess

import pytest
from pytest_mock import MockerFixture, MockType


def generate_subprocess_error(
    args: list, returncode: int, stderr: str = ""
) -> subprocess.CalledProcessError:
    """Helper to generate a CalledProcessError for failing commands."""
    return subprocess.CalledProcessError(
        returncode=returncode,
        cmd=args,
        output=b"",
        stderr=stderr.encode() if isinstance(stderr, str) else stderr,
    )


def subprocess_router(args, **kwargs):
    """Routes the intercepted subprocess.run calls to the correct mock response."""

    # restic prune
    if args[:2] == ["/usr/bin/restic", "prune"]:
        # Magic input: trigger failure if a specific env var is set in the test
        import os

        if "corrupted" in os.getenv("RESTIC_REPOSITORY", ""):
            raise generate_subprocess_error(args, 1, "Fatal: repository corrupted")
        return subprocess.CompletedProcess(args, 0, stdout=b"prune successful")

    # fusermount
    if args[:1] == ["fusermount"]:
        return subprocess.CompletedProcess(args, 0, stdout=b"")

    # sudo tailscale up
    if args[:4] == ["sudo", "-S", "tailscale", "up"]:
        auth_key = args[5]  # The authkey is at index 5
        password_input = kwargs.get("input", b"")

        # Simulate wrong sudo password
        if password_input == b"wrong_sudo_pass\n":
            raise generate_subprocess_error(args, 1, "sudo: incorrect password")

        # Simulate invalid auth key
        if auth_key == "invalid_key":
            raise generate_subprocess_error(
                args, 1, "tailscale up failed: invalid authkey"
            )

        return subprocess.CompletedProcess(args, 0, stdout=b"Success")

    # tailscale status --json
    if args[:3] == ["tailscale", "status", "--json"]:
        # Magic input to simulate Tailscale daemon being down
        import os

        if os.getenv("MOCK_TAILSCALE_DOWN") == "1":
            raise generate_subprocess_error(
                args, 1, "failed to connect to local tailscaled"
            )

        # Magic input to simulate a connected node that is missing an ID
        if os.getenv("MOCK_TAILSCALE_MISSING_ID") == "1":
            mock_status = {
                "TailscaleIPs": ["100.100.100.100"],
                "BackendState": "Running",
            }
            return subprocess.CompletedProcess(args, 0, stdout=json.dumps(mock_status))

        # Default: Return a valid JSON string with a Self.ID
        mock_status = {
            "TailscaleIPs": ["100.100.100.100"],
            "BackendState": "Running",
            "Self": {"ID": "12346"},
        }
        return subprocess.CompletedProcess(args, 0, stdout=json.dumps(mock_status))

    # sftp (checking disk space)
    if args[:1] == ["sftp"]:
        connection_string = args[3]  # e.g., "user@hostname"

        # Simulate connection failure to a bad host
        if "bad_host" in connection_string:
            raise generate_subprocess_error(
                args, 255, "ssh: Could not resolve hostname"
            )

        # Simulated 'df' output for SFTP
        # text=True is passed in the application, so stdout should be a string
        import os

        if os.getenv("MOCK_DISK_FULL") == "1":
            # Magic input: trigger full disk output via environment variable
            mock_df_output = """
            Size     Used    Avail   (root)    %Capacity
            1000000  998976  1024    1024      99%
            """
        else:
            # Default output simulating ~50GB free space
            mock_df_output = """
            Size     Used    Avail   (root)    %Capacity
            1000000  500000  500000  500000    50%
            """

        return subprocess.CompletedProcess(args, 0, stdout=mock_df_output)

    # sudo -k (invalidate credentials)
    if args[:2] == ["sudo", "-k"]:
        return subprocess.CompletedProcess(args, 0, stdout=b"")

    # sudo -S -v (validate password)
    if args[:3] == ["sudo", "-S", "-v"]:
        password_input = kwargs.get("input", b"")
        if password_input == b"wrong_sudo_pass\n":
            raise generate_subprocess_error(args, 1, "sudo: incorrect password")
        return subprocess.CompletedProcess(args, 0, stdout=b"")

    # crontab -l (list cron jobs)
    if args[:2] == ["crontab", "-l"]:
        # Return the specific cron list as a string (text=True)
        # dummy crontab for task abcd
        cron_content = (
            '0 3 * * * /usr/local/bin/peerstash backup abcd 10 >> CRON_LOG = "/var/log/peerstash-cron.log" 2>&1\n'
            '0 4 * * 0 /usr/local/bin/peerstash prune abcd 10 >> CRON_LOG = "/var/log/peerstash-cron.log" 2>&1\n'
        )
        return subprocess.CompletedProcess(args, 0, stdout=cron_content)

    # crontab - (write cron jobs)
    if args[:2] == ["crontab", "-"]:
        # The new cron content is passed via the 'input' kwarg
        # Automatically passes in standard conditions
        return subprocess.CompletedProcess(args, 0, stdout="")

    # Fallback for unhandled subprocess calls
    raise ValueError(f"Unhandled subprocess command in mock: {args}")


@pytest.fixture
def mock_subprocess(mocker: MockerFixture):
    """Globally patches subprocess.run with our router."""
    mocker.patch("subprocess.run", side_effect=subprocess_router)

@pytest.fixture
def mock_popen(mocker: MockerFixture) -> MockType:
    """Patches Popen globally and returns the mock object for type-safe assertions."""
    return mocker.patch("subprocess.Popen")
