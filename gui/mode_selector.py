"""遗传模式选择器 — 顶部水平Tab"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QButtonGroup
from PyQt6.QtCore import pyqtSignal
from config import GENETIC_MODES, COLOR_DOMINANT, COLOR_BG_PANEL, COLOR_BORDER


class ModeSelector(QWidget):
    """顶部水平Tab，发出 mode_changed 信号"""

    mode_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._buttons = {}
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._group = QButtonGroup(self)

        for mode_key, mode_label in GENETIC_MODES.items():
            btn = QPushButton(mode_label)
            btn.setCheckable(True)
            btn.setFlat(True)
            btn.setCursor(self.cursor())
            btn.setStyleSheet(f"""
                QPushButton {{
                    padding: 6px 14px;
                    border: 1px solid {COLOR_BORDER};
                    border-radius: 4px;
                    background: {COLOR_BG_PANEL};
                    font-size: 12px;
                    color: #64748b;
                }}
                QPushButton:hover {{
                    border-color: {COLOR_DOMINANT};
                    color: {COLOR_DOMINANT};
                }}
                QPushButton:checked {{
                    background: {COLOR_DOMINANT};
                    color: white;
                    border-color: {COLOR_DOMINANT};
                }}
            """)
            btn.clicked.connect(lambda checked, k=mode_key: self.mode_changed.emit(k))
            self._group.addButton(btn)
            self._buttons[mode_key] = btn
            layout.addWidget(btn)

        layout.addStretch()

        # 默认选中第一个
        first_key = list(GENETIC_MODES.keys())[0]
        self._buttons[first_key].setChecked(True)

    def current_mode(self):
        for key, btn in self._buttons.items():
            if btn.isChecked():
                return key
        return "classic"
