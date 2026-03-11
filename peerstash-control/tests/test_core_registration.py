import base64
import json
from unittest.mock import mock_open

import pytest
import requests
from pytest_mock import MockerFixture, MockType

from peerstash.core.registration import (PeerExistsError, _delete_known_host,
                                         _update_known_hosts, delete_peer,
                                         parse_share_key, upsert_peer)


@pytest.fixture
def valid_user_data():
    return {
        "username": "bob",
        "server_public_key": "srv_key",
        "client_public_key": "cli_key",
        "invite_code": "code123",
    }


@pytest.fixture
def mock_registration_fs(mocker: MockerFixture):
    """Safely mocks filesystem operations specifically for known_hosts manipulation."""
    mocker.patch("os.makedirs")
    mocker.patch("os.path.exists", return_value=True)
    m_open = mock_open()
    mocker.patch("builtins.open", m_open)
    return m_open


# --- Key Parsing Tests ---


def test_parse_share_key_success(valid_user_data):
    b64_payload = base64.b64encode(
        json.dumps(valid_user_data).encode("utf-8"), altchars=b"-_"
    ).decode("utf-8")
    share_key = f"peerstash.bob#{b64_payload}"

    parsed = parse_share_key(share_key)
    assert parsed["username"] == "bob"
    assert parsed["server_public_key"] == "srv_key"


def test_parse_share_key_username_mismatch(valid_user_data):
    valid_user_data["username"] = "malicious_user"
    b64_payload = base64.b64encode(
        json.dumps(valid_user_data).encode("utf-8"), altchars=b"-_"
    ).decode("utf-8")
    share_key = f"peerstash.bob#{b64_payload}"

    with pytest.raises(ValueError, match="username does not match hash"):
        parse_share_key(share_key)


def test_parse_share_key_invalid_base64():
    with pytest.raises(ValueError, match="Invalid share key"):
        parse_share_key("peerstash.bob#not_valid_base64_!@#")


def test_parse_share_key_missing_delimiter():
    # No '#' character in the string
    with pytest.raises(ValueError, match="Invalid share key"):
        parse_share_key("peerstash.bob_NO_HASH_DELIMITER")


def test_parse_share_key_missing_username_key():
    # Valid base64, but the dictionary is missing the 'username' key
    bad_data = {"server_public_key": "srv"}
    b64_payload = base64.b64encode(json.dumps(bad_data).encode("utf-8")).decode("utf-8")
    share_key = f"peerstash.bob#{b64_payload}"

    with pytest.raises(ValueError, match="Invalid share key"):
        parse_share_key(share_key)


# --- Upsert & Delete Tests ---


def test_upsert_peer_new_success(
    mock_db,
    mock_daemon_and_locks,
    mock_registration_fs,
    mocked_sftpgo_api,
    valid_user_data,
    monkeypatch,
):
    monkeypatch.setenv(
        "API_KEY", "abcDEF987"
    )  # Match the token required by sftpgo_mock.py

    result = upsert_peer(valid_user_data, quota_gb=10, allow_update=False)

    assert result is True
    assert "peerstash-bob" in mock_db["hosts"]


def test_upsert_peer_update_success(
    mock_db,
    mock_daemon_and_locks,
    mock_registration_fs,
    mocked_sftpgo_api,
    valid_user_data,
    monkeypatch,
):
    monkeypatch.setenv("API_KEY", "abcDEF987")
    mock_db["hosts"]["peerstash-bob"] = True  # Seed the DB so it processes as an update

    result = upsert_peer(valid_user_data, quota_gb=20, allow_update=True)

    assert result is True


def test_upsert_peer_db_exists_no_update(mock_db, valid_user_data):
    mock_db["hosts"]["peerstash-bob"] = True

    with pytest.raises(PeerExistsError, match="User bob already exists"):
        upsert_peer(valid_user_data, quota_gb=10, allow_update=False)


def test_upsert_peer_sftpgo_conflict(
    mock_db, mock_daemon_and_locks, mocked_sftpgo_api, monkeypatch
):
    monkeypatch.setenv("API_KEY", "abcDEF987")
    # Trigger the 409 Conflict intentionally programmed into sftpgo_mock.py
    conflict_user_data = {
        "username": "exists",
        "server_public_key": "srv",
        "client_public_key": "cli",
        "invite_code": "code",
    }

    with pytest.raises(RuntimeError, match="Database might be corrupted"):
        upsert_peer(conflict_user_data, quota_gb=10, allow_update=False)


