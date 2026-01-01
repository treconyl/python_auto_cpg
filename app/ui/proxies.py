from __future__ import annotations

from datetime import datetime
from PySide6 import QtCore, QtWidgets

from app.services import proxies_service


class ProxiesView(QtWidgets.QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QtWidgets.QVBoxLayout(self)

        header = QtWidgets.QLabel("Proxy Keys")
        header.setObjectName("sectionTitle")
        layout.addWidget(header)

        toolbar = QtWidgets.QHBoxLayout()
        add_btn = QtWidgets.QPushButton("Add")
        add_btn.clicked.connect(self.add_proxy)  # type: ignore[attr-defined]
        refresh_btn = QtWidgets.QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_proxies)  # type: ignore[attr-defined]
        toolbar.addWidget(add_btn)
        toolbar.addWidget(refresh_btn)
        toolbar.addStretch(1)
        layout.addLayout(toolbar)

        self._table = QtWidgets.QTableWidget(0, 6)
        self._table.setHorizontalHeaderLabels(
            ["Label", "Status", "IP", "Expires", "Last Used", "Actions"]
        )
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.itemDoubleClicked.connect(self.edit_proxy)  # type: ignore[attr-defined]
        layout.addWidget(self._table)

        self.load_proxies()

    def load_proxies(self) -> None:
        self._table.setRowCount(0)
        for row in proxies_service.list_proxies():
            row_idx = self._table.rowCount()
            self._table.insertRow(row_idx)
            label_item = QtWidgets.QTableWidgetItem(row["label"])
            label_item.setData(QtCore.Qt.ItemDataRole.UserRole, row["id"])
            label_item.setData(QtCore.Qt.ItemDataRole.UserRole + 1, row.get("api_key") or "")
            label_item.setData(QtCore.Qt.ItemDataRole.UserRole + 2, row.get("is_active", 1))
            label_item.setData(QtCore.Qt.ItemDataRole.UserRole + 3, row.get("meta") or {})
            self._table.setItem(row_idx, 0, label_item)
            self._table.setItem(row_idx, 1, QtWidgets.QTableWidgetItem(row.get("status") or ""))
            meta = row.get("meta") or {}
            self._table.setItem(row_idx, 2, QtWidgets.QTableWidgetItem(meta.get("last_proxy_http") or ""))
            self._table.setItem(row_idx, 3, QtWidgets.QTableWidgetItem(meta.get("last_proxy_expire_at") or ""))
            self._table.setItem(row_idx, 4, QtWidgets.QTableWidgetItem(row.get("last_used_at") or ""))
            self._table.setCellWidget(row_idx, 5, self._actions_widget(row))

    def add_proxy(self) -> None:
        dialog = ProxyDialog(self)
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            proxies_service.create_proxy(dialog.payload())
            self.load_proxies()

    def edit_proxy(self, item: QtWidgets.QTableWidgetItem) -> None:
        proxy_id = item.data(QtCore.Qt.ItemDataRole.UserRole)
        if proxy_id is None:
            return
        row_idx = item.row()
        dialog = ProxyDialog(self, self._row_payload(row_idx))
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            proxies_service.update_proxy(proxy_id, dialog.payload())
            self.load_proxies()

    def _row_payload(self, row_idx: int) -> dict[str, str | bool | dict]:
        label_item = self._table.item(row_idx, 0)
        return {
            "label": label_item.text(),
            "api_key": label_item.data(QtCore.Qt.ItemDataRole.UserRole + 1) or "",
            "status": self._table.item(row_idx, 1).text() or "idle",
            "is_active": bool(label_item.data(QtCore.Qt.ItemDataRole.UserRole + 2)),
            "meta": label_item.data(QtCore.Qt.ItemDataRole.UserRole + 3) or {},
        }

    def _actions_widget(self, proxy: dict[str, object]) -> QtWidgets.QWidget:
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        test_btn = QtWidgets.QPushButton("Test")
        rotate_btn = QtWidgets.QPushButton("Rotate")
        stop_btn = QtWidgets.QPushButton("Stop")

        test_btn.clicked.connect(lambda: self.test_proxy(proxy))  # type: ignore[attr-defined]
        rotate_btn.clicked.connect(lambda: self.rotate_proxy(proxy))  # type: ignore[attr-defined]
        stop_btn.clicked.connect(lambda: self.stop_proxy(proxy))  # type: ignore[attr-defined]

        layout.addWidget(test_btn)
        layout.addWidget(rotate_btn)
        layout.addWidget(stop_btn)
        layout.addStretch(1)
        return widget

    def test_proxy(self, proxy: dict[str, object]) -> None:
        try:
            payload = proxies_service.test_proxy(proxy)
        except Exception as exc:
            QtWidgets.QMessageBox.warning(self, "Proxy API", str(exc))
            return
        self._apply_proxy_payload(proxy, payload, action="test")

    def rotate_proxy(self, proxy: dict[str, object]) -> None:
        try:
            payload = proxies_service.rotate_proxy(proxy)
        except Exception as exc:
            QtWidgets.QMessageBox.warning(self, "Proxy API", str(exc))
            return
        self._apply_proxy_payload(proxy, payload, action="rotate")

    def stop_proxy(self, proxy: dict[str, object]) -> None:
        proxies_service.stop_proxy(int(proxy["id"]))
        self.load_proxies()

    def _apply_proxy_payload(self, proxy: dict[str, object], payload: dict[str, object], action: str) -> None:
        meta = dict(proxy.get("meta") or {})
        meta["last_proxy_response"] = payload
        meta["last_proxy_http"] = payload.get("proxyhttp")
        meta["last_proxy_socks"] = payload.get("proxysocks5")
        meta["last_proxy_username"] = payload.get("username")
        meta["last_proxy_password"] = payload.get("password")
        meta["last_proxy_rotated_at"] = datetime.utcnow().isoformat(timespec="seconds")

        status_code = payload.get("status")
        if status_code == 100:
            meta["last_proxy_expire_at"] = payload.get("Token expiration date")
            proxies_service.set_proxy_status(int(proxy["id"]), "running", is_active=True)
        else:
            proxies_service.set_proxy_status(int(proxy["id"]), "expired", is_active=False)

        proxies_service.update_proxy_meta(int(proxy["id"]), meta)
        self.load_proxies()


