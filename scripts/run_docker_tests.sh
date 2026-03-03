#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Create some dummy directories to satisfy mounts
mkdir -p ".test/peerstash_test_root" ".test/peerstash_test_control/config" ".test/peerstash_test_control/data" ".test/peerstash_test_restore"

echo "Bringing up test environment..."
docker compose -f peerstash-compose/docker-compose-test.yml build
docker compose -f peerstash-compose/docker-compose-test.yml up -d

echo "Waiting for container to be ready..."
sleep 3

echo "Running tests..."
# Install uv inside the container and use it to run pytest with dev dependencies
docker exec peerstash-control-test bash -c "pip install uv && cd /app/testing && uv run pytest tests/test_integration_docker.py -v"

echo "Tearing down test environment..."
docker compose -f peerstash-compose/docker-compose-test.yml down

# Clean up dummy directories
rm -rf ".test/peerstash_test_root" ".test/peerstash_test_control" ".test/peerstash_test_restore"