def test_upsert_peer_http_error(
    mock_db, mock_registration_fs, valid_user_data, mocker: MockerFixture
):
    # Mock requests.post to return a generic 500 error, bypassing the SFTPGo mock
    mock_post = mocker.patch("requests.post")
    mock_response = mocker.Mock()
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
        "500 Server Error"
    )
    mock_post.return_value = mock_response

    with pytest.raises(requests.exceptions.HTTPError, match="500 Server Error"):
        upsert_peer(valid_user_data, quota_gb=10, allow_update=False)


def test_delete_peer_success(
    mock_db, mock_registration_fs, mock_daemon_and_locks, mocked_sftpgo_api, monkeypatch
):
    monkeypatch.setenv("API_KEY", "abcDEF987")
    mock_db["hosts"]["peerstash-bob"] = True

    delete_peer("bob")

    assert "peerstash-bob" not in mock_db["hosts"]


def test_delete_peer_http_error(mock_db, mock_registration_fs, mocker: MockerFixture):
    mock_db["hosts"]["peerstash-bob"] = True

    # Mock requests.delete to return a generic 500 error
    mock_delete = mocker.patch("requests.delete")
    mock_response = mocker.Mock()
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
        "500 Server Error"
    )
    mock_delete.return_value = mock_response

    with pytest.raises(requests.exceptions.HTTPError, match="500 Server Error"):
        delete_peer("bob")


# --- Known Hosts Filesystem Tests ---


def test_update_known_hosts_append(
    mock_registration_fs: MockType, mock_daemon_and_locks, mocker: MockerFixture
):
    _update_known_hosts("bob", "srv_key", replace=False)

    mock_registration_fs.assert_called_with(mocker.ANY, "a")
    mock_registration_fs().write.assert_called_with("\n[peerstash-bob]:2022 srv_key\n")


def test_update_known_hosts_replace(
    mock_registration_fs: MockType, mock_daemon_and_locks, mocker: MockerFixture
):
    # Simulate a file with two lines
    file_content = "[peerstash-alice]:2022 old_key\n[peerstash-bob]:2022 old_key\n"
    mock_registration_fs.side_effect = [
        mock_open(read_data=file_content).return_value,  # For reading
        mock_open().return_value,  # For writing
    ]

    _update_known_hosts("bob", "new_srv_key", replace=True)

    mock_registration_fs.assert_called_with(mocker.ANY, "w")
    # Assert alice's key stayed the same, and bob's was updated
    mock_registration_fs().write.assert_any_call("[peerstash-alice]:2022 old_key\n")
    mock_registration_fs().write.assert_any_call("[peerstash-bob]:2022 new_srv_key\n")


def test_delete_known_host(
    mock_registration_fs: MockType, mock_daemon_and_locks, mocker: MockerFixture
):
    file_content = "[peerstash-alice]:2022 key\n[peerstash-bob]:2022 key\n"
    mock_registration_fs.side_effect = [
        mock_open(read_data=file_content).return_value,
        mock_open().return_value,
    ]

    _delete_known_host("bob")

    # Assert bob's line was entirely skipped
    mock_registration_fs.assert_called_with(mocker.ANY, "w")
    mock_registration_fs().write.assert_called_once_with("[peerstash-alice]:2022 key\n")


def test_update_known_hosts_file_creation(
    mock_registration_fs: MockType, mock_daemon_and_locks, mocker: MockerFixture
):
    # Force os.path.exists to False to trigger the file creation block
    mocker.patch("os.path.exists", return_value=False)

    _update_known_hosts("bob", "srv_key", replace=False)

    # Assert it was opened with "w" first (to create), then "a" (to append)
    mock_registration_fs.assert_any_call(mocker.ANY, "w")
    mock_registration_fs.assert_any_call(mocker.ANY, "a")


def test_delete_known_host_file_creation(
    mock_registration_fs: MockType, mock_daemon_and_locks, mocker: MockerFixture
):
    mocker.patch("os.path.exists", return_value=False)

    mock_registration_fs.side_effect = [
        mock_open().return_value,  # 1. For creation "w"
        mock_open(read_data="").return_value,  # 2. For reading "r" (empty file)
        mock_open().return_value,  # 3. For rewriting "w"
    ]

    _delete_known_host("bob")

    # Assert the very first call was to create the file
    assert mock_registration_fs.call_args_list[0] == mocker.call(mocker.ANY, "w")
