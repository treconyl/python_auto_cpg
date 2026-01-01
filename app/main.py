from __future__ import annotations

import sys

import os
import warnings

os.environ.setdefault("QT_LOGGING_RULES", "qt.gui.icc=false")

try:
    from urllib3.exceptions import NotOpenSSLWarning
except Exception:  # pragma: no cover - optional dependency behavior
    NotOpenSSLWarning = None

from PySide6 import QtGui, QtWidgets

from app.services import db
from app.ui.accounts import AccountsView
from app.ui.dashboard import DashboardView
from app.ui.garena_test import GarenaTestView
from app.ui.proxies import ProxiesView
from app.ui.style import app_stylesheet
from app.config import settings


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("python_auto_cpg")
        icon_path = settings.ASSETS_DIR / "logo.png"
        if icon_path.exists():
            self.setWindowIcon(QtGui.QIcon(str(icon_path)))
        self.resize(1280, 720)

        tabs = QtWidgets.QTabWidget()
        tabs.addTab(DashboardView(), "Dashboard")
        tabs.addTab(ProxiesView(), "Proxy Keys")
        tabs.addTab(AccountsView(), "Accounts")
        tabs.addTab(GarenaTestView(), "Account Test")

        self.setCentralWidget(tabs)


def main() -> int:
    db.ensure_paths()
    db.migrate()

    if NotOpenSSLWarning is not None:
        warnings.filterwarnings("ignore", category=NotOpenSSLWarning)

    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("python_auto_cpg")
    app.setStyleSheet(app_stylesheet())
    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
