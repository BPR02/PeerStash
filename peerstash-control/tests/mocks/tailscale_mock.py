import json
import re

import pytest
import responses
from requests import PreparedRequest


def acl_post_callback(request: PreparedRequest) -> tuple[int, dict[str, str], str]:
    """Callback to validate the POST /tailnet/-/acl payload."""
    payload = json.loads(request.body) if request.body else {}
    headers = request.headers
    # check if etag matches the one sent by the mock response for GET /tailnet/-/acl
    if headers["If-Match"] != "123456abcdef":
        return (
            412,
            {},
            json.dumps({"message": "precondition failed, invalid old hash"}),
        )
    return (200, {}, json.dumps(payload))


def keys_post_callback(request: PreparedRequest) -> tuple[int, dict[str, str], str]:
    """Callback to validate the POST /tailnet/-/keys payload."""
    payload = json.loads(request.body) if request.body else {}
    resp = {
        "id": "k123456CNTRL",
        "key": "tskey-auth-abcDEFghijkl-abcDEFGHIJKLMNOPQRSTUVWXYZ123456",
        "keyType": payload["keyType"] if "keyType" in payload else "auth",
        "expirySeconds": (
            payload["expirySeconds"] if "expirySeconds" in payload else 86400
        ),
        "capabilities": payload["capabilities"] if "capabilities" in payload else {},
        "invalid": False,
    }
    return (200, {}, json.dumps(resp))


def device_invite_callback(request: PreparedRequest) -> tuple[int, dict[str, str], str]:
    """Callback to validate the device ID from the URL."""
    # Extract the device ID from the URL using regex
    if not request.url:
        return (404, {}, json.dumps({"message": "Not Found"}))
    match = re.search(r"/device/([^/]+)/device-invites", request.url)
    device_id = match.group(1) if match else ""

    # reject test case
    if device_id == "invalid" or device_id == "":
        return (
            404,
            {},
            json.dumps({"message": "not found"}),
        )

    payload = json.loads(request.body) if request.body else {}

    return (
        200,
        {},
        json.dumps(
            [
                {
                    "id": "12346",
                    "deviceId": device_id,
                    "multiUse": payload["multiUse"] if "multiUse" in payload else False,
                    "inviteUrl": "https://login.tailscale.com/admin/invite/abcXYZ",
                    "accepted": False,
                }
            ]
        ),
    )


@pytest.fixture
def mocked_tailscale_api():
    """Fixture that uses responses to mock the Tailscale API."""
    with responses.RequestsMock() as rsps:
        base_url = "https://api.tailscale.com/api/v2"

        # Static Mock: GET /tailnet/-/acl
        rsps.add(
            responses.GET,
            f"{base_url}/tailnet/-/acl",
            json={
                "grants": [
                    {
                        "src": ["*"],
                        "dst": ["*"],
                        "ip": ["*"],
                    },
                ],
                "ssh": [
                    {
                        "action": "check",
                        "src": ["autogroup:member"],
                        "dst": ["autogroup:self"],
                        "users": ["autogroup:nonroot", "root"],
                    }
                ],
            },
            headers={"etag": "123456abcdef"},
            status=200,
        )

        # Static Mock: DELETE /tailnet/-/keys/{keyId}
        rsps.add(
            responses.DELETE,
            re.compile(rf"^{base_url}/tailnet/-/keys/[^/]+$"),
            status=200,
        )

        # Dynamic Mock: POST /tailnet/-/keys
        rsps.add(
            responses.POST,
            f"{base_url}/tailnet/-/keys",
            callback=keys_post_callback,
            content_type="application/json",
        )

        # Dynamic Mock: POST /tailnet/-/acl
        rsps.add_callback(
            responses.POST,
            f"{base_url}/tailnet/-/acl",
            callback=acl_post_callback,
            content_type="application/json",
        )

        # Dynamic Mock: POST /device/{deviceId}/device-invites
        rsps.add_callback(
            responses.POST,
            re.compile(rf"^{base_url}/device/[^/]+/device-invites$"),
            callback=device_invite_callback,
            content_type="application/json",
        )

        yield rsps  # Yield control back to the test
