"""封装 Matplotlib 画布，用于无闪烁渲染统计报表"""

import matplotlib
matplotlib.use('QtAgg')  # PyQt6 后端

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import seaborn as sns

from config import (
    COLOR_DOMINANT, COLOR_RECESSIVE, COLOR_THEORY_LINE,
    COLOR_TEXT_PRIMARY, CHART_DPI
)

# 设置 seaborn 风格
sns.set_style("whitegrid")
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 11

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题


class BarChartCanvas(FigureCanvas):
    """表现型柱状图 + 理论参考线"""

    def __init__(self, parent=None, width=6, height=4, dpi=CHART_DPI):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.fig.subplots_adjust(left=0.12, right=0.95, top=0.9, bottom=0.15)
        self.setParent(parent)
        self.setMaximumHeight(320)
        self.draw()

    def plot_results(self, phenotype_counts, phenotype_ratios,
                     theory_dominant=0.75, theory_recessive=0.25,
                     parent1='Aa', parent2='Aa'):
        """
        绘制柱状图。

        参数：
            phenotype_counts: {"显性": N, "隐性": N}
            phenotype_ratios: {"显性": ratio, "隐性": ratio}
            theory_dominant: 显性理论比例
            theory_recessive: 隐性理论比例
            parent1, parent2: 亲本基因型
        """
        self.ax.clear()

        categories = ['显性\n(AA + Aa)', '隐性\n(aa)']
        actual_pcts = [
            phenotype_ratios["显性"] * 100,
            phenotype_ratios["隐性"] * 100
        ]
        theory_pcts = [theory_dominant * 100, theory_recessive * 100]
        colors = [COLOR_DOMINANT, COLOR_RECESSIVE]

        # 柱状图
        bars = self.ax.bar(categories, actual_pcts, color=colors,
                           alpha=0.85, edgecolor='white', linewidth=1.2,
                           width=0.5)

        # 数值标签
        for bar, pct in zip(bars, actual_pcts):
            height = bar.get_height()
            self.ax.text(bar.get_x() + bar.get_width() / 2., height + 1,
                         f'{pct:.1f}%', ha='center', va='bottom',
                         fontsize=12, fontweight='bold',
                         color=COLOR_TEXT_PRIMARY)

        # 理论线
        for i, theory_pct in enumerate(theory_pcts):
            self.ax.axhline(y=theory_pct, color=COLOR_THEORY_LINE,
                            linestyle='--', linewidth=2, alpha=0.8)
            self.ax.text(len(categories) - 0.5, theory_pct + 1,
                         f'理论值: {theory_pct:.0f}%',
                         fontsize=9, color=COLOR_THEORY_LINE,
                         fontstyle='italic')

        self.ax.set_ylim(0, max(100, max(theory_pcts) + 15))
        self.ax.set_ylabel('占比 (%)')
        self.ax.set_title(f'表现型分布 vs 孟德尔理论值\n({parent1} × {parent2})',
                          fontweight='bold', color=COLOR_TEXT_PRIMARY,
                          pad=15)

        # 图例
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor=COLOR_DOMINANT, alpha=0.85, label='显性'),
            Patch(facecolor=COLOR_RECESSIVE, alpha=0.85, label='隐性'),
            Patch(facecolor='none', edgecolor=COLOR_THEORY_LINE,
                  label=f'理论值 ({theory_dominant*100:.0f}% / {theory_recessive*100:.0f}%)',
                  hatch='', linestyle='--')
        ]
        self.ax.legend(handles=legend_elements, loc='upper right',
                       fontsize=9, framealpha=0.9)

        self.draw()


