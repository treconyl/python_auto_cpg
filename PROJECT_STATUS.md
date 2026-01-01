# Python port notes

## Scope and business flow

- Goal: replace PHP/Laravel with a native Python desktop app (PySide6) while keeping the core workflow: manage accounts, manage proxies, run Playwright to rotate passwords, view logs.
- Runtime: macOS + Windows via PyInstaller.
- Storage: SQLite with WAL + retry to handle up to 5 concurrent workers writing status.

## Steps (done / todo)

- [x] Create Python app skeleton under `python_port/`.
- [x] Add SQLite init + migrations (accounts, proxy_keys, garena_test_credentials).
- [x] Implement CRUD services for accounts and proxies.
- [x] Connect Accounts UI: list, add/edit dialog, import/export CSV.
- [x] Connect Proxies UI: list, add/edit dialog.
- [x] Add proxy API integration (test/rotate/stop) and write proxy meta to DB.
- [x] Add queue service + Playwright runner with log tail in UI.
- [x] Update account status on job start/success/fail.
- [x] Implement password policy validation on UI (8-16 chars, upper/lower/digit/special).
- [x] Add multi-run (dispatch 5 workers across active proxies) similar to Laravel flow.
- [x] Add proxy cooldown handling (skip rotate if last rotated < 60s).
- [x] Add account filtering and search in UI.
- [x] Improve error handling + user feedback (API failures, timeouts).
- [x] Add packaging spec and build script for PyInstaller (icon, logs, assets).

## Key files

- `python_port/app/main.py` - app entry, tabs.
- `python_port/app/services/db.py` - SQLite WAL + retry + migrate.
- `python_port/app/services/accounts_service.py` - accounts CRUD + import/export.
- `python_port/app/services/proxies_service.py` - proxy CRUD + API actions.
- `python_port/app/services/garena_service.py` - Playwright spawn + log.
- `python_port/app/ui/*` - views.
- `python_port/requirements.txt` - runtime deps.

## Basic run (dev)

- Install deps: `pip install -r python_port/requirements.txt`
- Run UI: `python -m app.main` from `python_port/`

## Build (PyInstaller)

- Run: `./build_pyinstaller.sh` from `python_port/`
- Output: `python_port/dist/garena-tool`

## Notes

- SQLite is safe for 5 workers if WAL + retry is enabled (already in `db.py`).
- Playwright Node script is reused from existing `playwright/garena-runner.js`.
