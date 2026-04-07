# LMS Automation Setup

This folder contains the Selenium + Pytest automation scaffold for the LMS ASM report.

To avoid long runs that can take 30+ minutes, the recommended default is now a very small `quick` suite for daily checks. A slightly broader `smoke` suite is still available when you want more LMS coverage without running the whole 55-case pack.

## Default target

- Base URL: `http://lms.localhost:8000`
- Sample account: `Administrator / admin`
- Default HTML report: `tests/automation/reports/report.html`
- Recommended default run: `pytest -m quick`

## Run from VS Code on Windows

1. Select interpreter: `tests\automation\.venv-win\Scripts\python.exe`
2. Open the Testing panel.
3. Run the discovered Pytest cases from the UI.

VS Code is configured to run the `quick` suite by default so the machine does not get stuck on long test sessions.

## Run from terminal

### PowerShell

```powershell
.\tests\automation\.venv-win\Scripts\Activate.ps1
pytest -m quick
```

### WSL / Linux

```bash
source tests/automation/.venv/bin/activate
pytest -m quick
```

## Useful options

```powershell
pytest -m quick
pytest -m smoke
pytest tests/automation/test_auth.py::test_tc01_login_redirects_to_dashboard -q
pytest --headed -m quick
pytest --base-url http://lms.localhost:8000 -m quick
```

## Suites

### Quick suite

Fast daily regression checks that avoid heavy seeded data:

- `TC01` Login redirects to dashboard
- `TC26` Admin creates user and queues welcome email

### Smoke suite

Broader LMS coverage using the cases already verified end-to-end:

- `TC01` Login redirects to dashboard
- `TC21` Live class join link access
- `TC24` Fast Learner badge assignment
- `TC26` Admin creates user and queues welcome email
- `TC28` Statistics page shows large user count
- `TC29` Mobile homepage rendering
- `TC34` Batch discussion comment
- `TC53` Sidebar navigation to core sections

## Full suite

If you still want to run the whole 55-case suite later, use an explicit command:

```powershell
pytest tests/automation
```

## UI Phase 1

Parallel-safe E2E flows built directly from the current LMS UI and routes, without using the ASM PDF or heavy seed data.

Run them with xdist. The verified stable setting for this machine is `-n 2`, which keeps parallelism without overloading Chrome headless:

```powershell
pytest -n auto -m ui_phase1 tests/automation/test_ui_phase1_e2e.py
```

Current phase-1 flows:

- `UI01` Login page renders email, password, and login button
- `UI02` Admin can enter LMS and see core sidebar navigation
- `UI03` Sidebar opens Courses
- `UI04` Sidebar opens Programs
- `UI05` Sidebar opens Batches
- `UI06` Sidebar opens Search and returns the empty-state message for a unique query
- `UI07` Sidebar opens Notifications and shows Unread/Read tabs
- `UI08` Sidebar opens Statistics and renders key cards
- `UI09` User menu toggles theme
- `UI10` User menu logs out


## Launchers

- Windows CMD: `tests\automation\run_quick.cmd`
- PowerShell: `tests\automation\run_quick.ps1`
- WSL/Linux: `tests/automation/run_quick.sh`
- Broader suite: `tests\automation\run_smoke.cmd`
- UI phase 2: `tests\automation\run_ui_phase2.cmd`

## Environment variables

- `LMS_BASE_URL`
- `LMS_ADMIN_USERNAME`
- `LMS_ADMIN_PASSWORD`
- `LMS_CHROME_BINARY`

If Chrome is not auto-detected, set `LMS_CHROME_BINARY` to the browser executable path.

## UI Phase 2

Stateful E2E flows built directly from the current LMS UI, while using deterministic seed data only for setup and reset.

Run them with xdist. The verified stable setting for this machine is `-n 2`, which keeps parallelism without overloading Chrome headless:

```powershell
pytest -n 2 --dist loadscope -m ui_phase2 tests/automation/test_ui_phase2_learning.py tests/automation/test_ui_phase2_notifications.py tests/automation/test_ui_phase2_assessments.py --html=tests/automation/reports/ui_phase2_report.html --self-contained-html --junitxml=tests/automation/reports/ui_phase2_junit.xml
python tests/automation/generate_ui_phase2_testcase_report.py
```

Current phase-2 flows:

- `UI21` Student can enroll in a free course
- `UI22` Lesson page auto-updates student progress
- `UI23` Completed student sees Get Certificate
- `UI24` Notifications page shows backend-created unread data
- `UI25` Notification can move from Unread to Read
- `UI26` First quiz attempt is recorded
- `UI27` Quiz blocks after maximum attempts
- `UI28` Quiz summary shows 80 percent score
- `UI29` Assignment accepts PDF upload
- `UI30` Assignment rejects EXE upload