class ConvergenceCanvas(FigureCanvas):
    """大数定律收敛折线图"""

    def __init__(self, parent=None, width=6, height=4, dpi=CHART_DPI):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.fig.subplots_adjust(left=0.12, right=0.95, top=0.9, bottom=0.15)
        self.setParent(parent)
        self.setMaximumHeight(320)
        self.draw()

    def plot_convergence(self, x_data, y_data, total_simulations,
                         theory_ratio=0.75, parent1='Aa', parent2='Aa'):
        """
        绘制收敛折线图。

        参数：
            x_data: 实验次数序列（已抽稀）
            y_data: 累计显性比例序列
            total_simulations: 总模拟次数
            theory_ratio: 显性理论比例
            parent1, parent2: 亲本基因型
        """
        self.ax.clear()

        # 主折线：显性比例演化
        self.ax.plot(x_data, y_data, color=COLOR_DOMINANT,
                     linewidth=1.2, alpha=0.85, label='观测比例')

        # 理论参考线
        self.ax.axhline(y=theory_ratio, color=COLOR_THEORY_LINE,
                        linestyle='--', linewidth=2,
                        alpha=0.8, label=f'理论值 ({theory_ratio:.2f})')

        # 填充不确定性区域（±5% 带宽）
        self.ax.axhspan(theory_ratio - 0.05, theory_ratio + 0.05,
                         alpha=0.08, color=COLOR_DOMINANT)

        self.ax.set_xlabel('杂交次数', fontsize=11)
        self.ax.set_ylabel('显性表现型比例', fontsize=11)
        self.ax.set_title(
            f'大数定律：显性比例收敛过程 '
            f'(n={total_simulations:,}) '
            f'({parent1} × {parent2})',
            fontweight='bold', color=COLOR_TEXT_PRIMARY, pad=15
        )

        y_min = max(0, theory_ratio - 0.55)
        y_max = min(1.05, theory_ratio + 0.55)
        self.ax.set_ylim(y_min, y_max)
        self.ax.legend(loc='lower right', fontsize=9, framealpha=0.9)

        # 标注起始位置和最终值
        self.ax.annotate(f'起始: {y_data[0]:.3f}',
                         xy=(x_data[0], y_data[0]),
                         xytext=(x_data[0], y_data[0] + 0.08),
                         fontsize=8, color=COLOR_TEXT_PRIMARY,
                         arrowprops=dict(arrowstyle='->', color='gray', lw=0.8))

        self.ax.annotate(f'理论值: {theory_ratio:.4f}',
                         xy=(x_data[-1], y_data[-1]),
                         xytext=(x_data[-1] * 0.7, y_data[-1] - 0.05),
                         fontsize=9, fontweight='bold',
                         color=COLOR_DOMINANT,
                         arrowprops=dict(arrowstyle='->',
                                         color=COLOR_DOMINANT, lw=1.0))

        self.draw()


# ══════════════════════════════════════════════
# v2.0 新增图表类型
# ══════════════════════════════════════════════

import numpy as np


class HeatmapCanvas(FigureCanvas):
    """二因子基因型分布热力图"""

    def __init__(self, parent=None, width=6, height=5, dpi=CHART_DPI):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.fig.subplots_adjust(left=0.12, right=0.95, top=0.9, bottom=0.15)
        self.setParent(parent)
        self.setMaximumHeight(320)
        self._cbar = None

    def plot_heatmap(self, result_dict, gene_a_label="A", gene_b_label="B"):
        """将多基因结果转为 2D 矩阵绘制热力图"""
        # 清除旧 colorbar（避免叠加）
        if self._cbar is not None:
            self._cbar.remove()
            self._cbar = None
        self.ax.clear()
        rows = set()
        cols = set()
        for key in result_dict:
            parts = key.split("|")
            if len(parts) >= 2:
                rows.add(parts[0])
                cols.add(parts[1])

        rows = sorted(rows)
        cols = sorted(cols)
        matrix = np.zeros((len(rows), len(cols)))
        for key, count in result_dict.items():
            parts = key.split("|")
            if len(parts) >= 2:
                i = rows.index(parts[0])
                j = cols.index(parts[1])
                matrix[i, j] = count

        im = self.ax.imshow(matrix, cmap='Blues', aspect='auto')
        self._cbar = self.fig.colorbar(im, ax=self.ax, label='Count')
        self.ax.set_xticks(range(len(cols)))
        self.ax.set_xticklabels(cols)
        self.ax.set_yticks(range(len(rows)))
        self.ax.set_yticklabels(rows)
        self.ax.set_xlabel(f'Gene {gene_b_label}')
        self.ax.set_ylabel(f'Gene {gene_a_label}')
        self.ax.set_title(f'二因子基因型分布热力图 ({gene_a_label} x {gene_b_label})',
                         fontweight='bold', color=COLOR_TEXT_PRIMARY)

        # 数值标注
        for i in range(len(rows)):
            for j in range(len(cols)):
                val = int(matrix[i, j])
                if val > 0:
                    color = 'white' if matrix[i, j] > matrix.max() * 0.7 else 'black'
                    self.ax.text(j, i, str(val), ha='center', va='center',
                                color=color, fontsize=9)
        self.draw()


