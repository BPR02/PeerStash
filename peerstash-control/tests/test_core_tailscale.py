import subprocess

import pytest
import requests

from peerstash.core.tailscale import (_generate_auth_key, _get_local_device_id,
                                      generate_device_invite, modify_policy,
                                      register_device, revoke_api_token)


def test_revoke_api_token_success(mocked_tailscale_api):
    token = "tskey-api-12345-SECRET"
    result = revoke_api_token(token)
    assert result is True


def test_revoke_api_token_invalid_format(mocked_tailscale_api):
    token = "invalid-token-format"
    result = revoke_api_token(token)
    assert result is False


def test_revoke_api_token_network_error(mocker):
    mocker.patch(
        "requests.delete",
        side_effect=requests.exceptions.ConnectionError("Network down"),
    )
    result = revoke_api_token("tskey-api-12345-SECRET")
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


def test_get_local_device_id_daemon_down(mock_subprocess, monkeypatch):
    monkeypatch.setenv("MOCK_TAILSCALE_DOWN", "1")
    with pytest.raises(RuntimeError, match="Failed to query local Tailscale status"):
        _get_local_device_id()


def test_generate_device_invite_missing_url(mocker):
    mocker.patch("peerstash.core.tailscale._get_local_device_id", return_value="12346")

    mock_response = mocker.Mock()
    mock_response.json.return_value = [{"id": "12346", "multiUse": True}]
    mocker.patch("requests.post", return_value=mock_response)

    token = "tskey-api-12345-SECRET"
    invite_code = generate_device_invite(token)

    assert invite_code is None
