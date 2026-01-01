from __future__ import annotations

from datetime import datetime
import csv
import random
import string
from typing import Any

from app.services import db


def list_accounts(
    search: str | None = None,
    status: str | None = None,
    sort: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
    error_only: bool = False,
) -> list[dict[str, Any]]:
    conditions = []
    params: list[object] = []

    if search:
        conditions.append("login LIKE ?")
        params.append(f"%{search}%")
    if status:
        conditions.append("status = ?")
        params.append(status)
    if error_only or sort == "error_latest":
        conditions.append("last_error IS NOT NULL")

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    order_by = "updated_at DESC"
    if sort == "updated_oldest":
        order_by = "updated_at ASC"
    if sort == "attempt_newest":
        order_by = "last_attempted_at DESC, id DESC"
    if sort == "attempt_oldest":
        order_by = "last_attempted_at ASC, id ASC"
    if sort == "error_latest":
        order_by = "last_attempted_at DESC, id DESC"

    limit_clause = ""
    params_out = list(params)
    if limit is not None:
        limit_clause = " LIMIT ?"
        params_out.append(limit)
        if offset is not None:
            limit_clause += " OFFSET ?"
            params_out.append(offset)

    sql = f"SELECT * FROM accounts {where} ORDER BY {order_by}{limit_clause};"

    with db.session() as connection:
        rows = db.execute_with_retry(connection, sql, tuple(params_out)).fetchall()
    return [dict(row) for row in rows]


def count_accounts(search: str | None = None, status: str | None = None, error_only: bool = False) -> int:
    conditions = []
    params: list[object] = []

    if search:
        conditions.append("login LIKE ?")
        params.append(f"%{search}%")
    if status:
        conditions.append("status = ?")
        params.append(status)
    if error_only:
        conditions.append("last_error IS NOT NULL")

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    sql = f"SELECT COUNT(*) FROM accounts {where};"

    with db.session() as connection:
        return db.execute_with_retry(connection, sql, tuple(params)).fetchone()[0]


def create_account(payload: dict[str, Any]) -> None:
    now = datetime.utcnow().isoformat(timespec="seconds")
    with db.session() as connection:
        db.execute_with_retry(
            connection,
            """
            INSERT INTO accounts (login, current_password, next_password, status, last_error, last_attempted_at, last_succeeded_at, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """.strip(),
            (
                payload["login"],
                payload.get("current_password"),
                payload.get("next_password"),
                payload.get("status", "pending"),
                payload.get("last_error"),
                payload.get("last_attempted_at"),
                payload.get("last_succeeded_at"),
                now,
                now,
            ),
        )


def update_account(account_id: int, payload: dict[str, Any]) -> None:
    now = datetime.utcnow().isoformat(timespec="seconds")
    with db.session() as connection:
        db.execute_with_retry(
            connection,
            """
            UPDATE accounts
            SET login = ?, current_password = ?, next_password = ?, status = ?, last_error = ?, updated_at = ?
            WHERE id = ?;
            """.strip(),
            (
                payload["login"],
                payload.get("current_password"),
                payload.get("next_password"),
                payload.get("status", "pending"),
                payload.get("last_error"),
                now,
                account_id,
            ),
        )


def update_account_status(account_id: int, status: str, last_error: str | None = None) -> None:
    now = datetime.utcnow().isoformat(timespec="seconds")
    last_succeeded_at = now if status == "success" else None
    with db.session() as connection:
        db.execute_with_retry(
            connection,
            """
            UPDATE accounts
            SET status = ?, last_error = ?, last_attempted_at = ?, last_succeeded_at = ?, updated_at = ?
            WHERE id = ?;
            """.strip(),
            (status, last_error, now, last_succeeded_at, now, account_id),
        )


def mark_success(account_id: int, new_password: str) -> None:
    now = datetime.utcnow().isoformat(timespec="seconds")
    with db.session() as connection:
        db.execute_with_retry(
            connection,
            """
            UPDATE accounts
            SET status = 'success',
                current_password = ?,
                next_password = ?,
                last_error = NULL,
                last_attempted_at = ?,
                last_succeeded_at = ?,
                updated_at = ?
            WHERE id = ?;
            """.strip(),
            (new_password, new_password, now, now, now, account_id),
        )


def mark_failed(account_id: int, error: str | None) -> None:
    now = datetime.utcnow().isoformat(timespec="seconds")
    with db.session() as connection:
        db.execute_with_retry(
            connection,
            """
            UPDATE accounts
            SET status = 'failed',
                last_error = ?,
                last_attempted_at = ?,
                updated_at = ?
            WHERE id = ?;
            """.strip(),
            (error, now, now, account_id),
        )


