#!/usr/bin/env bash
set -euo pipefail

source "$(dirname "$0")/.venv/bin/activate"
pytest -m quick tests/automation
