"""超级孟德尔基因大数对决数字实验室 — 程序入口"""

import sys
import os

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon


def main():
    """主函数：初始化 QApplication 并启动主窗口"""

    # 高DPI支持（Qt6 默认启用，显式设置确保兼容性）
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Super Mendel Gene Big-Data Duel Lab")
    app.setOrganizationName("MendelDataLab")
    app.setApplicationVersion("1.0.0")

    # 设置应用图标（如果有的话，纯代码绘制避免依赖外部文件）
    # 暂时省略图标设置

    # 创建并显示主窗口
    from gui.main_window import MainWindow
    window = MainWindow()
    window.show()

    # 进入事件循环
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
