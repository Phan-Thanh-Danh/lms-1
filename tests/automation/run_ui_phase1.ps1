$ErrorActionPreference = "Stop"

$python = Join-Path $PSScriptRoot ".venv-win\Scripts\python.exe"

if (-not (Test-Path $python)) {
    throw "Windows virtual environment not found at $python"
}

& $python -u -m pytest -n auto --dist loadscope -m ui_phase1 tests/automation/test_ui_phase1_e2e.py
