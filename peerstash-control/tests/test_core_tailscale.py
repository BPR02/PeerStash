import subprocess

import commentjson
import pytest
import requests
from pytest import MonkeyPatch
from pytest_mock import MockerFixture

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


def test_revoke_api_token_network_error(mocker: MockerFixture):
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


def test_modify_policy_filters_default_rules(mocker: MockerFixture):
    """Verifies that default allow-all rules are stripped from the policy."""
    # 1. Mock the GET response to inject a policy with the default allow-all rules
    mock_get = mocker.patch("requests.get")
    mock_get.return_value.headers = {"ETag": "W/123"}
    mock_get.return_value.text = commentjson.dumps(
        {
            "acls": [
                {"action": "accept", "src": ["*"], "dst": ["*:*"]},
                {"action": "accept", "src": ["admin"], "dst": ["*:22"]},
            ],
            "grants": [
                {"src": ["*"], "dst": ["*"], "ip": ["*"]},
            ],
        }
    )

    # 2. Mock the POST request so we can intercept the modified payload
    mock_post = mocker.patch("requests.post")

    # 3. Execute the function
    modify_policy("tskey-api-123")

    # 4. Extract the JSON payload that was about to be sent to Tailscale
    mock_post.assert_called_once()
    posted_data = mock_post.call_args.kwargs["data"]
    posted_policy = commentjson.loads(posted_data)

    # 5. Assert the allow-all rule was removed from acls, but valid rules were kept
    assert len(posted_policy["acls"]) == 1
    assert posted_policy["acls"][0]["src"] == ["admin"]

    # 6. Assert the allow-all is also correctly stripped from the grants system
    grants = posted_policy.get("grants", [])
    assert not any(
        g.get("src") == ["*"] and g.get("dst") == ["*"] and g.get("ip") == ["*"]
        for g in grants
    )


def test_modify_policy_initializes_missing_grants(mocker: MockerFixture):
    """Verifies that the grants list is initialized if it doesn't exist."""
    # 1. Mock GET response with a policy that completely lacks the "grants" key
    mock_get = mocker.patch("requests.get")
    mock_get.return_value.headers = {"ETag": "W/123"}
    mock_get.return_value.text = commentjson.dumps(
        {
            "acls": [{"action": "accept", "src": ["admin"], "dst": ["*:22"]}]
            # "grants" is intentionally omitted
        }
    )

    # 2. Mock POST request to intercept the payload
    mock_post = mocker.patch("requests.post")

    # 3. Execute the function
    modify_policy("tskey-api-123")

    # 4. Extract the JSON payload
    mock_post.assert_called_once()
    posted_data = mock_post.call_args.kwargs["data"]
    posted_policy = commentjson.loads(posted_data)

    # 5. Assert the 'grants' key was safely created by the `else` block
    assert "grants" in posted_policy

    # 6. Assert that the 3 required Peerstash routing rules were successfully appended to it
    assert len(posted_policy["grants"]) == 3
    assert {
        "src": ["tag:peerstash"],
        "dst": ["tag:peerstash"],
        "ip": ["tcp:2022"],
    } in posted_policy["grants"]


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
    with pytest.raises(subprocess.CalledProcessError, match="sudo"):
        register_device("tskey-api-12345-SECRET", "wrong_sudo_pass")


def test_get_local_device_id_failure(mock_subprocess, monkeypatch: MonkeyPatch):
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


def test_get_local_device_id_daemon_down(mock_subprocess, monkeypatch: MonkeyPatch):
    monkeypatch.setenv("MOCK_TAILSCALE_DOWN", "1")
    with pytest.raises(RuntimeError, match="Failed to query local Tailscale status"):
        _get_local_device_id()


def test_generate_device_invite_missing_url(mocker: MockerFixture):
    mocker.patch("peerstash.core.tailscale._get_local_device_id", return_value="12346")

    mock_response = mocker.Mock()
    mock_response.json.return_value = [{"id": "12346", "multiUse": True}]
    mocker.patch("requests.post", return_value=mock_response)

    token = "tskey-api-12345-SECRET"
    invite_code = generate_device_invite(token)

    assert invite_code is None