class ProxyDialog(QtWidgets.QDialog):
    def __init__(self, parent: QtWidgets.QWidget | None = None, payload: dict[str, str | bool] | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Proxy Key")
        self.setModal(True)

        layout = QtWidgets.QVBoxLayout(self)
        form = QtWidgets.QFormLayout()

        self._label = QtWidgets.QLineEdit(payload.get("label", "") if payload else "")
        self._api_key = QtWidgets.QPlainTextEdit(payload.get("api_key", "") if payload else "")
        self._status = QtWidgets.QComboBox()
        self._status.addItems(["idle", "running", "expired"])
        if payload and payload.get("status") in ["idle", "running", "expired"]:
            self._status.setCurrentText(payload["status"])
        self._is_active = QtWidgets.QCheckBox()
        self._is_active.setChecked(bool(payload.get("is_active", True)) if payload else True)

        form.addRow("Label", self._label)
        form.addRow("API Key", self._api_key)
        form.addRow("Status", self._status)
        form.addRow("Active", self._is_active)
        layout.addLayout(form)

        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Save | QtWidgets.QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)  # type: ignore[attr-defined]
        buttons.rejected.connect(self.reject)  # type: ignore[attr-defined]
        layout.addWidget(buttons)

    def payload(self) -> dict[str, str | bool]:
        return {
            "label": self._label.text().strip(),
            "api_key": self._api_key.toPlainText().strip(),
            "status": self._status.currentText(),
            "is_active": self._is_active.isChecked(),
        }