class GroupedBarCanvas(FigureCanvas):
    """性染色体按性别分组柱状图"""

    def __init__(self, parent=None, width=6, height=4, dpi=CHART_DPI):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.fig.subplots_adjust(left=0.12, right=0.95, top=0.9, bottom=0.15)
        self.setParent(parent)

    def plot_sex_linked(self, daughter_stats, son_stats):
        self.ax.clear()
        categories = ['正常', '携带者', '患病']
        x = np.arange(len(categories))
        width = 0.35

        d_values = [
            daughter_stats.get('正常', 0),
            daughter_stats.get('携带者', 0),
            daughter_stats.get('患病', 0),
        ]
        s_values = [
            son_stats.get('正常', 0),
            0,  # 儿子无携带者概念
            son_stats.get('患病', 0),
        ]

        bars1 = self.ax.bar(x - width/2, d_values, width, label='女儿',
                           color=COLOR_RECESSIVE, alpha=0.85)
        bars2 = self.ax.bar(x + width/2, s_values, width, label='儿子',
                           color=COLOR_DOMINANT, alpha=0.85)

        self.ax.set_xticks(x)
        self.ax.set_xticklabels(categories)
        self.ax.set_ylabel('人数')
        self.ax.set_title('X 连锁遗传 — 按性别分层', fontweight='bold',
                         color=COLOR_TEXT_PRIMARY)
        self.ax.legend()
        self.draw()


class PieChartCanvas(FigureCanvas):
    """ABO 血型四分类饼图"""

    def __init__(self, parent=None, width=5, height=4, dpi=CHART_DPI):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.fig.subplots_adjust(left=0.12, right=0.95, top=0.9, bottom=0.15)
        self.setParent(parent)

    def plot_abo(self, phenotype_counts):
        self.ax.clear()
        filtered = {k: v for k, v in phenotype_counts.items() if v > 0}
        if not filtered:
            self.ax.text(0.5, 0.5, '无数据', ha='center', va='center', fontsize=14)
            self.ax.set_title('ABO 血型分布', fontweight='bold', color=COLOR_TEXT_PRIMARY)
            self.draw()
            return
        labels = list(filtered.keys())
        sizes = list(filtered.values())
        colors_abo = {'A型': '#ef4444', 'B型': '#3b82f6', 'AB型': '#8b5cf6', 'O型': '#6b7280'}
        colors = [colors_abo[l] for l in labels]
        wedges, _, autotexts = self.ax.pie(
            sizes, labels=None, autopct='%1.1f%%',
            colors=colors, startangle=90,
            pctdistance=0.55, radius=0.75
        )
        self.ax.legend(wedges, labels, loc='lower center',
                       bbox_to_anchor=(0.5, -0.15), ncol=min(len(labels), 2),
                       fontsize=9, framealpha=0.8)
        self.ax.set_title('ABO 血型分布', fontweight='bold', color=COLOR_TEXT_PRIMARY)
        self.fig.subplots_adjust(bottom=0.2)
        self.draw()


