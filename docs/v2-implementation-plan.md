# 人类染色体基因推算 v2.0 — 详细开发实施方案（审查修正版）

> **基准**: 设计文档 `docs/human-chromosome-design.md`  
> **基准代码**: `E:\space\mendel_data_lab` (v1.0)  
> **审查**: Claude Code `--effort high` 深度审查  
> **修正**: 3 阻塞项 + 7 遗漏项  
> **总批次**: 10 批 | **新增文件**: 4 | **修改文件**: 6 | **新增代码**: ~1000 行

---

## 🔧 审查修正要点

| 问题 | 严重度 | 修正 |
|------|:---:|------|
| control_panel.py 无修改计划 | 🔴 | 新增批次 9：`QStackedWidget` 动态模式控件栈 |
| 批次顺序倒置（worker 先于 stats） | 🔴 | 重排：引擎(1-5)→统计(6)→线程(7)→图表(8)→面板(9)→主窗口(10) |
| worker_thread API 破坏兼容 | 🔴 | 适配器模式：`SimulationWorker.__init__` 保持旧签名兼容，mode 为可选参数 |
| 基因数无上限 | 🟡 | `polygenic.py` 中 `assert num_genes <= 4` |
| scipy 依赖未声明 | 🟡 | `requirements.txt` 新增 `scipy`，备选纯 NumPy 实现 |
| 报告多模式格式化遗漏 | 🟡 | 批次 6 中 `stats_analyzer.py` 的 `generate_summary_report` 接收 mode 参数 |
| worker 未知 mode 无 fallback | 🟡 | `run()` 中 `dispatchers.get(mode, self._run_classic)` |
| 多基因组合键空格问题 | 🟡 | 基因型键用 `|` 分隔："AA|Bb|CC"，解析时 `split('|')` |

---

## 重排后批次顺序

```
引擎层（独立开发，互不依赖）
  批次1  config.py 扩展 + gui/mode_selector.py
  批次2  core/sex_chromosome.py           ──┐
  批次3  core/multi_allele.py              ─┤ 并行开发
  批次4  crossover_engine.py 多基因扩展     ─┤ 互不依赖
  批次5  core/polygenic.py                ──┘

统计 + 线程层（依赖引擎）
  批次6  core/stats_analyzer.py 多模式统计
  批次7  core/worker_thread.py 多模式 dispatch

UI 层（依赖所有上层）
  批次8  gui/chart_widget.py 新图表类型
  批次9  gui/control_panel.py 模式适配 ★新增
  批次10 gui/main_window.py 最终集成
```

---

## 阶段一：引擎层（批次 1-5）

### 批次 1：config.py 扩展 + gui/mode_selector.py

**目标**：遗传模式常量 + 模式选择器 UI 组件

**文件**：修改 `config.py`、新建 `gui/mode_selector.py`

**config.py 追加内容**：
```python
# ── 遗传模式 ──
GENETIC_MODES = {
    "classic": "单基因孟德尔 (经典)",
    "multigene": "二因子/三因子杂交",
    "sex": "性染色体遗传 (X 连锁)",
    "multi_allele": "复等位基因 (ABO 血型)",
    "polygenic": "多基因数量性状",
}
ABO_GENOTYPES = ["I^A I^A", "I^A i", "I^B I^B", "I^B i", "I^A I^B", "i i"]
ABO_PHENOTYPES = ["A型", "B型", "AB型", "O型"]
X_ALLELES = ["X^A", "X^a"]
MAX_GENES = 4  # 多基因模式上限
```

**gui/mode_selector.py**：`QGroupBox` + 5 个 `QRadioButton`，`mode_changed = pyqtSignal(str)`

**验证**：导入 config 所有新常量 + mode_selector 组件可实例化

---

### 批次 2：core/sex_chromosome.py

**目标**：X/Y 性染色体配子模型 + 半合子统计，纯 NumPy 向量化

