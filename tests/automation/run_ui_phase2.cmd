@echo off
setlocal
cd /d \\wsl.localhost\Ubuntu\home\loc\LMS_NEW

tests\automation\.venv-win\Scripts\pytest.exe -n 2 --dist loadscope -m ui_phase2 tests\automation\test_ui_phase2_learning.py tests\automation\test_ui_phase2_notifications.py tests\automation\test_ui_phase2_assessments.py --html=tests/automation/reports/ui_phase2_report.html --self-contained-html --junitxml=tests/automation/reports/ui_phase2_junit.xml
if errorlevel 1 exit /b %errorlevel%

tests\automation\.venv-win\Scripts\python.exe tests\automation\generate_ui_phase2_testcase_report.py
