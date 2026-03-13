#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Define a cleanup function that always runs at the end
cleanup() {
    echo "Tearing down test environment..."
    docker compose -f peerstash-compose/docker-compose-test.yml down || true
    
    # Use sudo in case Docker created files as root inside the bind mount
    if [ -d ".test" ]; then
        rm -rf ".test"
    fi
}

# Trap any exit (success, error, or Ctrl+C) and trigger the cleanup function
trap cleanup EXIT

# Create some dummy directories to satisfy mounts
mkdir -p ".test/peerstash_test_root" ".test/peerstash_test_control/config" ".test/peerstash_test_control/data" ".test/peerstash_test_restore"

echo "Bringing up test environment..."
docker compose -f peerstash-compose/docker-compose-test.yml build
docker compose -f peerstash-compose/docker-compose-test.yml up -d

echo "Waiting for container to be ready..."
sleep 3

echo "Running tests..."
# Temporarily disable 'set -e' so the script doesn't abort if tests fail
set +e
# Install uv inside the container and use it to run pytest with dev dependencies
docker exec peerstash-control-test bash -c "pip install uv && cd /app/testing && UV_PROJECT_ENVIRONMENT=/tmp/.venv uv run pytest tests/ --cov=peerstash --cov-report=term-missing --cov-report=html -v"

# Exit with the actual pytest exit code so CI/CD pipelines know if tests failed
TEST_EXIT_CODE=$?
set -e
exit $TEST_EXIT_CODE
