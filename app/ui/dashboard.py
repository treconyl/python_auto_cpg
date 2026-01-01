from __future__ import annotations

from PySide6 import QtWidgets

from app.services import accounts_service, proxies_service
from app.services.queue_service import QueueService
from app.workers.run_001proxy_worker import reset_stop, run_001proxy_loop, stop_all


class DashboardView(QtWidgets.QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(16)

        header = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel("System Overview")
        title.setObjectName("sectionTitle")
        header.addWidget(title)
        header.addStretch(1)
        refresh = QtWidgets.QPushButton("Refresh")
        refresh.clicked.connect(self.refresh)  # type: ignore[attr-defined]
        header.addWidget(refresh)
        layout.addLayout(header)

        actions = QtWidgets.QHBoxLayout()
        self._run_toggle = QtWidgets.QPushButton("Run 5 Chrome (001proxy)")
        self._run_toggle.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))
        self._run_toggle.clicked.connect(self.toggle_001proxy_batch)  # type: ignore[attr-defined]
        actions.addWidget(self._run_toggle)
        actions.addStretch(1)
        layout.addLayout(actions)

        grid = QtWidgets.QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)

        self._total_value = self._stat_card("Total Accounts", "0", "Pending: 0")
        self._success_value = self._stat_card("Success", "0", "0% completion")
        self._failed_value = self._stat_card("Failed", "0", "Needs review")
        self._proxy_value = self._stat_card("Proxies Running", "0/0", "Active keys")

        grid.addWidget(self._total_value[0], 0, 0)
        grid.addWidget(self._success_value[0], 0, 1)
        grid.addWidget(self._failed_value[0], 0, 2)
        grid.addWidget(self._proxy_value[0], 0, 3)
        layout.addLayout(grid)

        layout.addStretch(1)

        self.refresh()
        self._queue = QueueService(max_workers=5)
        self._is_001proxy_running = False

    def _stat_card(self, title: str, value: str, hint: str) -> tuple[QtWidgets.QFrame, QtWidgets.QLabel, QtWidgets.QLabel]:
        card = QtWidgets.QFrame()
        card.setObjectName("statCard")
        vbox = QtWidgets.QVBoxLayout(card)
        vbox.setSpacing(6)
        title_label = QtWidgets.QLabel(title)
        value_label = QtWidgets.QLabel(value)
        value_label.setObjectName("statValue")
        hint_label = QtWidgets.QLabel(hint)
        hint_label.setObjectName("statHint")
        vbox.addWidget(title_label)
        vbox.addWidget(value_label)
        vbox.addWidget(hint_label)
        return card, value_label, hint_label

    def refresh(self) -> None:
        account_stats = accounts_service.stats()
        proxy_stats = proxies_service.stats()
        total = account_stats["total"]
        success = account_stats["success"]
        failed = account_stats["failed"]
        pending = account_stats["pending"]
        proxy_running = proxy_stats["running"]
        proxy_total = proxy_stats["total"]

        completion = 0.0 if total == 0 else round(success / max(total, 1) * 100, 1)

        self._total_value[1].setText(str(total))
        self._total_value[2].setText(f"Pending: {pending}")
        self._success_value[1].setText(str(success))
        self._success_value[2].setText(f"{completion}% completion")
        self._failed_value[1].setText(str(failed))
        self._failed_value[2].setText("Needs review" if failed else "All good")
        self._proxy_value[1].setText(f"{proxy_running}/{proxy_total}")
        self._proxy_value[2].setText("Active keys")

    def toggle_001proxy_batch(self) -> None:
        if not self._is_001proxy_running:
            reset_stop()
            for _ in range(5):
                self._queue.submit(run_001proxy_loop)
            self._is_001proxy_running = True
            self._run_toggle.setText("Stop 001proxy")
            self._run_toggle.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaStop))
        else:
            stop_all()
            self._is_001proxy_running = False
            self._run_toggle.setText("Run 5 Chrome (001proxy)")
            self._run_toggle.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))
