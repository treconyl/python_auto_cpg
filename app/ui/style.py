from __future__ import annotations


def app_stylesheet() -> str:
    return """
    QWidget {
        font-family: "Helvetica Neue", "Segoe UI", Arial, sans-serif;
        font-size: 13px;
        color: #2b2f36;
        background-color: #fff2ea;
    }

    QMainWindow::separator {
        background: #f0d5c4;
        width: 1px;
        height: 1px;
    }

    QTabWidget::pane {
        border: 1px solid #f0d5c4;
        border-radius: 18px;
        padding: 16px;
        background: #fff7f2;
    }

    QTabBar::tab {
        background: #ffffff;
        color: #9a7d6d;
        padding: 10px 18px;
        border-radius: 16px;
        margin-right: 10px;
    }

    QTabBar::tab:selected {
        background: #ff7a2f;
        color: #ffffff;
    }

    QPushButton {
        background: #ff7a2f;
        border: none;
        border-radius: 14px;
        padding: 9px 16px;
        font-weight: 600;
        color: #ffffff;
    }

    QPushButton:hover {
        background: #f06b1e;
    }

    QPushButton:pressed {
        background: #e45f14;
    }

    QLineEdit, QComboBox, QTextEdit, QPlainTextEdit {
        background: #ffffff;
        border: 1px solid #f0d5c4;
        border-radius: 12px;
        padding: 8px 10px;
        selection-background-color: #ff7a2f;
    }

    QComboBox::drop-down {
        border: none;
        width: 20px;
    }

    QTableWidget {
        background: #ffffff;
        border: 1px solid #f0d5c4;
        border-radius: 16px;
        gridline-color: #f3dfd3;
    }

    QHeaderView::section {
        background: #fff0e8;
        color: #a07055;
        padding: 8px 10px;
        border: none;
        border-bottom: 1px solid #f0d5c4;
    }

    QTableWidget::item:selected {
        background: #ffe7d6;
    }

    QLabel#sectionTitle {
        font-size: 20px;
        font-weight: 600;
        color: #1f2937;
    }

    QFrame#statCard {
        background: #ffffff;
        border: 1px solid #f2dacb;
        border-radius: 18px;
        padding: 14px;
    }

    QLabel#statValue, QLabel#statHint {
        background: transparent;
    }

    QLabel#statValue {
        font-size: 22px;
        font-weight: 700;
        color: #111827;
    }

    QLabel#statHint {
        color: #9a7d6d;
    }
    """