class HistogramCanvas(FigureCanvas):
    """多基因性状直方图 + 正态拟合曲线 (纯 NumPy)"""

    def __init__(self, parent=None, width=6, height=4, dpi=CHART_DPI):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.fig.subplots_adjust(left=0.12, right=0.95, top=0.9, bottom=0.15)
        self.setParent(parent)

    def plot_histogram(self, values, mu, sigma):
        self.ax.clear()
        self.ax.hist(values, bins=60, density=True, alpha=0.7,
                    color=COLOR_DOMINANT, edgecolor='white', linewidth=0.5)

        if sigma > 0:
            x = np.linspace(mu - 4*sigma, mu + 4*sigma, 200)
            pdf = (1.0 / (sigma * np.sqrt(2.0 * np.pi))) * \
                  np.exp(-0.5 * ((x - mu) / sigma) ** 2)
            self.ax.plot(x, pdf, color=COLOR_RECESSIVE, linewidth=2.5,
                        label=f'正态拟合 (μ={mu:.1f}, σ={sigma:.1f})')

        self.ax.axvline(mu, color=COLOR_THEORY_LINE, linestyle='--',
                       linewidth=1.5, alpha=0.7, label=f'均值={mu:.1f}')

        self.ax.set_xlabel('性状值')
        self.ax.set_ylabel('概率密度')
        self.ax.set_title('多基因数量性状分布 + 正态拟合', fontweight='bold',
                         color=COLOR_TEXT_PRIMARY)
        self.ax.legend(fontsize=9)
        self.draw()


class PunnettCanvas(FigureCanvas):
    """Punnett 方格可视化 — 配子组合矩阵"""

    def __init__(self, parent=None, width=4.5, height=4, dpi=CHART_DPI):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.fig.subplots_adjust(left=0.12, right=0.95, top=0.9, bottom=0.15)
        self.setParent(parent)

    def plot_punnett(self, parent1_alleles, parent2_alleles, mode="classic"):
        """绘制 Punnett 方格。parent1_alleles: 母本配子列表, parent2_alleles: 父本配子列表"""
        self.ax.clear()
        self.ax.axis('off')

        rows = parent2_alleles  # 父本(行)
        cols = parent1_alleles  # 母本(列)

        cell_text = []
        cell_colors = []
        for r in rows:
            row_text = []
            row_color = []
            for c in cols:
                gt = r + c
                if gt == 'aA':
                    gt = 'Aa'  # 标准化
                row_text.append(gt)
                has_dom = any(ch.isupper() for ch in gt)
                row_color.append(f'{COLOR_DOMINANT}44' if has_dom else f'{COLOR_RECESSIVE}44')
            cell_text.append(row_text)
            cell_colors.append(row_color)

        row_labels = [f'♂ {a}' for a in rows]
        col_labels = [f'♀ {a}' for a in cols]
        table = self.ax.table(
            cellText=cell_text, rowLabels=row_labels, colLabels=col_labels,
            cellLoc='center', loc='center', cellColours=cell_colors
        )
        table.auto_set_font_size(False)
        table.set_fontsize(13)
        table.scale(1, 1.6)

        for key, cell in table.get_celld().items():
            cell.set_edgecolor('#e2e8f0')
            cell.set_linewidth(1)
            if key[0] == 0 or key[1] == -1:
                cell.set_facecolor('#f1f5f9')
                cell.set_text_props(weight='bold', fontsize=11)

        mode_names = {"classic": "经典遗传", "sex": "伴性遗传", "multi_allele": "复等位基因", "multigene": "多基因杂交"}
        self.ax.set_title(f'Punnett 方格 ({mode_names.get(mode, mode)})',
                         fontweight='bold', color=COLOR_TEXT_PRIMARY, pad=15, fontsize=13)
        self.draw()
