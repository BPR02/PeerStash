import json
import re

import pytest
import responses
from requests import PreparedRequest


def token_get_callback(request: PreparedRequest) -> tuple[int, dict[str, str], str]:
    """Callback to validate the GET /token authorization."""
    headers = request.headers

    # check if authorization matches `admin:adminpass`
    if headers.get("Authorization", "") != "Basic YWRtaW46YWRtaW5wYXNz":
        return (
            401,
            {},
            json.dumps({"message": "Unauthorized"}),
        )
    return (
        200,
        {},
        json.dumps({"access_token": "abc123", "expires_at": "2026-03-01T00:00:00Z"}),
    )


def users_post_callback(request: PreparedRequest) -> tuple[int, dict[str, str], str]:
    """Callback to validate the PUT /users user existence."""
    payload = json.loads(request.body) if request.body else {}
    headers = request.headers

    # check if authorization matches `the key given by the mock POST /apikeys`
    if headers.get("Authorization", "") != "Bearer abcDEF987":
        return (
            401,
            {},
            json.dumps({"message": "Unauthorized"}),
        )

    # reject test case
    username = payload.get("username")
    if not username:
        return (
            404,
            {},
            json.dumps({"message": "Not Found"}),
        )

    if username == "exists":
        return (
            409,
            {},
            json.dumps(
                {
                    "error": "duplicated key not allowed: UNIQUE constraint failed: users.username",
                    "message": "",
                }
            ),
        )

    return (
        200,
        {},
        json.dumps(
            {
                "id": 1,
                "status": payload.get("status", 0),
                "username": username,
                "public_keys": payload.get("public_keys", []),
                "home_dir": f"/srv/sftpgo/data/{username}",
                "quota_size": payload.get("quota_size", 0),
                "quota_files": 0,
                "permissions": payload.get("permissions", {}),
            }
        ),
    )


def users_put_callback(request: PreparedRequest) -> tuple[int, dict[str, str], str]:
    """Callback to validate the PUT /users/{username} user existence."""
    if not request.url:
        return (404, {}, json.dumps({"message": "Not Found"}))
    match = re.search(r"/users/([^/]+)", request.url)
    username = match.group(1) if match else ""
    headers = request.headers

    # check if authorization matches `the key given by the mock POST /apikeys`
    if headers.get("Authorization", "") != "Bearer abcDEF987":
        return (
            401,
            {},
            json.dumps({"message": "Unauthorized"}),
        )

    # reject test case
    if username == "invalid" or username == "":
        return (
            404,
            {},
            json.dumps({"message": "Not Found"}),
        )

    return (
        200,
        {},
        json.dumps({"message": "User updated"}),
    )


@pytest.fixture
def mocked_sftpgo_api():
    """Fixture that uses responses to mock the SFTPGo API."""
    with responses.RequestsMock() as rsps:
        base_url = "http://localhost:8080/api/v2"

        # Dynamic Mock: GET /token
        rsps.add(
            responses.GET,
            f"{base_url}/token",
            callback=token_get_callback,
            content_type="application/json",
        )

        # Static Mock: GET /apikeys
        rsps.add(
            responses.GET,
            f"{base_url}/apikeys",
            json=[
                [
                    {
                        "id": "abcdefg",
                        "name": "host",
                        "scope": 1,
                        "created_at": 0,
                        "updated_at": 0,
                        "admin": "admin",
                    },
                    {
                        "id": "lmnop",
                        "name": "not_host",
                        "scope": 1,
                        "created_at": 0,
                        "updated_at": 0,
                        "admin": "admin2",
                    },
                ]
            ],
            status=200,
        )

        # Static Mock: POST /apikeys
        rsps.add(
            responses.POST,
            f"{base_url}/apikeys",
            json={
                "mesage": "API key created. This is the only time the API key is visible, please save it.",
                "key": "abcDEF987",
            },
            status=200,
        )

        # Static Mock: PUT /admin/profile
        rsps.add(
            responses.PUT,
            f"{base_url}/admin/profile",
            json={"message": "User updated"},
            status=200,
        )

        # Dynamic Mock: POST /users
        rsps.add(
            responses.POST,
            f"{base_url}/users",
            callback=users_post_callback,
            content_type="application/json",
        )

        # Dynamic Mock: PUT /users/{username}
        rsps.add(
            responses.PUT,
            re.compile(rf"^{base_url}/users/[^/]+$"),
            callback=users_put_callback,
            content_type="application/json",
        )

        # Static Mock: DELETE /users/{username}
        rsps.add(
            responses.DELETE,
            re.compile(rf"^{base_url}/users/[^/]+$"),
            json={"message": "User deleted"},
            status=200,
        )

        yield rsps  # Yield control back to the test
