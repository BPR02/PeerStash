import base64
import json

import pytest
from pytest_mock import MockerFixture

from peerstash.core.identity import (_generate_identity_payload,
                                     generate_share_key)


@pytest.fixture
def mock_identity_fs(mocker: MockerFixture):
    """Mocks file reads for public keys dynamically."""

    def fake_get_file_content(path):
        if "sftpgo" in path:
            return "server_key_123"
        if ".ssh" in path:
            return "client_key_456"
        return None

    return mocker.patch(
        "peerstash.core.identity.get_file_content", side_effect=fake_get_file_content
    )


def test_generate_share_key_success(mock_db, mock_identity_fs):
    key = generate_share_key()

    # Assert string format
    prefix, b64_payload = key.split("#")
    assert prefix == "peerstash.mockuser"

    # Assert payload decodes properly and matches DB mock defaults
    decoded = json.loads(base64.b64decode(b64_payload, altchars=b"-_").decode("utf-8"))
    assert decoded["username"] == "mockuser"
    assert decoded["server_public_key"] == "server_key_123"
    assert decoded["client_public_key"] == "client_key_456"
    assert decoded["invite_code"] == "invite_xyz"


def test_generate_payload_missing_username(mock_db, mock_identity_fs, mocker: MockerFixture):
    mocker.patch("peerstash.core.identity.db_get_user", return_value=None)
    with pytest.raises(ValueError, match="Username not found"):
        _generate_identity_payload()


def test_generate_payload_missing_server_key(mock_db, mocker: MockerFixture):
    mocker.patch(
        "peerstash.core.identity.get_file_content", side_effect=[None, "client_key"]
    )
    with pytest.raises(ValueError, match="Host keys not found"):
        _generate_identity_payload()


def test_generate_payload_missing_client_key(mock_db, mocker: MockerFixture):
    mocker.patch(
        "peerstash.core.identity.get_file_content", side_effect=["server_key", None]
    )
    with pytest.raises(ValueError, match="User keys not found"):
        _generate_identity_payload()


def test_generate_payload_missing_invite_code(mock_db, mock_identity_fs, mocker: MockerFixture):
    mocker.patch("peerstash.core.identity.db_get_invite_code", return_value=None)
    with pytest.raises(ValueError, match="Invite code not found"):
        _generate_identity_payload()
