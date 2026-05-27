"""遗传模式选择器"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QRadioButton
from PyQt6.QtCore import pyqtSignal
from config import GENETIC_MODES


class ModeSelector(QWidget):
    """遗传模式单选组，发出 mode_changed 信号"""

    mode_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.buttons = {}
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        group = QGroupBox("遗传模式")
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(6)

        first = True
        for mode_key, mode_label in GENETIC_MODES.items():
            btn = QRadioButton(mode_label)
            btn.setChecked(first)
            btn.toggled.connect(
                lambda checked, k=mode_key: (
                    self.mode_changed.emit(k) if checked else None
                )
            )
            self.buttons[mode_key] = btn
            group_layout.addWidget(btn)
            first = False

        layout.addWidget(group)

    def current_mode(self):
        """返回当前选中的模式 key"""
        for key, btn in self.buttons.items():
            if btn.isChecked():
                return key
        return "classic"