**文件**：新建 `core/sex_chromosome.py`（~85 行）

**核心函数**：
```python
def simulate_sex_chromosome_crossover(mother_X, father_X_allele, N):
    """返回 {"女儿": {...}, "儿子": {...}}"""
    # 母亲等概率提供一条 X
    # 父亲：女儿得 X，儿子得 Y (np.where 掩码)
    # 儿子半合子：性状仅由母亲 X 决定
    
def analyze_sex_linked(result, mother, father):
    """按性别分层统计 + 理论值"""
```

**关键测试用例（必须通过）**：

| 亲本组合 | 预期女儿 | 预期儿子 |
|---------|---------|---------|
| X^C X^c × X^C | 100% 正常 | 50% 正常, 50% 患病 |
| X^c X^c × X^C | 100% 携带者 | 100% 患病 |
| X^C X^C × X^c | 100% 携带者 | 100% 正常 |
| X^C X^c × X^c | 50% 携带者, 50% 患病 | 50% 正常, 50% 患病 |

---

### 批次 3：core/multi_allele.py

**目标**：复等位基因引擎 + ABO 表现型映射表

**文件**：新建 `core/multi_allele.py`（~120 行）

**核心函数**：
```python
ABO_PHENOTYPE_MAP = {
    ("I^A","I^A"): "A型", ("I^A","i"): "A型",
    ("I^B","I^B"): "B型", ("I^B","i"): "B型",
    ("I^A","I^B"): "AB型", ("i","i"): "O型",
}

def simulate_abo_crossover(p1_genotype, p2_genotype, N):
    """复用 simulate_crossover_vectorized + 映射表 → 返回 {基因型, 表现型}"""

def analyze_abo_results(result):
    """ABO 四分类卡方检验"""
```

**关键测试用例**：

| 亲本组合 | 预期表现型比 |
|---------|------------|
| I^A i × I^B i | A:B:AB:O = 1:1:1:1 |
| I^A I^B × i i | A:B = 1:1 |
| I^A i × I^A i | A:O = 3:1 |
| I^A I^B × I^A I^B | A:B:AB = 1:1:2 |

---

### 批次 4：crossover_engine.py 多基因扩展

**目标**：新增 `simulate_multigene_crossover()`，`np.column_stack` 向量化合并

**文件**：修改 `core/crossover_engine.py`（追加 ~45 行）

**核心函数**：
```python
def simulate_multigene_crossover(parent1_gtypes, parent2_gtypes, N):
    """
    parent1_gtypes: list[str]，如 ["Aa", "Bb", "CC"]
    返回: dict，键为 "AA|Bb|CC" (用 | 分隔避免空格歧义)
    """
    # 每个基因独立杂交
    # np.column_stack → np.char.add 链式拼接
    # 统计 np.unique
```

**关键设计决策**：基因型组合键用 `|` 分隔而非直接拼接——避免 `"I^A"+"A"` vs `"I^"+"AA"` 的歧义。

**测试**：`AaBb × AaBb` → 9 种基因型，9:3:3:1 表现型比

---

### 批次 5：core/polygenic.py

**目标**：多基因加性效应 + 正态拟合（纯 NumPy 实现，不依赖 scipy）

**文件**：新建 `core/polygenic.py`（~150 行）

**核心函数**：
```python
def simulate_polygenic_trait(num_genes, parent1_gtypes, parent2_gtypes, 
                             effects, base_value, noise_std, N):
    """
    返回: ndarray of trait values (N,)
    """
    assert num_genes <= MAX_GENES, f"最多支持 {MAX_GENES} 个基因"
    # 每个基因独立杂交 → 根据基因型分配效应值 → 累加 → 加噪声
    
def fit_normal(values):
    """纯 NumPy 正态分布参数估计（不依赖 scipy）"""
    mu = np.mean(values)
    sigma = np.std(values, ddof=1)
    return mu, sigma
```

