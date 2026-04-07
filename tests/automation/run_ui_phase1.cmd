@echo off
set PYTHON=\\wsl.localhost\Ubuntu\home\loc\LMS_NEW\tests\automation\.venv-win\Scripts\python.exe
"%PYTHON%" -u -m pytest -n auto --dist loadscope -m ui_phase1 tests/automation/test_ui_phase1_e2e.py