def claim_next_account(new_password: str) -> dict[str, Any] | None:
    with db.session() as connection:
        db.execute_with_retry(connection, "BEGIN IMMEDIATE;")
        row = db.execute_with_retry(
            connection,
            """
            SELECT * FROM accounts
            WHERE status = 'pending' AND current_password IS NOT NULL
            ORDER BY id
            LIMIT 1;
            """.strip(),
        ).fetchone()
        if not row:
            return None
        now = datetime.utcnow().isoformat(timespec="seconds")
        db.execute_with_retry(
            connection,
            """
            UPDATE accounts
            SET status = 'processing',
                last_attempted_at = ?,
                last_error = NULL,
                next_password = ?,
                updated_at = ?
            WHERE id = ?;
            """.strip(),
            (now, new_password, now, row["id"]),
        )
        return dict(row)


def generate_password() -> str:
    length = random.randint(10, 12)
    upper = "ABCDEFGHJKLMNPQRSTUVWXYZ"
    lower = "abcdefghijkmnopqrstuvwxyz"
    digits = "23456789"
    special = "@#$%&*?!"
    pool = upper + lower + digits + special

    chars = [
        random.choice(upper),
        random.choice(lower),
        random.choice(digits),
        random.choice(special),
    ]
    chars.extend(random.choice(pool) for _ in range(length - len(chars)))
    random.shuffle(chars)
    return "".join(chars)


def import_accounts(file_path: str) -> dict[str, int]:
    inserted = 0
    updated = 0
    skipped = 0
    now = datetime.utcnow().isoformat(timespec="seconds")

    def parse_line(line: str) -> tuple[str, str] | None:
        line = line.strip()
        if not line or line.startswith("#"):
            return None
        if "|" in line:
            parts = [part.strip() for part in line.split("|", 1)]
        else:
            parts = [part.strip() for part in next(csv.reader([line]))]
        if len(parts) < 2 or not parts[0] or not parts[1]:
            return None
        return parts[0], parts[1]

    with db.session() as connection:
        with open(file_path, "r", encoding="utf-8") as handle:
            for raw in handle:
                parsed = parse_line(raw)
                if not parsed:
                    skipped += 1
                    continue
                login, password = parsed
                exists = db.execute_with_retry(
                    connection,
                    "SELECT 1 FROM accounts WHERE login = ?;",
                    (login,),
                ).fetchone()
                db.execute_with_retry(
                    connection,
                    """
                    INSERT INTO accounts (login, current_password, status, last_error, created_at, updated_at)
                    VALUES (?, ?, 'pending', NULL, ?, ?)
                    ON CONFLICT(login) DO UPDATE SET
                        current_password = excluded.current_password,
                        status = 'pending',
                        last_error = NULL,
                        updated_at = excluded.updated_at;
                    """.strip(),
                    (login, password, now, now),
                )
                if exists:
                    updated += 1
                else:
                    inserted += 1

    return {"inserted": inserted, "updated": updated, "skipped": skipped}


def export_accounts(file_path: str) -> None:
    with db.session() as connection:
        rows = db.execute_with_retry(
            connection,
            "SELECT login, current_password, status, last_attempted_at, last_error FROM accounts ORDER BY id ASC;",
        ).fetchall()

    with open(file_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["login", "current_password", "status", "last_attempted_at", "last_error"])
        for row in rows:
            writer.writerow(
                [
                    row["login"],
                    row["current_password"],
                    row["status"],
                    row["last_attempted_at"],
                    row["last_error"],
                ]
            )


def stats() -> dict[str, Any]:
    with db.session() as connection:
        total = db.execute_with_retry(connection, "SELECT COUNT(*) FROM accounts;").fetchone()[0]
        success = db.execute_with_retry(
            connection,
            "SELECT COUNT(*) FROM accounts WHERE status = 'success';",
        ).fetchone()[0]
        failed = db.execute_with_retry(
            connection,
            "SELECT COUNT(*) FROM accounts WHERE status = 'failed';",
        ).fetchone()[0]
        pending = db.execute_with_retry(
            connection,
            "SELECT COUNT(*) FROM accounts WHERE status = 'pending';",
        ).fetchone()[0]
    return {
        "total": total,
        "success": success,
        "failed": failed,
        "pending": pending,
    }
