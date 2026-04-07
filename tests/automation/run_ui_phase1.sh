#!/usr/bin/env bash
set -euo pipefail

source "$(dirname "$0")/.venv/bin/activate"
pytest -n auto --dist loadscope -m ui_phase1 tests/automation/test_ui_phase1_e2e.py
