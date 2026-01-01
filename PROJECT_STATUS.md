# python_auto_cpg notes

## Scope and business flow

- Goal: replace PHP/Laravel with a native Python desktop app (PySide6) while keeping the core workflow: manage accounts, manage proxies, run Playwright to rotate passwords, view logs.
- Runtime: macOS + Windows via PyInstaller.
- Storage: SQLite with WAL + retry to handle up to 5 concurrent workers writing status.

## Steps (done / todo)

- [x] Create Python app skeleton under `python_auto_cpg/`.
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

- `python_auto_cpg/app/main.py` - app entry, tabs.
- `python_auto_cpg/app/services/db.py` - SQLite WAL + retry + migrate.
- `python_auto_cpg/app/services/accounts_service.py` - accounts CRUD + import/export.
- `python_auto_cpg/app/services/proxies_service.py` - proxy CRUD + API actions.
- `python_auto_cpg/app/services/garena_service.py` - Playwright spawn + log.
- `python_auto_cpg/app/ui/*` - views.
- `python_auto_cpg/playwright/*.js` - Playwright scripts (garena + 001proxy).
- `python_auto_cpg/requirements.txt` - runtime deps.

## Basic run (dev)

- Install deps: `pip install -r python_auto_cpg/requirements.txt`
- Run UI: `python3 -m app.main` from `python_auto_cpg/`

## Playwright setup (only when running Garena/001proxy jobs)

- Ensure scripts live in `python_auto_cpg/playwright/` (or set `PLAYWRIGHT_ROOT` to another repo).
- Install node deps: `cd python_auto_cpg/playwright && npm install`
- Install browser: `npx playwright install chromium`

## Build (PyInstaller)

- Run: `./build_pyinstaller.sh` from `python_auto_cpg/`
- Output: `python_auto_cpg/dist/python_auto_cpg`

## Notes

- SQLite is safe for 5 workers if WAL + retry is enabled (already in `db.py`).
- Playwright scripts are expected under `python_auto_cpg/playwright/` (or via `PLAYWRIGHT_ROOT`).
