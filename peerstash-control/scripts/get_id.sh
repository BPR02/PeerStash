#!/bin/bash

SSH_FOLDER="/var/lib/peerstash"

# set up SSH user keys
if [ ! -f ~/.ssh/id_ed25519 ]; then
    # copy or generate keys
    if [ ! -f $SSH_FOLDER/id_ed25519 ]; then
        echo "Generating SSH user keys..."
        ssh-keygen -t ed25519 -N "" -f ~/.ssh/id_ed25519 -C $USERNAME
        cp ~/.ssh/id_* $SSH_FOLDER/
    else
        echo "Using existing SSH user keys..."
        cp $SSH_FOLDER/id_* ~/.ssh/
    fi

    # use generated key for all SSH/SFTP connections
    echo "" >> ~/.ssh/config
    echo "Host *" >> ~/.ssh/config
    echo "	IdentityFile ~/.ssh/id_ed25519" >> ~/.ssh/config
fi