**测试**：5 基因全杂合，效应 [2,1.5,1,0.5,0.3]，10万次模拟 → 均值≈2.65±0.05

---

## 阶段二：统计 + 线程层（批次 6-7）

### 批次 6：core/stats_analyzer.py 多模式统计

**目标**：新增多基因/性染色体/ABO/多基因性状的统计函数，**保持原有函数签名不变**

**文件**：修改 `core/stats_analyzer.py`（新增 ~110 行）

**向后兼容策略**：
- 原 `analyze_genotype_ratios(result, total, parent1, parent2)` 不变
- 新增 `analyze_multigene_ratios(result, total, p1_gtypes, p2_gtypes)`
- 新增 `analyze_sex_linked(result, mother, father)`
- 新增 `analyze_abo_phenotypes(result)`
- 新增 `analyze_polygenic_stats(values)`
- `generate_summary_report` 新增可选 `mode` 参数，默认 "classic"

**注意**：本批次**不修改**已有函数签名——批次 7 的 worker_thread 通过 mode 分发到不同函数，零回归风险。

---

### 批次 7：core/worker_thread.py 多模式 dispatch

**目标**：适配器模式支持 mode，**向后兼容**

**文件**：修改 `core/worker_thread.py`（~40 行增量）

**适配器模式**：
```python
class SimulationWorker(QThread):
    def __init__(self, parent1=None, parent2=None, num_simulations=None, 
                 mode="classic", params=None, parent=None):
        """
        向后兼容：传 parent1, parent2 → 经典模式
        新模式：传 mode + params
        """
        super().__init__(parent)
        self.mode = mode
        if params is None:
            params = {"parent1": parent1, "parent2": parent2, 
                      "num_simulations": num_simulations}
        self.params = params
    
    def run(self):
        dispatchers = {
            "classic": self._run_classic,
            "multigene": self._run_multigene,
            "sex": self._run_sex,
            "multi_allele": self._run_multi_allele,
            "polygenic": self._run_polygenic,
        }
        handler = dispatchers.get(self.mode, self._run_classic)  # fallback
        handler()
```

**关键**：`dispatchers.get(mode, self._run_classic)` 提供未知 mode 降级，避免崩溃。

---

## 阶段三：UI 层（批次 8-10）

### 批次 8：gui/chart_widget.py 新图表类型

**目标**：热力图、分组柱状图、饼图、直方图+正态拟合

**文件**：修改 `gui/chart_widget.py`（新增 4 个 Canvas 类，~130 行）

**新类**：
- `HeatmapCanvas` — Seaborn `heatmap()`，二因子基因型矩阵
- `GroupedBarCanvas` — 按性别分组的柱状图（女儿 vs 儿子）
- `PieChartCanvas` — ABO 四分类环形图
- `HistogramCanvas` — 直方图 + `fit_normal()` 正态曲线叠加

**中文字体**：复用已有的 `rcParams['font.sans-serif']` 配置。

---

### 批次 9：gui/control_panel.py 模式适配 ★ 新增

**目标**：`QStackedWidget` 为每种模式提供不同参数控件页面

**文件**：修改 `gui/control_panel.py`（~60 行增量）

**架构**：
```python
class ControlPanel(QWidget):
    def __init__(self, parent=None):
        self.stack = QStackedWidget()
        self.page_classic = ClassicControlPage()     # 现有控件
        self.page_multigene = MultiGeneControlPage() # 基因数 + 基因型输入
        self.page_sex = SexControlPage()             # X 等位基因选择
        self.page_abo = ABOControlPage()             # ABO 基因型下拉框
        self.page_polygenic = PolygenicControlPage() # 基因数滑块 + 效应
        self.stack.addWidget(self.page_classic)
        # ... 添加所有页面
        
    def switch_mode(self, mode):
        """根据 mode 切换 QStackedWidget 页面"""
        page_map = {"classic": 0, "multigene": 1, "sex": 2, 
                    "multi_allele": 3, "polygenic": 4}
        self.stack.setCurrentIndex(page_map.get(mode, 0))
    
    def get_params(self):
        """返回当前模式下的参数字典"""
        current_page = self.stack.currentWidget()
        return current_page.get_params()
```

