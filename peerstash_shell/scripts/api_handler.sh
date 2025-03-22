#!/bin/sh

WEB_APP_PUBKEY_PATH="/peerstash/config/web_app_public.pem"

# Read from input
read -r REQUEST_TYPE
read -r PAYLOAD
read -r SIGNATURE

# Handle web app public key submission (only allowed once)
if [ "$REQUEST_TYPE" = "SET_PUBKEY" ]; then
    if [ -s "$WEB_APP_PUBKEY_PATH" ]; then
        echo "Web app public key already set. Rejecting update." >&2
        exit 1
    fi
    echo "$PAYLOAD" > "$WEB_APP_PUBKEY_PATH"
    echo "Web app public key stored."
    exit 0
fi

# Handle authentication requests from the web app
if [ "$REQUEST_TYPE" = "AUTH_REQUEST" ]; then
    # Ensure the web app public key exists
    if [ ! -s "$WEB_APP_PUBKEY_PATH" ]; then
        echo "No web app public key found. Unauthorized request." >&2
        exit 1
    fi

    # Verify the request signature
    sig="$(mktemp)"
    echo "$SIGNATURE" | base64 -d > "$sig"
    if ! echo "$PAYLOAD" | openssl dgst -sha256 -verify "$WEB_APP_PUBKEY_PATH" -signature "$sig"; then
        echo "Signature verification failed. Unauthorized request." >&2
        rm "$sig"
        exit 1
    fi
    rm "$sig"

    echo "Authentication successful."
    exit 0
fi

echo "Invalid request type." >&2
exit 1
