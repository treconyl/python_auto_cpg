from __future__ import annotations

from concurrent.futures import Future
from pathlib import Path
from PySide6 import QtCore, QtWidgets

from app.config import settings
from app.services import accounts_service, proxies_service
from app.services.queue_service import QueueService
from app.workers.run_garena_worker import run_garena_job


class GarenaTestView(QtWidgets.QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QtWidgets.QVBoxLayout(self)

        header = QtWidgets.QLabel("Account Test Runner")
        header.setObjectName("sectionTitle")
        layout.addWidget(header)

        toolbar = QtWidgets.QHBoxLayout()
        refresh_btn = QtWidgets.QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_data)  # type: ignore[attr-defined]
        toolbar.addWidget(refresh_btn)
        toolbar.addStretch(1)
        layout.addLayout(toolbar)

        form = QtWidgets.QFormLayout()
        self._accounts = QtWidgets.QComboBox()
        self._new_password = QtWidgets.QLineEdit()
        self._new_password.setText(settings.DEFAULT_NEW_PASSWORD)
        self._proxies = QtWidgets.QComboBox()
        self._headless = QtWidgets.QCheckBox("Headless")
        self._headless.setChecked(True)
        form.addRow("Account", self._accounts)
        form.addRow("New Password", self._new_password)
        form.addRow("Proxy Key", self._proxies)
        form.addRow("", self._headless)
        layout.addLayout(form)

        actions = QtWidgets.QHBoxLayout()
        run_btn = QtWidgets.QPushButton("Run Test")
        run_btn.clicked.connect(self.run_test)  # type: ignore[attr-defined]
        actions.addWidget(run_btn)
        actions.addStretch(1)
        layout.addLayout(actions)

        log_label = QtWidgets.QLabel("Latest log")
        layout.addWidget(log_label)

        self._log_view = QtWidgets.QPlainTextEdit()
        self._log_view.setReadOnly(True)
        layout.addWidget(self._log_view)

        self._queue = QueueService(max_workers=5)
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(5000)
        self._timer.timeout.connect(self.load_log_tail)  # type: ignore[attr-defined]
        self._timer.start()

        self.load_data()
        self.load_log_tail()

    def load_data(self) -> None:
        self._accounts.clear()
        self._proxies.clear()
        self._proxies.addItem("None", None)

        for account in accounts_service.list_accounts():
            label = account["login"]
            self._accounts.addItem(label, account)

        for proxy in proxies_service.list_proxies():
            label = f"{proxy['label']} ({proxy.get('status') or 'idle'})"
            self._proxies.addItem(label, proxy)

    def run_test(self) -> None:
        account = self._accounts.currentData()
        if not account:
            QtWidgets.QMessageBox.warning(self, "Run Test", "Select an account")
            return
        new_password = self._new_password.text().strip() or settings.DEFAULT_NEW_PASSWORD
        if not self._password_valid(new_password):
            QtWidgets.QMessageBox.warning(
                self,
                "Run Test",
                "Password must be 8-16 chars with upper/lower/digit/special.",
            )
            return

        credentials = {
            "account_id": account["id"],
            "username": account["login"],
            "password": account.get("current_password") or "",
            "new_password": new_password,
            "proxy_key_id": None,
            "proxy_label": None,
            "headless": self._headless.isChecked(),
        }

        proxy = self._proxies.currentData()
        if proxy:
            credentials["proxy_key_id"] = proxy["id"]
            credentials["proxy_label"] = proxy["label"]

        if not credentials["password"]:
            QtWidgets.QMessageBox.warning(self, "Run Test", "Account has no password")
            return

        future = self._queue.submit(run_garena_job, credentials)
        future.add_done_callback(self._handle_job_result)
        self.load_log_tail()

    def load_log_tail(self) -> None:
        log_path = Path(settings.LOG_FILE)
        if not log_path.exists():
            self._log_view.setPlainText("")
            return
        lines = log_path.read_text(encoding="utf-8").splitlines()
        tail = "\n".join(lines[-200:])
        self._log_view.setPlainText(tail)

    def _handle_job_result(self, future: Future) -> None:
        try:
            code = future.result()
            message = "Job done" if code == 0 else f"Job failed ({code})"
        except Exception as exc:
            message = f"Job error: {exc}"
        QtCore.QTimer.singleShot(0, lambda: self._on_job_finished(message))

    def _on_job_finished(self, message: str) -> None:
        self.load_log_tail()
        QtWidgets.QMessageBox.information(self, "Garena Test", message)

    def _password_valid(self, value: str) -> bool:
        if len(value) < 8 or len(value) > 16:
            return False
        has_upper = any(ch.isupper() for ch in value)
        has_lower = any(ch.islower() for ch in value)
        has_digit = any(ch.isdigit() for ch in value)
        has_special = any(not ch.isalnum() for ch in value)
        return has_upper and has_lower and has_digit and has_special
