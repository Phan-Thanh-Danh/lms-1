@echo off
set PYTHON=\\wsl.localhost\Ubuntu\home\loc\LMS_NEW\tests\automation\.venv-win\Scripts\python.exe
"%PYTHON%" -u -m pytest -m quick tests/automation
