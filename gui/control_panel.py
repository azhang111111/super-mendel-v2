"""亲代基因型选择控制面板"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QLabel,
    QComboBox, QSpinBox, QSlider, QPushButton,
    QProgressBar, QHBoxLayout, QStackedWidget,
    QDoubleSpinBox, QLineEdit, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt
from config import (
    GENOTYPE_OPTIONS, SIMULATION_PRESETS,
    COLOR_DOMINANT, COLOR_RECESSIVE, COLOR_ACCENT,
    ABO_GENOTYPES
)


class ControlPanel(QWidget):
    """左侧控制面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("controlPanel")
        self.current_mode = "classic"
        self._input_widgets = []
        self._mg_input_widgets = []
        self._mg_input_combos = []
        self._preset_buttons = []
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # ── QStackedWidget: 模式页面 ──
        self.stacked = QStackedWidget()

        # Page 0: 经典单基因
        self.stacked.addWidget(self._create_classic_page())

        # Page 1: 多基因杂交
        self.stacked.addWidget(self._create_multigene_page())

        # Page 2: 性染色体
        self.stacked.addWidget(self._create_sex_page())

        # Page 3: ABO 血型
        self.stacked.addWidget(self._create_abo_page())

        # Page 4: 多基因数量性状
        self.stacked.addWidget(self._create_polygenic_page())

        layout.addWidget(self.stacked)

        # ── 模拟次数设置 (公共) ──
        sim_group = QGroupBox("模拟规模")
        sim_layout = QVBoxLayout(sim_group)
        sim_layout.setSpacing(8)

        preset_label = QLabel("快捷预设：")
        preset_label.setStyleSheet(f"color: {COLOR_ACCENT};")
        sim_layout.addWidget(preset_label)

        preset_row = QHBoxLayout()
        preset_row.setSpacing(4)
        for preset in SIMULATION_PRESETS:
            btn = QPushButton(self._format_number(preset))
            btn.setFixedHeight(28)
            btn.setStyleSheet("""
                QPushButton {
                    font-size: 10px;
                    padding: 4px 6px;
                    border-radius: 3px;
                }
            """)
            btn.clicked.connect(lambda checked, p=preset: self._set_simulations(p))
            preset_row.addWidget(btn)
            self._preset_buttons.append(btn)
        sim_layout.addLayout(preset_row)

        spin_row = QHBoxLayout()
        spin_label = QLabel("精确次数：")
        self.count_spin = QSpinBox()
        self.count_spin.setRange(10, 10_000_000)
        self.count_spin.setSingleStep(1000)
        self.count_spin.setValue(10000)
        self.count_spin.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.count_spin.valueChanged.connect(self._on_spin_changed)
        spin_row.addWidget(spin_label)
        spin_row.addWidget(self.count_spin)
        sim_layout.addLayout(spin_row)

        self.count_slider = QSlider(Qt.Orientation.Horizontal)
        self.count_slider.setRange(1, 100)
        self.count_slider.setValue(40)
        self.count_slider.valueChanged.connect(self._on_slider_changed)
        sim_layout.addWidget(self.count_slider)

        layout.addWidget(sim_group)

        # ── 开始按钮 ──
        self.run_button = QPushButton("开始模拟")
        self.run_button.setMinimumHeight(44)
        self.run_button.setStyleSheet(f"""
            QPushButton {{
                font-size: 14px;
                background-color: {COLOR_DOMINANT};
            }}
        """)
        self.run_button.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self.run_button)

        # ── 进度条 ──
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("就绪")
        layout.addWidget(self.progress_bar)

        layout.addStretch()

    # ── Page factories ──

    def _create_classic_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)

        parent_group = QGroupBox("亲代基因型")
        parent_layout = QVBoxLayout(parent_group)
        parent_layout.setSpacing(10)

        female_row = QHBoxLayout()
        female_label = QLabel("母本基因型：")
        female_label.setStyleSheet(f"color: {COLOR_RECESSIVE}; font-weight: bold;")
        self.female_combo = QComboBox()
        self.female_combo.addItems(GENOTYPE_OPTIONS)
        self.female_combo.setCurrentIndex(1)
        female_row.addWidget(female_label)
        female_row.addWidget(self.female_combo)
        female_row.addStretch()
        parent_layout.addLayout(female_row)

        male_row = QHBoxLayout()
        male_label = QLabel("父本基因型：")
        male_label.setStyleSheet(f"color: {COLOR_DOMINANT}; font-weight: bold;")
        self.male_combo = QComboBox()
        self.male_combo.addItems(GENOTYPE_OPTIONS)
        self.male_combo.setCurrentIndex(1)
        male_row.addWidget(male_label)
        male_row.addWidget(self.male_combo)
        male_row.addStretch()
        parent_layout.addLayout(male_row)

        layout.addWidget(parent_group)
        layout.addStretch()

        self._input_widgets.extend([self.female_combo, self.male_combo])
        return page

    def _create_multigene_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)

        group = QGroupBox("多基因杂交参数")
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(10)

        count_row = QHBoxLayout()
        count_row.addWidget(QLabel("基因数："))
        self.mg_gene_count = QComboBox()
        self.mg_gene_count.addItems(["2个基因", "3个基因", "4个基因"])
        self.mg_gene_count.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.mg_gene_count.currentIndexChanged.connect(self._on_mg_gene_count_changed)
        count_row.addWidget(self.mg_gene_count)
        count_row.addStretch()
        group_layout.addLayout(count_row)

        # 可滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFixedHeight(160)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
            }
            QScrollArea > QWidget > QWidget {
                background-color: #ffffff;
            }
            QScrollBar:vertical {
                width: 6px;
                background: transparent;
                border: none;
            }
            QScrollBar::handle:vertical {
                background: #cbd5e1;
                border-radius: 3px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        self.mg_genes_container = QWidget()
        self.mg_genes_container.setStyleSheet("background-color: #ffffff;")
        self.mg_genes_layout = QVBoxLayout(self.mg_genes_container)
        self.mg_genes_layout.setSpacing(6)
        self.mg_genes_layout.setContentsMargins(8, 8, 8, 8)

        scroll_area.setWidget(self.mg_genes_container)
        group_layout.addWidget(scroll_area)

        layout.addWidget(group)
        layout.addStretch()

        self._mg_input_widgets = []
        self._build_mg_gene_inputs()
        return page

    def _build_mg_gene_inputs(self):
        """重建 MultiGenePage 中各基因的输入块 (垂直布局)"""
        # 清空旧控件
        while self.mg_genes_layout.count():
            item = self.mg_genes_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

        # 从全局追踪中移除旧的基因输入控件
        for w in self._mg_input_widgets:
            if w in self._input_widgets:
                self._input_widgets.remove(w)
        self._mg_input_widgets.clear()
        self._mg_input_combos.clear()

        n = self.mg_gene_count.currentIndex() + 2  # 0→2基因, 1→3基因, 2→4基因
        combo_options = ["AA", "Aa", "aa"]

        group_style = """
            QGroupBox {
                font-weight: bold;
                border: 1px solid #e2e8f0;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 14px;
                background-color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
            }
        """

        for i in range(n):
            gene_box = QGroupBox(f"基因{i + 1}")
            gene_box.setStyleSheet(group_style)
            box_layout = QVBoxLayout(gene_box)
            box_layout.setSpacing(4)
            box_layout.setContentsMargins(10, 14, 10, 10)

            # 母本行
            mother_row = QHBoxLayout()
            mother_row.addWidget(QLabel("母本："))
            mother_combo = QComboBox()
            mother_combo.addItems(combo_options)
            mother_combo.setCurrentIndex(1)
            mother_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
            mother_row.addWidget(mother_combo)
            mother_row.addStretch()
            box_layout.addLayout(mother_row)

            # 父本行
            father_row = QHBoxLayout()
            father_row.addWidget(QLabel("父本："))
            father_combo = QComboBox()
            father_combo.addItems(combo_options)
            father_combo.setCurrentIndex(1)
            father_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
            father_row.addWidget(father_combo)
            father_row.addStretch()
            box_layout.addLayout(father_row)

            self.mg_genes_layout.addWidget(gene_box)

            # 分隔线 (除最后一个)
            if i < n - 1:
                sep = QFrame()
                sep.setFrameShape(QFrame.Shape.HLine)
                sep.setFixedHeight(1)
                sep.setStyleSheet("background-color: #e2e8f0; border: none;")
                self.mg_genes_layout.addWidget(sep)

            self._mg_input_combos.append((mother_combo, father_combo))
            self._mg_input_widgets.extend([mother_combo, father_combo])

        self.mg_genes_layout.addSpacing(14)
        self.mg_genes_layout.addStretch()
        self._input_widgets.extend(self._mg_input_widgets)

    @staticmethod
    def _clear_layout(layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                ControlPanel._clear_layout(item.layout())

    def _on_mg_gene_count_changed(self, _index):
        self._build_mg_gene_inputs()

    def _create_sex_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)

        group = QGroupBox("性染色体 (X 连锁)")
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(10)

        mother_row = QHBoxLayout()
        mother_label = QLabel("母亲 X 等位基因：")
        mother_label.setStyleSheet(f"color: {COLOR_RECESSIVE}; font-weight: bold;")
        self.sex_mother_combo = QComboBox()
        self.sex_mother_combo.addItems(["X^A X^A", "X^A X^a", "X^a X^a"])
        self.sex_mother_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContentsOnFirstShow)
        self.sex_mother_combo.setMinimumWidth(130)
        mother_row.addWidget(mother_label)
        mother_row.addWidget(self.sex_mother_combo)
        mother_row.addStretch()
        group_layout.addLayout(mother_row)

        father_row = QHBoxLayout()
        father_label = QLabel("父亲 X 等位基因：")
        father_label.setStyleSheet(f"color: {COLOR_DOMINANT}; font-weight: bold;")
        self.sex_father_combo = QComboBox()
        self.sex_father_combo.addItems(["X^A", "X^a"])
        self.sex_father_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContentsOnFirstShow)
        self.sex_father_combo.setMinimumWidth(130)
        father_row.addWidget(father_label)
        father_row.addWidget(self.sex_father_combo)
        father_row.addStretch()
        group_layout.addLayout(father_row)

        layout.addWidget(group)
        layout.addStretch()

        self._input_widgets.extend([self.sex_mother_combo, self.sex_father_combo])
        return page

    def _create_abo_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)

        group = QGroupBox("ABO 血型")
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(10)

        mother_row = QHBoxLayout()
        mother_label = QLabel("母本基因型：")
        mother_label.setStyleSheet(f"color: {COLOR_RECESSIVE}; font-weight: bold;")
        self.abo_mother_combo = QComboBox()
        self.abo_mother_combo.addItems(ABO_GENOTYPES)
        mother_row.addWidget(mother_label)
        mother_row.addWidget(self.abo_mother_combo)
        mother_row.addStretch()
        group_layout.addLayout(mother_row)

        father_row = QHBoxLayout()
        father_label = QLabel("父本基因型：")
        father_label.setStyleSheet(f"color: {COLOR_DOMINANT}; font-weight: bold;")
        self.abo_father_combo = QComboBox()
        self.abo_father_combo.addItems(ABO_GENOTYPES)
        father_row.addWidget(father_label)
        father_row.addWidget(self.abo_father_combo)
        father_row.addStretch()
        group_layout.addLayout(father_row)

        layout.addWidget(group)
        layout.addStretch()

        self._input_widgets.extend([self.abo_mother_combo, self.abo_father_combo])
        return page

    def _create_polygenic_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)

        group = QGroupBox("多基因数量性状")
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(10)

        count_row = QHBoxLayout()
        count_row.addWidget(QLabel("基因数："))
        self.pg_gene_count = QSpinBox()
        self.pg_gene_count.setRange(2, 4)
        self.pg_gene_count.setValue(2)
        self.pg_gene_count.setKeyboardTracking(False)
        self.pg_gene_count.setAccelerated(True)
        self.pg_gene_count.setButtonSymbols(QSpinBox.ButtonSymbols.UpDownArrows)
        count_row.addWidget(self.pg_gene_count)
        count_row.addStretch()
        group_layout.addLayout(count_row)

        base_row = QHBoxLayout()
        base_row.addWidget(QLabel("基准值："))
        self.pg_base = QDoubleSpinBox()
        self.pg_base.setRange(0, 10000)
        self.pg_base.setValue(170.0)
        self.pg_base.setDecimals(1)
        base_row.addWidget(self.pg_base)
        base_row.addStretch()
        group_layout.addLayout(base_row)

        noise_row = QHBoxLayout()
        noise_row.addWidget(QLabel("噪声："))
        self.pg_noise = QDoubleSpinBox()
        self.pg_noise.setRange(0, 1000)
        self.pg_noise.setValue(2.0)
        self.pg_noise.setDecimals(1)
        noise_row.addWidget(self.pg_noise)
        noise_row.addStretch()
        group_layout.addLayout(noise_row)

        layout.addWidget(group)
        layout.addStretch()

        self._input_widgets.extend([self.pg_gene_count, self.pg_base, self.pg_noise])
        return page

    # ── 模式切换 ──

    def switch_mode(self, mode):
        """切换到指定模式页面

        mode: 'classic' | 'multigene' | 'sex' | 'multi_allele' | 'polygenic'
        """
        index_map = {
            "classic": 0,
            "multigene": 1,
            "sex": 2,
            "multi_allele": 3,
            "polygenic": 4,
        }
        idx = index_map.get(mode, 0)
        self.stacked.setCurrentIndex(idx)
        self.current_mode = mode

    def get_params(self):
        """从当前页获取参数，返回 dict"""
        params = {
            "mode": self.current_mode,
            "count": self.get_simulation_count(),
        }
        if self.current_mode == "classic":
            params["female"], params["male"] = self.get_parents()
        elif self.current_mode == "multigene":
            params["gene_count"] = self.mg_gene_count.currentIndex() + 2
            params["gene_pairs"] = [(m.currentText(), f.currentText()) for m, f in self._mg_input_combos]
        elif self.current_mode == "sex":
            params["mother_x"] = self.sex_mother_combo.currentText()
            params["father_x"] = self.sex_father_combo.currentText()
        elif self.current_mode == "multi_allele":
            params["mother_abo"] = self.abo_mother_combo.currentText()
            params["father_abo"] = self.abo_father_combo.currentText()
        elif self.current_mode == "polygenic":
            params["gene_count"] = self.pg_gene_count.value()
            params["base_value"] = self.pg_base.value()
            params["noise"] = self.pg_noise.value()
        return params

    # ── 公开 API（保持向后兼容）──

    def get_parents(self):
        """获取当前经典模式下选择的亲代基因型"""
        return self.female_combo.currentText(), self.male_combo.currentText()

    def get_simulation_count(self):
        """获取模拟次数"""
        return self.count_spin.value()

    def set_running_state(self, running):
        """切换运行/空闲状态"""
        self.run_button.setEnabled(not running)
        self.female_combo.setEnabled(not running)
        self.male_combo.setEnabled(not running)
        self.count_spin.setEnabled(not running)
        self.count_slider.setEnabled(not running)
        for btn in self._preset_buttons:
            btn.setEnabled(not running)
        for w in self._input_widgets:
            w.setEnabled(not running)
        if running:
            self.run_button.setText("模拟中...")
            self.progress_bar.setFormat("运行中...")
        else:
            self.run_button.setText("开始模拟")
            self.progress_bar.setFormat("就绪")

    def update_progress(self, current, total):
        """更新进度条"""
        if total > 0:
            pct = int(current / total * 100)
            self.progress_bar.setValue(pct)
            self.progress_bar.setFormat(f"{pct}% ({current:,}/{total:,})")

    # ── 内部辅助方法 ──

    def _format_number(self, n):
        """格式化大数显示"""
        if n >= 1_000_000:
            return f'{n // 1_000_000}M'
        elif n >= 1_000:
            return f'{n // 1_000}K'
        return str(n)

    def _set_simulations(self, count):
        """预设按钮点击"""
        self.count_spin.setValue(count)

    def _on_spin_changed(self, value):
        """输入框变化 → 滑块同步（对数映射）"""
        import math
        log_val = math.log10(value)
        slider_val = int((log_val - 1) / 6 * 99 + 1)
        self.count_slider.blockSignals(True)
        self.count_slider.setValue(min(max(slider_val, 1), 100))
        self.count_slider.blockSignals(False)

    def _on_slider_changed(self, value):
        """滑块变化 → 输入框同步（对数映射）"""
        log_val = (value - 1) / 99 * 6 + 1
        count = int(10 ** log_val)
        if count < 100:
            count = (count // 10) * 10
        elif count < 1000:
            count = (count // 50) * 50
        elif count < 10000:
            count = (count // 500) * 500
        elif count < 100000:
            count = (count // 5000) * 5000
        elif count < 1000000:
            count = (count // 50000) * 50000
        else:
            count = (count // 500000) * 500000
        count = max(10, min(count, 10_000_000))
        self.count_spin.blockSignals(True)
        self.count_spin.setValue(count)
        self.count_spin.blockSignals(False)
