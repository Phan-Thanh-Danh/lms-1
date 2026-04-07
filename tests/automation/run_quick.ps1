$ErrorActionPreference = "Stop"

$python = Join-Path $PSScriptRoot ".venv-win\Scripts\python.exe"

if (-not (Test-Path $python)) {
    throw "Windows virtual environment not found at $python"
}

& $python -u -m pytest -m quick tests/automation
