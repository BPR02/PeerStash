#!/bin/bash
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
  docker tag "$FULL_IMAGE:$VERSION" "$FULL_IMAGE:dev"
  docker push "$FULL_IMAGE:dev"
fi
