#!/bin/sh

ORIGINAL_PASSWD="/usr/bin/passwd"
DB_PATH="/peerstash/config/users.db"

# Read input from stdin
stty -echo
printf "Old Password: "
read -r OLD_PASSWORD
stty echo
printf "\n"

# verify old password (since we're root, passwd will not ask for old password)
CURRENT_HASH=$(grep "^$USER:" /etc/shadow | cut -d: -f2)
if ! echo "$OLD_PASSWORD" | openssl passwd -6 -stdin --salt "$(echo "$CURRENT_HASH" | cut -d'$' -f3)" | grep -q "$CURRENT_HASH"; then
    echo "Incorrect password"
    exit 1
fi

stty -echo
printf "New Password: "
read -r NEW_PASSWORD
stty echo
printf "\n"
stty -echo
printf "Retype Password: "
read -r CONFIRM_PASSWORD
stty echo
printf "\n"

# Pass to the original passwd binary
if (echo "$NEW_PASSWORD"; echo "$CONFIRM_PASSWORD") | $ORIGINAL_PASSWD "$USER"; then
    # If passwd succeeded, hash the new password and save it
    HASHED_PASSWORD=$(openssl passwd -6 "$NEW_PASSWORD")

    # Store hashed password in SQLite database
    sqlite3 "$DB_PATH" "UPDATE users SET password_hash='$HASHED_PASSWORD' WHERE username='$USER';"
    echo "Updated database"
else
    # echo "Failed to update password."
    exit 1
fi
