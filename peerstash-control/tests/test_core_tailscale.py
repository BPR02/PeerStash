import pytest
import subprocess
from peerstash.core.tailscale import (
    revoke_api_token,
    modify_policy,
    _generate_auth_key,
    register_device,
    _get_local_device_id,
    generate_device_invite,
)


def test_revoke_api_token_success(mocked_tailscale_api):
    token = "tskey-api-12345-SECRET"
    result = revoke_api_token(token)
    assert result is True


def test_revoke_api_token_invalid_format(mocked_tailscale_api):
    token = "invalid-token-format"
    result = revoke_api_token(token)
    assert result is False


def test_modify_policy_success(mocked_tailscale_api):
    token = "tskey-api-12345-SECRET"
    try:
        modify_policy(token)
    except Exception as e:
        pytest.fail(f"modify_policy raised an exception: {e}")


def test_generate_auth_key_success(mocked_tailscale_api):
    token = "tskey-api-12345-SECRET"
    key = _generate_auth_key(token)
    assert key == "tskey-auth-abcDEFghijkl-abcDEFGHIJKLMNOPQRSTUVWXYZ123456"


def test_register_device_success(mocked_tailscale_api, mock_subprocess):
    try:
        register_device("tskey-api-12345-SECRET", "valid_sudo_password")
    except Exception as e:
        pytest.fail(f"register_device failed unexpectedly: {e}")


def test_register_device_wrong_password(mocked_tailscale_api, mock_subprocess):
    with pytest.raises(subprocess.CalledProcessError, match="sudo: incorrect password"):
        register_device("tskey-api-12345-SECRET", "wrong_sudo_pass")


def test_get_local_device_id_failure(mock_subprocess, monkeypatch):
    monkeypatch.setenv("MOCK_TAILSCALE_MISSING_ID", "1")

    with pytest.raises(ValueError, match="Could not find 'ID'. Is the node connected?"):
        _get_local_device_id()


def test_get_local_device_id_success(mock_subprocess):
    device_id = _get_local_device_id()
    assert device_id == "12346"


def test_generate_device_invite_success(mocked_tailscale_api, mock_subprocess):
    token = "tskey-api-12345-SECRET"
    invite_code = generate_device_invite(token)

    assert invite_code == "abcXYZ"
