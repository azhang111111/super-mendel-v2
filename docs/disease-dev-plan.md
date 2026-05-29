# 疾病模拟功能 — 详细开发实施方案

> **设计文档**: `docs/disease-pedigree-design.md`  
> **基准代码**: `E:\space\mendel_data_lab` (v2.0)  
> **新增模式**: `disease` — 疾病模拟  

---

## 批次 1：数据层 — config.py 疾病库

**修改**: `config.py`

在 GENETIC_MODES 末尾追加 `"disease": "疾病模拟"`。

在 MODE_DESCRIPTIONS 末尾追加 disease 描述。

在文件末尾追加 DISEASE_LIBRARY 字典（10种疾病，每种含 mode/inheritance/description/params/offspring_risk）。

---

## 批次 2：引擎层 — core/pedigree.py 家系模拟引擎

**新建**: `core/pedigree.py`（~120行）

核心函数:
- `simulate_pedigree(founder_gtypes, generations, children_per_couple)` → 返回三代家系基因型
- `calculate_pedigree_stats(pedigree_data)` → 统计每代患病率/携带率

---

## 批次 3：UI层 — gui/chart_widget.py PedigreeCanvas 家系图

**修改**: `gui/chart_widget.py`（追加 ~80行）

新增 PedigreeCanvas 类，用 matplotlib.patches 绘制标准家系图:
- □ 男性 / ○ 女性
- ■ 患病（实心）/ ◐ 携带者（半实心）
- ─ 婚姻线 / │ 亲子线

---

## 批次 4：UI层 — gui/control_panel.py 疾病页面

**修改**: `gui/control_panel.py`（追加 ~60行）

新增 `_create_disease_page()`:
- 疾病选择 QComboBox（列出 10 种疾病）
- 疾病说明 QLabel（遗传方式 + 描述）
- "加载此场景" QPushButton → 填入参数
- 子女数 QSpinBox

新增 `_apply_disease_scenario(name)`:
- 根据疾病库加载参数
- 自动切换到对应遗传模式
- 填入亲本基因型

---

## 批次 5：线程层 — core/worker_thread.py

**修改**: `core/worker_thread.py`（追加 ~15行）

新增 `_run_disease()`:
- 从 params 获取疾病参数
- 调用 pedigree.simulate_pedigree
- 发射 simulation_finished 信号

dispatchers 加 `"disease": self._run_disease`

---

## 批次 6：集成层 — gui/main_window.py

**修改**: `gui/main_window.py`（追加 ~30行）

- QStackedWidget 加第 6 页（disease_page）
- _on_finished 中处理 disease 模式：显示 PedigreeCanvas
- _generate_text_report 中 disease 模式报告

---

**总批次**: 6  
**新增文件**: 1 (`core/pedigree.py`)  
**修改文件**: 5  
**新增代码**: ~350行
