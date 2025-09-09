#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
TESTS_DIR="$ROOT_DIR/tests"

echo "[tests] Running scraper offline unit tests (no network)..."
"$TESTS_DIR/scraper_unit.sh"

echo "[tests] Scraper unit tests completed. Proceeding to integration suites."

echo "[tests] Running database integration tests..."
"$ROOT_DIR/database/test_integration.sh"

echo "[tests] Running API integration tests..."
"$ROOT_DIR/api/test_api_integration.sh"

echo "[tests] All tests completed."


