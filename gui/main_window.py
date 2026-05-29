"""主窗口 — 侧边控制栏 + 右侧双标签统计面板 (v2.0 多模式)"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QTabWidget, QTextEdit, QStatusBar, QLabel, QSplitter, QStackedWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from config import (
    COLOR_BG_MAIN, COLOR_BG_PANEL, COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY, COLOR_DOMINANT, COLOR_THEORY_LINE,
    COLOR_RECESSIVE,
    MODE_DESCRIPTIONS,
)
from gui.mode_selector import ModeSelector
from gui.control_panel import ControlPanel
from gui.chart_widget import (
    BarChartCanvas, ConvergenceCanvas,
    HeatmapCanvas, GroupedBarCanvas, PieChartCanvas, HistogramCanvas,
    DiseasePunnettCanvas,
)
from core.worker_thread import SimulationWorker


class MainWindow(QMainWindow):
    """超级孟德尔基因大数对决数字实验室 — 主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("超级孟德尔 — 基因大数对决实验室")
        self.setMinimumSize(1100, 700)
        self.resize(1280, 800)
        self.worker = None
        self._init_ui()
        self._apply_styles()

    def _init_ui(self):
        """初始化 UI 布局"""
        central = QWidget()
        self.setCentralWidget(central)

        # 水平分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)

        # ── 顶部：遗传模式下拉框 ──
        self.mode_selector = ModeSelector()

        # ── 左侧：控制面板 ──
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)

        self.control_panel = ControlPanel()
        left_layout.addWidget(self.control_panel)

        splitter.addWidget(left_widget)

        # ── 右侧：Tab 区域 ──
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(8, 8, 8, 8)
        right_layout.setSpacing(8)

        self.tab_widget = QTabWidget()

        # 图表区改用 QStackedWidget — 每个模式一页
        self.chart_stack = QStackedWidget()

        # 经典模式页 (bar + convergence)
        classic_page = QWidget()
        classic_layout = QVBoxLayout(classic_page)
        classic_layout.setSpacing(4)
        self.bar_chart = BarChartCanvas()
        self.convergence_chart = ConvergenceCanvas()
        classic_layout.addWidget(self.bar_chart)
        classic_layout.addWidget(self.convergence_chart)
        self.chart_stack.addWidget(classic_page)

        # 多基因页 (heatmap)
        multigene_page = QWidget()
        multigene_layout = QVBoxLayout(multigene_page)
        multigene_layout.setSpacing(8)
        self.heatmap_canvas = HeatmapCanvas()
        multigene_layout.addStretch()
        multigene_layout.addWidget(self.heatmap_canvas)
        self.chart_stack.addWidget(multigene_page)

        # 性染色体页 (grouped_bar)
        sex_page = QWidget()
        sex_layout = QVBoxLayout(sex_page)
        sex_layout.setSpacing(8)
        self.grouped_bar_canvas = GroupedBarCanvas()
        sex_layout.addStretch()
        sex_layout.addWidget(self.grouped_bar_canvas)
        self.chart_stack.addWidget(sex_page)

        # ABO页 (pie)
        abo_page = QWidget()
        abo_layout = QVBoxLayout(abo_page)
        abo_layout.setSpacing(8)
        self.pie_chart_canvas = PieChartCanvas()
        abo_layout.addStretch()
        abo_layout.addWidget(self.pie_chart_canvas)
        self.chart_stack.addWidget(abo_page)

        # 数量性状页 (histogram)
        polygenic_page = QWidget()
        polygenic_layout = QVBoxLayout(polygenic_page)
        self.histogram_canvas = HistogramCanvas()
        polygenic_layout.addStretch()
        polygenic_layout.addWidget(self.histogram_canvas)
        self.chart_stack.addWidget(polygenic_page)

        # 疾病页 (Punnett + stats)
        disease_page = QWidget()
        disease_layout = QVBoxLayout(disease_page)
        disease_layout.setSpacing(8)

        class StatsCanvas(FigureCanvas):
            def __init__(self, parent=None, width=7, height=3, dpi=100):
                self.fig = Figure(figsize=(width, height), dpi=dpi)
                self.ax = self.fig.add_subplot(111)
                super().__init__(self.fig)
                self.fig.subplots_adjust(left=0.12, right=0.95, top=0.85, bottom=0.2)
                self.setParent(parent)

            def plot_disease_stats(self, report):
                self.ax.clear()
                sim = report.get("sim_data", {})
                if not sim:
                    self.ax.text(0.5, 0.5, "暂无统计数据", ha='center', va='center')
                    self.draw()
                    return

                total = sim.get("总模拟次数", 1)
                if "基因型分布" in sim:
                    categories = list(sim["基因型分布"].keys())
                    values = [v / total * 100 for v in sim["基因型分布"].values()]
                else:
                    keys = ["女儿正常","女儿携带","女儿患病","儿子正常","儿子患病"]
                    categories = [k for k in keys if k in sim]
                    values = [sim[k] / total * 100 for k in categories]

                colors = [COLOR_RECESSIVE if '患病' in k else COLOR_DOMINANT if '正常' in k else COLOR_THEORY_LINE for k in categories]

                bars = self.ax.bar(categories, values, color=colors, alpha=0.85, edgecolor='white', lw=1.2, width=0.5)
                for bar, val in zip(bars, values):
                    self.ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+1, f'{val:.1f}%', ha='center', fontsize=10, fontweight='bold')
                self.ax.set_ylabel('百分比 (%)')
                self.ax.set_ylim(0, max(values) + 15)
                self.ax.set_title(f'子代风险分析 — {report.get("disease_name","")}', fontweight='bold', fontsize=11, color=COLOR_TEXT_PRIMARY, pad=10)
                self.draw()

        self.disease_punnett_canvas = DiseasePunnettCanvas(width=4.5, height=4)
        disease_layout.addWidget(self.disease_punnett_canvas)

        self.disease_stats_canvas = StatsCanvas()
        disease_layout.addWidget(self.disease_stats_canvas)
        disease_layout.addStretch()
        self.chart_stack.addWidget(disease_page)

        self.tab_widget.addTab(self.chart_stack, "📊 实时图表")

        # Tab 2：文本报告
        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        self.report_text.setFont(QFont("Consolas", 10))
        self.report_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLOR_BG_PANEL};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid #e2e8f0;
                border-radius: 4px;
                padding: 12px;
            }}
        """)
        self.tab_widget.addTab(self.report_text, "📋 统计报告")

        # Tab 3：模式说明
        self.help_text = QTextEdit()
        self.help_text.setReadOnly(True)
        self.help_text.setFont(QFont("Microsoft YaHei", 11))
        self.help_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLOR_BG_PANEL};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid #e2e8f0;
                border-radius: 4px;
                padding: 16px;
            }}
        """)
        self.tab_widget.addTab(self.help_text, "📖 说明")
        self.help_text.setPlainText(MODE_DESCRIPTIONS["classic"])

        right_layout.addWidget(self.tab_widget)

        # ── 状态标签 ──
        self.status_label = QLabel("就绪 — 请选择参数并开始模拟")
        self.status_label.setStyleSheet(f"""
            color: {COLOR_TEXT_SECONDARY};
            font-size: 12px;
            padding: 8px;
            background-color: {COLOR_BG_PANEL};
            border-radius: 4px;
        """)
        right_layout.addWidget(self.status_label)

        splitter.addWidget(right_widget)
        splitter.setSizes([280, 1000])

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)
        main_layout.addWidget(self.mode_selector)

        # ── 顶部提示条 ──
        self.tip_label = QLabel(MODE_DESCRIPTIONS["classic"])
        self.tip_label.setStyleSheet(f"""
            color: {COLOR_TEXT_SECONDARY};
            font-size: 11px;
            padding: 4px 8px;
            background-color: {COLOR_BG_PANEL};
            border-radius: 4px;
        """)
        self.tip_label.setWordWrap(True)
        main_layout.addWidget(self.tip_label)

        main_layout.addWidget(splitter)

        # ── 状态栏 ──
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("欢迎使用超级孟德尔基因大数对决数字实验室")

        # ── 信号连接 ──
        self.control_panel.run_button.clicked.connect(self._start_simulation)
        self.mode_selector.mode_changed.connect(self.control_panel.switch_mode)
        self.mode_selector.mode_changed.connect(self._on_mode_changed)

    def _on_mode_changed(self, mode):
        """模式切换时更新提示条、说明页和图表区"""
        desc = MODE_DESCRIPTIONS.get(mode, "")
        self.tip_label.setText(desc)
        self.help_text.setPlainText(desc)
        mode_pages = {"classic": 0, "multigene": 1, "sex": 2, "multi_allele": 3, "polygenic": 4, "disease": 5}
        self.chart_stack.setCurrentIndex(mode_pages.get(mode, 0))

    def _apply_styles(self):
        """应用全局样式"""
        from config import GLOBAL_QSS
        self.setStyleSheet(GLOBAL_QSS)

    def _start_simulation(self):
        """启动模拟计算 (v2.0 多模式)"""
        params = self.control_panel.get_params()
        mode = params["mode"]
        count = params["count"]

        # 转化参数 key 名以匹配 Worker 内部约定
        worker_params = {"num_simulations": count}
        status_info = ""

        if mode == "classic":
            worker_params["parent1"] = params["female"]
            worker_params["parent2"] = params["male"]
            status_info = f"{params['female']} × {params['male']}"
        elif mode == "multigene":
            pairs = params.get("gene_pairs", [])
            worker_params["parent1_gtypes"] = [p[0] for p in pairs]
            worker_params["parent2_gtypes"] = [p[1] for p in pairs]
            status_info = f"多基因 ({len(pairs)} 基因)"
        elif mode == "sex":
            worker_params["mother_X"] = params["mother_x"]
            worker_params["father_X"] = params["father_x"]
            status_info = f"X 连锁 ({params['mother_x']} × {params['father_x']})"
        elif mode == "multi_allele":
            worker_params["parent1_genotype"] = params["mother_abo"]
            worker_params["parent2_genotype"] = params["father_abo"]
            status_info = f"ABO ({params['mother_abo']} × {params['father_abo']})"
        elif mode == "polygenic":
            if "base_value" not in params or "noise" not in params:
                return  # 参数解析失败（float 转换错误），get_params 已弹窗
            gene_n = params["gene_count"]
            worker_params["num_genes"] = gene_n
            worker_params["parent1_gtypes"] = ["Aa"] * gene_n
            worker_params["parent2_gtypes"] = ["Aa"] * gene_n
            worker_params["base_value"] = params["base_value"]
            worker_params["noise_std"] = params["noise"]
            worker_params["effects"] = None
            status_info = f"数量性状 ({gene_n} 基因)"
        elif mode == "disease":
            worker_params["disease_name"] = params["disease_name"]
            worker_params["inheritance"] = params.get("inheritance", "")
            worker_params["disease_params"] = params["disease_params"]
            status_info = f"疾病模拟 ({params['disease_name']})"

        # 设置运行状态
        self.control_panel.set_running_state(True)
        self.mode_selector.setEnabled(False)
        self.status_label.setText(
            f"运行中：{status_info} | {count:,} 次模拟..."
        )
        self.status_label.setStyleSheet(f"""
            color: {COLOR_DOMINANT};
            font-size: 12px;
            font-weight: bold;
            padding: 8px;
            background-color: {COLOR_BG_PANEL};
            border-radius: 4px;
        """)
        self.status_bar.showMessage(
            f"正在模拟 {count:,} 次… ({status_info})"
        )

        self.report_text.clear()
        self.report_text.append("⏳ 模拟进行中...")

        # 创建并启动工作线程
        self.worker = SimulationWorker(mode=mode, params=worker_params)
        self.worker.progress_updated.connect(self._on_progress)
        self.worker.simulation_finished.connect(self._on_finished)
        self.worker.simulation_error.connect(self._on_error)
        self.worker.start()

    def _on_progress(self, current, total):
        """进度更新槽函数"""
        self.control_panel.update_progress(current, total)

    def _on_finished(self, report):
        """计算完成槽函数 (v2.0 多模式)"""
        self.control_panel.set_running_state(False)
        self.mode_selector.setEnabled(True)
        mode = report.get("mode", "classic")
        total = report["total_simulations"]

        mode_pages = {"classic": 0, "multigene": 1, "sex": 2, "multi_allele": 3, "polygenic": 4, "disease": 5}
        page_idx = mode_pages.get(mode, 0)
        self.chart_stack.setCurrentIndex(page_idx)

        # ── 根据模式绘制对应图表 ──
        if mode == "classic":
            self.bar_chart.plot_results(
                report["phenotype_counts"],
                report["phenotype_ratios"],
                theory_dominant=report["theory_dominant"],
                theory_recessive=report["theory_recessive"],
                parent1=report["parent1"],
                parent2=report["parent2"],
            )
            self.convergence_chart.plot_convergence(
                report["convergence_x"],
                report["convergence_y"],
                report["total_simulations"],
                theory_ratio=report["theory_dominant"],
                parent1=report["parent1"],
                parent2=report["parent2"],
            )

        elif mode == "multigene":
            result_dict = report.get("result_dict", {})
            if result_dict:
                self.heatmap_canvas.plot_heatmap(result_dict)
            pairs = report.get("gene_pairs", [("Aa", "Aa")])
            a1, a2 = list(pairs[0][0]), list(pairs[0][1])

        elif mode == "sex":
            self.grouped_bar_canvas.plot_sex_linked(
                report.get("daughter_stats", {}),
                report.get("son_stats", {}),
            )
            mother = report.get("mother_X", "X^C X^c").split()
            father = [report.get("father_X", "X^C"), "Y"]

        elif mode == "multi_allele":
            self.pie_chart_canvas.plot_abo(
                report.get("phenotype_counts", {}),
            )
            p1 = report.get("parent1_genotype", ["I^A", "i"])
            p2 = report.get("parent2_genotype", ["I^B", "i"])

        elif mode == "polygenic":
            self.histogram_canvas.plot_histogram(
                report.get("values", []),
                report.get("fit_mean", 0),
                report.get("fit_std", 1),
            )

        elif mode == "disease":
            self.disease_punnett_canvas.plot_disease_punnett(report)
            self.disease_stats_canvas.plot_disease_stats(report)

        # ── 生成文本报告 ──
        self._generate_text_report(report)

        # ── 状态 ──
        if mode == "classic":
            status_text = (
                f"完成：{report['parent1']} × {report['parent2']} | "
                f"{total:,} 次杂交秒级完成"
            )
        else:
            mode_names = {
                "multigene": "多基因杂交",
                "sex": "性染色体遗传",
                "multi_allele": "ABO 血型",
                "polygenic": "多基因数量性状",
            }
            name = mode_names.get(mode, mode)
            status_text = f"完成：{name} | {total:,} 次模拟完成"

        self.status_label.setText(status_text)
        self.status_label.setStyleSheet(f"""
            color: {COLOR_THEORY_LINE};
            font-size: 12px;
            font-weight: bold;
            padding: 8px;
            background-color: {COLOR_BG_PANEL};
            border-radius: 4px;
        """)
        self.status_bar.showMessage(
            f"模拟完成：{total:,} 次处理成功"
        )

        # 切换到图表 Tab
        self.tab_widget.setCurrentIndex(0)

    def _on_error(self, error_msg):
        """错误处理"""
        self.control_panel.set_running_state(False)
        self.mode_selector.setEnabled(True)
        self.status_label.setText(f"错误：{error_msg}")
        self.status_label.setStyleSheet("""
            color: #dc2626;
            font-size: 12px;
            font-weight: bold;
            padding: 8px;
            background-color: #fef2f2;
            border-radius: 4px;
        """)
        self.report_text.setHtml(
            f'<h3 style="color:red;">模拟出错</h3>'
            f'<pre>{error_msg}</pre>'
        )
        self.status_bar.showMessage("模拟失败！")

    def _generate_text_report(self, report):
        """生成格式化的文本报告 (v2.0 多模式)"""
        mode = report.get("mode", "classic")

        if mode == "classic":
            self._generate_classic_report(report)
        elif mode == "multigene":
            self._generate_multigene_report(report)
        elif mode == "sex":
            self._generate_sex_report(report)
        elif mode == "multi_allele":
            self._generate_abo_report(report)
        elif mode == "polygenic":
            self._generate_polygenic_report(report)
        elif mode == "disease":
            self._generate_disease_report(report)
        else:
            self._generate_classic_report(report)

    # ── 各模式报告生成器 ──

    def _generate_classic_report(self, report):
        """经典单基因孟德尔报告 (v1.0 兼容)"""
        lines = []
        lines.append("╔══════════════════════════════════════════════════╗")
        lines.append("║     超级孟德尔 — 基因大数对决实验室           ║")
        lines.append("╚══════════════════════════════════════════════════╝")
        lines.append("")
        lines.append("━" * 50)
        lines.append("  实验参数")
        lines.append("━" * 50)
        lines.append(f"  母本基因型：  {report['parent1']}")
        lines.append(f"  父本基因型：  {report['parent2']}")
        lines.append(f"  杂交总次数：  {report['total_simulations']:,}")
        lines.append("")
        lines.append("━" * 50)
        lines.append("  基因型结果 (AA : Aa : aa)")
        lines.append("━" * 50)
        g_counts = report['genotype_counts']
        g_ratios = report['genotype_ratios']
        g_dev = report['genotype_deviation_pct']
        lines.append(f"  AA:  {g_counts['AA']:>10,}  ({g_ratios['AA']:.4f} = {g_ratios['AA']*100:.2f}%)  "
                     f"偏离：{g_dev['AA']:+.2f}pp")
        lines.append(f"  Aa:  {g_counts['Aa']:>10,}  ({g_ratios['Aa']:.4f} = {g_ratios['Aa']*100:.2f}%)  "
                     f"偏离：{g_dev['Aa']:+.2f}pp")
        lines.append(f"  aa:  {g_counts['aa']:>10,}  ({g_ratios['aa']:.4f} = {g_ratios['aa']*100:.2f}%)  "
                     f"偏离：{g_dev['aa']:+.2f}pp")
        lines.append("")
        t_g = report["theory_genotype"]
        lines.append(f"  理论值：AA={t_g['AA']*100:.0f}%  Aa={t_g['Aa']*100:.0f}%  aa={t_g['aa']*100:.0f}%")
        lines.append("")
        lines.append("━" * 50)
        lines.append("  表现型结果 (显性 : 隐性)")
        lines.append("━" * 50)
        p_counts = report['phenotype_counts']
        p_ratios = report['phenotype_ratios']
        p_dev = report['phenotype_deviation_pct']
        lines.append(f"  显性：  {p_counts['显性']:>10,}  ({p_ratios['显性']:.4f} = {p_ratios['显性']*100:.2f}%)  "
                     f"偏离：{p_dev['显性']:+.2f}pp")
        lines.append(f"  隐性：  {p_counts['隐性']:>10,}  ({p_ratios['隐性']:.4f} = {p_ratios['隐性']*100:.2f}%)  "
                     f"偏离：{p_dev['隐性']:+.2f}pp")
        lines.append("")
        t_d = report["theory_dominant"]
        t_r = report["theory_recessive"]
        lines.append(f"  理论值：显性={t_d*100:.1f}%  隐性={t_r*100:.1f}%")
        lines.append("")
        lines.append("━" * 50)
        lines.append("  卡方拟合优度检验")
        lines.append("━" * 50)
        lines.append(f"  χ² = {report['chi2_statistic']:.3f}")
        lines.append(f"  判定：{report['chi2_verdict']}")
        lines.append("")

        # 大数定律观察
        lines.append("━" * 50)
        lines.append("  大数定律观察")
        lines.append("━" * 50)
        if report['total_simulations'] >= 10000:
            dom_pct = report['phenotype_ratios']['显性'] * 100
            theory_dom_pct = report['theory_dominant'] * 100
            if abs(dom_pct - theory_dom_pct) < 1.0:
                lines.append(f"  ✅ 强收敛！显性比例 ({dom_pct:.2f}%)")
                lines.append(f"     在孟德尔理论预测值 ({theory_dom_pct:.2f}%) 的 1% 范围内。")
            else:
                lines.append(f"  ⚠️ 轻微偏离：显性比例 ({dom_pct:.2f}%)")
                lines.append(f"     (理论值: {theory_dom_pct:.2f}%) 增加杂交次数可观察更强的收敛效果。")
        else:
            lines.append(f"  🔬 样本量较小（{report['total_simulations']:,} 次）。")
            lines.append(f"     建议增加到 10 万次以上可观察强收敛。")
        lines.append("")
        lines.append("━" * 50)

        self.report_text.clear()
        self.report_text.append('\n'.join(lines))

    def _generate_multigene_report(self, report):
        """多基因独立分配报告"""
        lines = []
        lines.append("╔══════════════════════════════════════════════════╗")
        lines.append("║     超级孟德尔 — 多基因独立分配               ║")
        lines.append("╚══════════════════════════════════════════════════╝")
        lines.append("")
        lines.append(f"  模拟次数：{report['total_simulations']:,}")
        lines.append(f"  基因型种类数：{report.get('total_genotypes', 'N/A')}")
        lines.append("")
        lines.append("━" * 50)
        lines.append("  各基因独立比例")
        lines.append("━" * 50)
        per_gene = report.get("per_gene_breakdown", {})
        for gene_key in sorted(per_gene.keys()):
            gene_info = per_gene[gene_key]
            label = gene_key.replace("gene_", "基因 ")
            lines.append(f"  [{label}] 亲本: {gene_info.get('parental', '')}")
            ratios = gene_info.get("ratios", {})
            counts = gene_info.get("counts", {})
            for gt in sorted(ratios.keys()):
                r = ratios[gt]
                c = counts.get(gt, 0)
                lines.append(f"    {gt}: {c:,} ({r*100:.1f}%)")
            lines.append("")
        lines.append("━" * 50)

        self.report_text.clear()
        self.report_text.append('\n'.join(lines))

    def _generate_sex_report(self, report):
        """性染色体 X 连锁报告"""
        lines = []
        lines.append("╔══════════════════════════════════════════════════╗")
        lines.append("║     超级孟德尔 — X 连锁遗传                   ║")
        lines.append("╚══════════════════════════════════════════════════╝")
        lines.append("")
        lines.append(f"  模拟次数：{report['total_simulations']:,}")
        lines.append(f"  女儿数：{report.get('daughter_count', 0):,}")
        lines.append(f"  儿子数：{report.get('son_count', 0):,}")
        lines.append("")
        lines.append("━" * 50)
        lines.append("  女儿统计")
        lines.append("━" * 50)
        for k, v in report.get("daughter_stats", {}).items():
            lines.append(f"  {k}: {v}")
        lines.append("")
        lines.append("━" * 50)
        lines.append("  儿子统计")
        lines.append("━" * 50)
        for k, v in report.get("son_stats", {}).items():
            lines.append(f"  {k}: {v}")
        lines.append("")
        lines.append("━" * 50)

        self.report_text.clear()
        self.report_text.append('\n'.join(lines))

    def _generate_abo_report(self, report):
        """ABO 血型四分类报告"""
        lines = []
        lines.append("╔══════════════════════════════════════════════════╗")
        lines.append("║     超级孟德尔 — ABO 血型遗传                 ║")
        lines.append("╚══════════════════════════════════════════════════╝")
        lines.append("")
        lines.append(f"  模拟次数：{report['total_simulations']:,}")
        lines.append("")
        lines.append("━" * 50)
        lines.append("  血型分布")
        lines.append("━" * 50)
        p_counts = report.get("phenotype_counts", {})
        ratios = report.get("ratios", {})
        for pt in ["A型", "B型", "AB型", "O型"]:
            c = p_counts.get(pt, 0)
            r = ratios.get(pt, 0) * 100
            lines.append(f"  {pt}: {c:,} ({r:.1f}%)")
        lines.append("")
        lines.append("━" * 50)

        self.report_text.clear()
        self.report_text.append('\n'.join(lines))

    def _generate_polygenic_report(self, report):
        """多基因数量性状报告"""
        lines = []
        lines.append("╔══════════════════════════════════════════════════╗")
        lines.append("║     超级孟德尔 — 多基因数量性状               ║")
        lines.append("╚══════════════════════════════════════════════════╝")
        lines.append("")
        lines.append(f"  模拟次数：{report['total_simulations']:,}")
        lines.append("")
        lines.append("━" * 50)
        lines.append("  统计量")
        lines.append("━" * 50)
        lines.append(f"  均值 (mean):     {report.get('mean', 'N/A')}")
        lines.append(f"  标准差 (std):     {report.get('std', 'N/A')}")
        lines.append(f"  最小值 (min):     {report.get('min', 'N/A')}")
        lines.append(f"  最大值 (max):     {report.get('max', 'N/A')}")
        lines.append(f"  中位数 (median):  {report.get('median', 'N/A')}")
        lines.append("")
        lines.append("━" * 50)
        lines.append("  正态拟合")
        lines.append("━" * 50)
        fit_mu = report.get("fit_mean", "N/A")
        fit_sigma = report.get("fit_std", "N/A")
        lines.append(f"  拟合 μ: {fit_mu}")
        lines.append(f"  拟合 σ: {fit_sigma}")
        skew = report.get("skewness", None)
        kurt = report.get("kurtosis", None)
        if skew is not None:
            lines.append(f"  偏度 (skewness): {skew:.4f}")
        if kurt is not None:
            lines.append(f"  峰度 (kurtosis): {kurt:.4f}")
        lines.append("")
        lines.append("━" * 50)

        self.report_text.clear()
        self.report_text.append('\n'.join(lines))

    def _generate_disease_report(self, report):
        self.report_text.clear()
        pedigree = report.get("pedigree_report", "")
        self.report_text.setFont(QFont("Consolas", 10))
        self.report_text.append(pedigree)

        # 追加模拟数据
        sim = report.get("sim_data", {})
        if sim:
            self.report_text.append("\n")
            self.report_text.append("━" * 50)
            if "基因型分布" in sim:
                for k, v in sim["基因型分布"].items():
                    pct = v / sim["总模拟次数"] * 100
                    self.report_text.append(f"  {k}: {v} ({pct:.1f}%)")
            elif "女儿正常" in sim:
                total = sim["总模拟次数"]
                for key in ["女儿正常","女儿携带","女儿患病","儿子正常","儿子患病"]:
                    if key in sim:
                        pct = sim[key] / total * 100
                        self.report_text.append(f"  {key}: {sim[key]} ({pct:.1f}%)")

    def closeEvent(self, event):
        """窗口关闭时确保工作线程终止"""
        if self.worker and self.worker.isRunning():
            self.worker.quit()
            self.worker.wait(2000)
        event.accept()
