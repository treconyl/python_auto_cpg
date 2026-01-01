# Kien truc de xuat (PySide6 + SQLite + PyInstaller)

## Muc tieu
- Thay the hoan toan PHP/Laravel.
- Chay duoc tren macOS va Windows.
- Giu logic chinh: quan ly account, proxy key, chay Playwright doi mat khau, xem log.

## Tong quan thanh phan
- UI: PySide6 (Qt)
- Database: SQLite (WAL mode)
- Worker: queue noi bo + thread pool
- Playwright: chay subprocess node (playwright/garena-runner.js)
- Log: file + hien thi trong UI (tail)
- Build: PyInstaller

## So do module (goi y)
- app/
  - main.py (boot UI, khoi tao DB, load config)
  - ui/ (man hinh)
    - dashboard.py
    - proxies.py
    - accounts.py
    - garena_test.py
  - services/
    - db.py (SQLite connection, WAL, retry)
    - accounts_service.py
    - proxies_service.py
    - garena_service.py
    - queue_service.py (job dispatcher)
  - workers/
    - run_garena_worker.py (spawn Playwright)
    - process_pending_worker.py (chon account + rotate proxy + queue)
  - models/
    - account.py
    - proxy_key.py
    - garena_credential.py
  - config/
    - settings.py (default password, path)

## SQLite luong va ghi
- Bat WAL: PRAGMA journal_mode=WAL;
- Connection rieng cho moi thread.
- Retry khi gap lock: backoff 50-200ms, toi da 5-7 lan.
- Voi 5 luong, tan suat ghi 1 phut/lan/luong thi OK.

## Mapping chuc nang hien tai -> Python
- Dashboard
  - Thong ke account (pending/success/failed)
  - Proxy running/total
  - Latest error
- Proxy Keys
  - CRUD
  - Test/Rotate/Stop (goi proxyxoay.shop API)
  - Luu meta: last_proxy_http, last_proxy_rotated_at, last_proxy_expire_at
- Accounts
  - Import CSV/TXT
  - Export CSV
  - Filter + edit
- Garena Test
  - Chon account, new password, proxy key
  - Run job, log 200 dong cuoi

## Playwright
- Giữ file JS hien tai, goi bang subprocess:
  - set env: GARENA_USERNAME, GARENA_PASSWORD, GARENA_NEW_PASSWORD, PLAYWRIGHT_HEADLESS...
- Log output vao file: logs/garena-test.log

## Build
- PyInstaller onefile hoac onedir.
- Bundled assets: playwright script, icons, logs folder.

## De xuat tiep theo
- Dinh nghia schema SQLite
- Tao UI skeleton (PySide6)
- Chuyen logic proxy/test/rotate
