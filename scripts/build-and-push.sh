#!/bin/bash

# Peerstash
# Copyright (C) 2026 BPR02

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

set -e

# Usage: ./scripts/build-and-push.sh <image_name> <version_tag> <branch_name>
IMAGE_NAME=$1
TAG=$2
BRANCH=$3

if [ -z "$GITHUB_TOKEN" ] || [ -z "$REPO_OWNER" ]; then
  echo "Error: Environment variables GITHUB_TOKEN and REPO_OWNER are required."
  exit 1
fi

FULL_IMAGE="ghcr.io/$REPO_OWNER/$IMAGE_NAME"

# Authenticate
echo "$GITHUB_TOKEN" | docker login --username "$REPO_OWNER" --password-stdin ghcr.io

# Build the specific tag (e.g., :1.0.1 OR :dev)
echo "🏗️  Building $FULL_IMAGE:$TAG..."
docker build -t "$FULL_IMAGE:$TAG" .
docker push "$FULL_IMAGE:$TAG"

# Only if we are on main, also push 'latest' and 'dev'
if [ "$BRANCH" = "main" ]; then
  echo "🏷️  Tagging $FULL_IMAGE:latest..."
  docker tag "$FULL_IMAGE:$TAG" "$FULL_IMAGE:latest"
  docker push "$FULL_IMAGE:latest"
  
  echo "🏷️  Tagging $FULL_IMAGE:dev to match latest..."
  docker tag "$FULL_IMAGE:$TAG" "$FULL_IMAGE:dev"
  docker push "$FULL_IMAGE:dev"
fi