---

### 批次 10：gui/main_window.py 最终集成

**目标**：模式选择 → 面板切换 → 线程启动 → 图表渲染 → 报告生成，完整流程串联

**文件**：修改 `gui/main_window.py`（~60 行增量）

**关键改动**：
- 连接 `ModeSelector.mode_changed` → `ControlPanel.switch_mode()`
- `_start_simulation()` 从 `ControlPanel.get_params()` 获取模式参数
- `_on_finished()` 根据 report 中的 mode 字段分发到对应 Canvas
- `_generate_text_report()` 根据 mode 生成不同格式报告

---

## 验证矩阵（修正版）

| 批次 | 验证项 | 预期 | 类型 |
|------|--------|------|:--:|
| 1 | config 新常量 + mode_selector 实例化 | 无 ImportError | 导入 |
| 2 | X^C X^c × X^C → 儿子 50% 患病 | χ² < 3.84 | 逻辑 |
| 2 | X^c X^c × X^C → 儿子 100% 患病 | 精确匹配 | 边界 |
| 3 | I^A i × I^B i → A:B:AB:O = 1:1:1:1 | χ² < 7.81 | 逻辑 |
| 3 | I^A I^B × I^A I^B → A:B:AB = 1:1:2 | χ² < 5.99 | 边界 |
| 4 | AaBb × AaBb → 9 种基因型 | 独立性 χ² < 9.49 | 逻辑 |
| 4 | 组合键格式 | 全部以 `|` 分隔 | 格式 |
| 5 | 5 基因性状均值≈2.65±0.05 | np.isclose | 统计 |
| 5 | num_genes=5 触发 AssertionError | 断言生效 | 边界 |
| 6 | classic 模式 stats 与 v1.0 完全一致 | 回归测试 | 兼容 |
| 6 | 新函数 `analyze_sex_linked` 正常输出 | 有返回值 | 导入 |
| 7 | `SimulationWorker("Aa", "Aa", 10000)` 向后兼容 | 无报错 | 兼容 |
| 7 | 未知 mode → fallback 到 classic | 不崩溃 | 鲁棒 |
| 8 | 4 种新 Canvas 实例化 + 中文正常 | 无方框 | 渲染 |
| 9 | 5 种模式切换，QStackedWidget 正确翻页 | 控件可见 | UI |
| 10 | 完整流程：选模式→设参数→模拟→图表→报告 | 无 Exception | 集成 |
| 10 | 切换模式后再次模拟 | 不崩溃 | 稳定性 |

---

## 打包验证

```bash
# 依赖安装
pip install scipy  # 新增依赖
cd /e/space/mendel_data_lab

# 全模块导入验证
python -c "
from core.sex_chromosome import simulate_sex_chromosome_crossover
from core.multi_allele import simulate_abo_crossover
from core.polygenic import simulate_polygenic_trait, fit_normal
from gui.chart_widget import HeatmapCanvas, GroupedBarCanvas, PieChartCanvas, HistogramCanvas
from gui.mode_selector import ModeSelector
print('All modules OK')
"

# 打包
pyinstaller -F -w --clean --name="超级孟德尔基因大数对决数字实验室v2" main.py
ls -lh dist/
```

---

## 风险热力图（修正后）

```
批次:  1   2   3   4   5   6   7   8   9  10
风险:  ░   ░   ░   ░   ▒   ▒   ▒   ▒   ▒   █
                                          ▲
                                    唯一高风险：最终集成
```

修正后风险大幅降低——引擎层（1-5）完全独立，统计（6）独立于线程（7），只有批次 10 是真正的集成点。
