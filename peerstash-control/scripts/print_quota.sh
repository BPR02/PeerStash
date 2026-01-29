#!/bin/bash

# intended for following use case:
# ./get_quota.sh username host port | ./print_quota.sh

read -r AVAIL
read -r USED

echo "$USED / $AVAIL"
