#!/bin/sh

ORIGINAL_PASSWD="/usr/bin/passwd"
DB_PATH="/peerstash/config/users.db"

# Read input from stdin
echo "Old password:"
read -s OLD_PASSWORD

# verify old password (since we're root, passwd will not ask for old password)
CURRENT_HASH=$(grep "^$USER:" /etc/shadow | cut -d: -f2)
if ! echo "$OLD_PASSWORD" | openssl passwd -6 -stdin --salt "$(echo "$CURRENT_HASH" | cut -d'$' -f3)" | grep -q "$CURRENT_HASH"; then
    echo "Incorrect password"
    exit 1
fi

echo "New password:"
read -s NEW_PASSWORD
echo "Retype password:"
read -s CONFIRM_PASSWORD

# Pass to the original passwd binary
(echo "$NEW_PASSWORD"; echo "$CONFIRM_PASSWORD") | $ORIGINAL_PASSWD $USER

# If passwd succeeded, hash the new password and save it
if [ $? -eq 0 ]; then
    HASHED_PASSWORD=$(openssl passwd -6 $NEW_PASSWORD)

    # Store hashed password in SQLite database
    sqlite3 "$DB_PATH" "UPDATE users SET password_hash='$HASHED_PASSWORD' WHERE username='$USER';"
    echo "Updated database"
else
    # echo "Failed to update password."
    exit 1
fi
