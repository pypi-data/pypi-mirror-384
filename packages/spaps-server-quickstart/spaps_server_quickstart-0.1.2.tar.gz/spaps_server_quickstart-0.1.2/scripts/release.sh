#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

echo "==> Running test suite"
PYTHONPATH="$PROJECT_ROOT/src" python3 -m pytest -q

echo "==> Linting"
python3 -m ruff check "$PROJECT_ROOT/src" "$PROJECT_ROOT/tests"

echo "==> Type checking"
python3 -m mypy "$PROJECT_ROOT/src"

echo "==> Building distribution"
cd "$PROJECT_ROOT"
rm -rf dist
python3 -m build

echo "==> Uploading via twine"
python3 -m twine upload dist/*

echo "Release complete." 
