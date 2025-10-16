#!/usr/bin/env bash

# Display usage information if help is requested
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Test runner script with multiple options:"
    echo "  (no args)    Run registry tests only"
    echo "  e2e_tests    Run all tests (registry + e2e system tests)"
    echo "  simple       Run simple tests (registry + e2e without save_reuse tests)"
    echo "  --help, -h   Show this help message"
    echo ""
    exit 0
fi

echo "Starting unit tests with uv..."

echo "Running ruff check..."
if ! uv run ruff check; then
    echo "❌ Ruff check failed!"
    exit 1
fi

echo "Running ruff format..."
if ! uv run ruff format --check; then
    echo "❌ Ruff format check failed!"
    exit 1
fi

# Check for test type flag
if [ "$1" = "full_tests" ]; then
    echo "Running full tests (registry + e2e system tests + variables manager tests)..."
    rm ./src/cuga/backend/tools_env/registry/mcp_servers/saved_flows.py
    echo "Running all tests (registry + e2e system tests)..."
    uv run pytest ./src -v
elif [ "$1" = "unit_tests" ]; then
    echo "Running unit tests (registry + variables manager + local sandbox tests)..."
    uv run pytest ./src/cuga/backend/tools_env/registry/tests/ -v
    uv run pytest ./src/cuga/backend/cuga_graph/nodes/api/variables_manager/tests/ -v
    uv run pytest ./src/system_tests/e2e/test_runtime_tools.py -v
    uv run pytest ./src/cuga/backend/tools_env/code_sandbox/tests/ -v
    uv run pytest ./src/system_tests/unit/test_sandbox_async.py -v
else
    echo "Running default tests (registry + variables manager + local sandbox + e2e without save_reuse and without sandbox docker)..."
    uv run pytest ./src/cuga/backend/tools_env/registry/tests/ -v
    uv run pytest ./src/cuga/backend/cuga_graph/nodes/api/variables_manager/tests/ -v
    uv run pytest ./src/cuga/backend/tools_env/code_sandbox/tests/ -v
    uv run pytest ./src/system_tests/e2e/balanced_test.py ./src/system_tests/e2e/fast_test.py ./src/system_tests/e2e/test_runtime_tools.py -v
fi

TEST_EXIT_CODE=$?

echo "Tests completed with exit code: $TEST_EXIT_CODE"
exit $TEST_EXIT_CODE