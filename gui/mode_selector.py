"""遗传模式选择器"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QComboBox
from PyQt6.QtCore import pyqtSignal
from config import GENETIC_MODES


class ModeSelector(QWidget):
    """遗传模式下拉框，发出 mode_changed 信号"""

    mode_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        group = QGroupBox("遗传模式")
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(6)

        self.combo = QComboBox()
        for mode_key, mode_label in GENETIC_MODES.items():
            self.combo.addItem(mode_label, mode_key)
        self.combo.setCurrentIndex(0)
        self.combo.currentIndexChanged.connect(
            lambda idx: self.mode_changed.emit(self.combo.itemData(idx))
        )
        group_layout.addWidget(self.combo)

        layout.addWidget(group)

    def current_mode(self):
        """返回当前选中的模式 key"""
        return self.combo.currentData() or "classic"
