# 人类染色体基因推算扩展 — 架构设计文档

> **项目**: 超级孟德尔基因大数对决数字实验室 v2.0 扩展  
> **基准代码**: `E:\space\mendel_data_lab` (当前 v1.0)  
> **设计日期**: 2026-05-27  

---

## 一、可行性分析

### 1.1 当前架构回顾

| 组件 | 能力 | 限制 |
|------|------|------|
| `crossover_engine.py` | 单基因、双等位、向量化百万级 | 仅支持 1 个基因座 (locus) |
| `stats_analyzer.py` | Punnett Square 理论值、卡方检验 | 仅 6 种亲本组合 |
| `chart_widget.py` | 柱状图 + 收敛折线图 | 仅显性/隐性二分类 |
| `worker_thread.py` | QThread 异步 | 通用，无需改动 |
| `main_window.py` | 控制面板 + 报告 | 仅单基因参数 |

### 1.2 可行性结论：✅ 核心架构支持，需扩展而非重写

| 人类遗传学特性 | 可行性 | 实现难度 | 说明 |
|---------------|--------|---------|------|
| **多基因独立分配**（二因子/三因子杂交） | ✅ 可行 | ⭐⭐ | NumPy 多维矩阵扩展，现有向量化引擎直接复用 |
| **性染色体遗传**（X 连锁） | ✅ 可行 | ⭐⭐ | 新增配子模型（X/Y），其余逻辑不变 |
| **复等位基因**（ABO 血型） | ✅ 可行 | ⭐ | 等位基因池从 2→N，其余逻辑不变 |
| **多基因数量性状**（身高/肤色） | ✅ 可行 | ⭐⭐⭐ | 多基因加性效应 + 正态分布建模 |
| **基因连锁与交换** | ⚠️ 部分可行 | ⭐⭐⭐⭐ | 需染色体结构建模，可做简化版 |
| **线粒体遗传** | ✅ 可行 | ⭐ | 母系遗传，简单规则 |
| **表观遗传学** | ❌ 暂不可行 | ⭐⭐⭐⭐⭐ | 超出当前数学模型范围 |

### 1.3 推荐扩展路线

```
v1.0 (当前) ──→ v2.0 (多基因+性染色体+复等位)
                  └── v2.1 (多基因性状可视化)
                       └── v3.0 (基因连锁+交换)
```

---

## 二、v2.0 新增模块设计

### 2.1 项目目录扩展

```
mendel_data_lab/
├── main.py                          # (不改)
├── config.py                        # (小改：新增常量和QSS)
│
├── gui/
│   ├── main_window.py               # (改：新增 Tab 页)
│   ├── control_panel.py             # (改：模式选择下拉框)
│   ├── chart_widget.py              # (改：新增多基因散点图)
│   └── mode_selector.py             # (新) 遗传模式选择器
│
├── core/
│   ├── crossover_engine.py          # (改：多基因向量化)
│   ├── stats_analyzer.py            # (改：多基因统计)
│   ├── worker_thread.py             # (改：多模式 dispatch，接收 mode 参数)
│   │
│   ├── sex_chromosome.py            # (新) X/Y 性染色体模型
│   ├── multi_allele.py              # (新) 复等位基因引擎 (ABO)
│   └── polygenic.py                 # (新) 多基因数量性状引擎
│
└── assets/                          # (不改)
```

### 2.2 新增文件清单

| 文件 | 行数估算 | 说明 |
|------|---------|------|
| `core/sex_chromosome.py` | ~80 | X/Y 染色体配子模型 |
| `core/multi_allele.py` | ~120 | N 等位基因向量化杂交 |
| `core/polygenic.py` | ~150 | 多基因加性效应 + 正态拟合 |
| `gui/mode_selector.py` | ~100 | 遗传模式切换面板 |
| **修改文件** | ~200 行增量 | engine/stats/chart/main_window 扩展 |

---

## 三、核心算法设计

### 3.1 多基因独立分配模型

**原理**：n 对等位基因位于 n 对同源染色体上，独立分配到配子中。

```python
def simulate_multigene_crossover(parent1_genotypes, parent2_genotypes, num_simulations):
    """
    parent1_genotypes: list, e.g. ["Aa", "Bb", "CC"]  (每个基因的基因型)
    parent2_genotypes: list, e.g. ["Aa", "Bb", "CC"]
    num_simulations: int
    
    返回: dict, 如 {"AABBCC": count, "AaBbCC": count, ...}
    """
    num_genes = len(parent1_genotypes)
    all_zygote_parts = []
    for i in range(num_genes):
        _, g1, g2 = simulate_crossover_vectorized(
            list(parent1_genotypes[i]), list(parent2_genotypes[i]), num_simulations
        )
        z = np.char.add(g1, g2)  # 单个基因的子代基因型 (N,)
        all_zygote_parts.append(z)
    
    # np.column_stack: (N, num_genes) 矩阵
    stacked = np.column_stack(all_zygote_parts)
    # 逐列拼接为组合键 "AABB", "AaBb", ...
    combined = stacked[:, 0]
    for j in range(1, num_genes):
        combined = np.char.add(combined, stacked[:, j])
    
    genotypes, counts = np.unique(combined, return_counts=True)
    return dict(zip(genotypes, counts.astype(int)))
```

**关键挑战**：n 个基因的组合空间是 `3^n`，4 基因 = 81 种结果。`np.column_stack` + `np.char.add` 链式拼接保持向量化，避免 Python 循环瓶颈。超过 4 个基因时建议抽稀显示 Top-N 基因型。

### 3.2 性染色体模型

| 亲本 | 配子 | 子代可能 |
|------|------|---------|
| ♀ XX × ♂ XY | ♀: X/X, ♂: X/Y | 女儿: XX, 儿子: XY |
| 基因位于 X 染色体上 | ♂ 仅一条 X（半合子） | 儿子的性状直接来自母亲 |

```python
def sex_chromosome_crossover(mother_X_alleles, father_X_allele, num_simulations):
    """
    性染色体遗传模拟。
    
    mother_X_alleles: 母亲两条 X 的等位基因，如 ['X^A', 'X^a'] 或 ['X^A', 'X^A']
    father_X_allele: 父亲唯一的 X 等位基因，如 'X^A' 或 'X^a'
                     注意：父亲还有一条 Y，不携带此基因
    
    子代性别由父亲决定：
      - 父亲提供 X → 女儿 (XX)
      - 父亲提供 Y → 儿子 (XY)
    
    返回: {
        "女儿": {"X^A X^A": count, "X^A X^a": count, ...},
        "儿子": {"X^A Y": count, "X^a Y": count}
    }
    """
    # 1. 母亲随机提供一条 X（等概率）
    mom_idx = np.random.randint(0, 2, size=num_simulations)
    mom_pool = np.array(mother_X_alleles)
    maternal_gamete = mom_pool[mom_idx]  # (N,)
    
    # 2. 性别决定：父亲随机提供 X 或 Y（各 50%）
    is_female = np.random.random(num_simulations) < 0.5
    paternal_gamete = np.where(is_female, father_X_allele, 'Y')
    
    # 3. 儿子只有一条 X（来自母亲），表现为半合子
    #    即儿子的性状完全由母亲给的 X 决定
    daughter_mask = is_female
    son_mask = ~is_female
    
    # 4. 统计女儿基因型
    daughter_pair = np.char.add(maternal_gamete[daughter_mask], paternal_gamete[daughter_mask])
    d_gtypes, d_counts = np.unique(daughter_pair, return_counts=True)
    
    # 5. 统计儿子基因型（半合子：母亲的X + Y）
    son_pair = np.char.add(maternal_gamete[son_mask],
                           np.full(son_mask.sum(), 'Y'))
    s_gtypes, s_counts = np.unique(son_pair, return_counts=True)
    
    return {
        "女儿": dict(zip(d_gtypes, d_counts.astype(int))),
        "儿子": dict(zip(s_gtypes, s_counts.astype(int))),
    }
```

**关键点**：儿子只有一条 X 染色体（半合子），所以 X 连锁隐性性状在儿子中表达率远高于女儿。例如红绿色盲基因 X^c，母亲为携带者 X^C X^c 时，儿子有 50% 概率患病，女儿 0%（除非父亲也患病）。

### 3.3 复等位基因模型（ABO 血型）

**概念区分**：
- **种群等位基因池**：一个物种所有可能的等位基因，如 ABO 系统有 `{I^A, I^B, i}` 共 3 种
- **个体基因型**：每个人携带池中的 2 个等位基因（二倍体），如 `I^A i`（A 型血）

**等位基因池**：`I^A`, `I^B`, `i`
- I^A 和 I^B 共显性，i 隐性
- 6 种基因型 → 4 种表现型（A/B/AB/O）

```python
# 种群级别等位基因池常量（不同系统可配置）
ALLELE_POOLS = {
    "ABO": ["I^A", "I^B", "i"],
    "兔子毛色": ["C", "c^ch", "c^h", "c"],  # 4 个等位基因
}

# 表现型映射表：基因型 → 表现型
ABO_PHENOTYPE_MAP = {
    ("I^A", "I^A"): "A型", ("I^A", "i"): "A型",
    ("I^B", "I^B"): "B型", ("I^B", "i"): "B型",
    ("I^A", "I^B"): "AB型",
    ("i", "i"): "O型",
}

def simulate_multi_allele(p1_genotype, p2_genotype, num_simulations):
    """
    p1_genotype: 个体基因型（2 个等位基因），如 ['I^A', 'i']
    p2_genotype: 同上，如 ['I^B', 'i']
    
    每个亲本等概率提供 1 个等位基因给子代。
    子代获得 2 个等位基因后，按表现型映射表归类。
    
    返回: {
        "genotype_counts": {"I^A I^B": count, ...},
        "phenotype_counts": {"A型": count, "B型": count, "AB型": count, "O型": count}
    }
    """
    # 复用现有向量化引擎（等位基因池为 2）
    result_dict, g1, g2 = simulate_crossover_vectorized(
        p1_genotype, p2_genotype, num_simulations
    )
    # 基因型 → 表现型映射
    pheno_counts = {"A型": 0, "B型": 0, "AB型": 0, "O型": 0}
    for gt, count in result_dict.items():
        alleles = tuple(sorted(gt))  # 标准化为排序元组
        pheno = ABO_PHENOTYPE_MAP.get(
            alleles,
            ABO_PHENOTYPE_MAP.get((alleles[1], alleles[0]), "未知")
        )
        pheno_counts[pheno] += count
    return {"genotype_counts": result_dict, "phenotype_counts": pheno_counts}
```

**注意**：现有 `simulate_crossover_vectorized` 假定等位基因池大小为 2（用 `np.random.randint(0, 2)`），对 2 等位基因的个体完全适用。若需扩展到 3+ 等位基因的个体层面（如四倍体生物），才需要修改随机索引范围为 `len(p1_pool)`。

### 3.4 多基因数量性状模型

**核心思想**：多个基因对同一性状产生加性效应，总体呈正态分布。

```
身高 = 基础值 + Σ(每个基因的加性效应) + 环境噪声

基因型 AA → 效应 +2cm
基因型 Aa → 效应 +1cm
基因型 aa → 效应 +0cm
```

```python
def simulate_polygenic_trait(num_genes, parent1_gtypes, parent2_gtypes, num_simulations):
    """
    num_genes: 参与性状的基因数 (如 5-20)
    每个基因独立杂交，效应累加
    
    返回: ndarray of trait values (可用于直方图 + 正态拟合)
    """
    trait_values = np.zeros(num_simulations)
    for gene_idx in range(num_genes):
        # 单基因杂交
        result, g1, g2 = simulate_crossover_vectorized(...)
        # 加性效应：根据基因型赋值
        effect = genotype_to_effect_map[gene_idx]
        trait_values += effect
    # 添加环境噪声
    trait_values += np.random.normal(0, noise_std, num_simulations)
    return trait_values
```

**可视化**：直方图 + 正态分布拟合曲线，展示中心极限定理。

---

## 四、UI 扩展设计

### 4.1 新增遗传模式选择

```
┌─────────────────────────────┐
│  遗传模式                    │
│  ┌───────────────────────┐  │
│  │ ○ 单基因孟德尔 (经典)  │  │
│  │ ○ 二因子杂交          │  │
│  │ ○ 性染色体遗传         │  │
│  │ ○ 复等位基因 (ABO)     │  │
│  │ ○ 多基因数量性状       │  │
│  └───────────────────────┘  │
└─────────────────────────────┘
```

### 4.2 模式切换时的 UI 变化

| 模式 | 控制面板变化 | 图表变化 |
|------|------------|---------|
| 单基因 | 母本/父本各 1 个下拉框 | 柱状图 + 收敛折线图 |
| 二因子杂交 | 基因A/B/C 各两个下拉框 | 基因型分布热力图 |
| 性染色体 | ♀ X 等位基因、♂ X/Y 等位基因 | 按性别分组的柱状图 |
| ABO 血型 | 母本/父本从 6 种基因型选择 | ABO 四分类饼图 |
| 多基因性状 | 基因数滑块（2-20）+ 效应大小 | 直方图 + 正态拟合 |

### 4.3 新增图表类型

| 图表 | 用于 | 实现 |
|------|------|------|
| 热力图 (Heatmap) | 二因子基因型分布 | Seaborn `heatmap()` |
| 分组柱状图 | 性染色体按性别分列 | 双组 bar chart |
| 饼图/环形图 | ABO 血型四分类 | Matplotlib `pie()` |
| 直方图+正态拟合 | 多基因性状分布 | `hist()` + `scipy.stats.norm.fit()` |

---

## 五、数据流设计

```
┌──────────┐    ┌──────────────────┐    ┌───────────────┐
│ 模式选择  │───▶│  参数收集        │───▶│  计算引擎      │
│ (mode)   │    │ (parent+alleles) │    │ (dispatch)    │
└──────────┘    └──────────────────┘    └───────┬───────┘
                                                │
                        ┌───────────────────────┘
                        ▼
              ┌─────────────────┐
              │ 单基因引擎       │ crossover_engine.py
              │ 性染色体引擎     │ sex_chromosome.py
              │ 复等位基因引擎   │ multi_allele.py
              │ 多基因性状引擎   │ polygenic.py
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │ 统计分析        │ stats_analyzer.py
              │ (按模式分发)     │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │ 图表渲染        │ chart_widget.py
              │ 报告生成        │ main_window.py
              └─────────────────┘
```

---

## 六、实施计划

### 阶段一：基础设施 (2-3 批次)

| 批次 | 内容 | 新增文件 |
|------|------|---------|
| 1 | `config.py` 扩展 + `mode_selector.py` | `gui/mode_selector.py` |
| 2 | `core/sex_chromosome.py` 性染色体引擎 | `core/sex_chromosome.py` |
| 3 | `core/multi_allele.py` 复等位基因引擎 | `core/multi_allele.py` |

### 阶段二：多基因引擎 + 线程适配 (3 批次)

| 批次 | 内容 | 修改文件 |
|------|------|---------|
| 4 | `crossover_engine.py` 多基因扩展 | `core/crossover_engine.py` |
| 5 | `core/polygenic.py` 多基因性状 | `core/polygenic.py` |
| 6 | `worker_thread.py` 多模式 dispatch | `core/worker_thread.py` |

> **批次 6 设计要点**：`SimulationWorker.__init__` 新增 `mode` 参数（`"classic"`/`"sex"`/`"multi_allele"`/`"polygenic"`/`"multigene"`），`run()` 中根据 mode 分发到不同引擎函数，各自生成相应格式的 report dict。注意保持现有的 `pyqtSignal` 接口不变（`progress_updated`、`simulation_finished`、`simulation_error`），仅变化 report dict 内部字段。

### 阶段三：UI 集成 (2 批次)

| 批次 | 内容 | 修改文件 |
|------|------|---------|
| 6 | `main_window.py` 模式 Tab 集成 | `gui/main_window.py` |
| 7 | `chart_widget.py` 新增图表类型 | `gui/chart_widget.py` |
| 8 | `stats_analyzer.py` 多模式统计 | `core/stats_analyzer.py` |

**总计**：~9 批次，约 9 个文件（4 新 + 5 改），新增代码 ~900 行。

---

## 七、教育价值对照

| 扩展模块 | 教学目标 | 对应高中/大学生物知识点 |
|---------|---------|----------------------|
| 多基因独立分配 | 孟德尔第二定律（自由组合） | 二因子/三因子杂交，9:3:3:1 |
| 性染色体遗传 | X 连锁显性/隐性 | 红绿色盲、血友病家系分析 |
| 复等位基因 | 共显性、复等位现象 | ABO 血型系统 |
| 多基因数量性状 | 数量遗传学、中心极限定理 | 身高/肤色多基因遗传 |

---

## 八、风险评估

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| 多基因组合爆炸（n 基因=3^n 种基因型） | 高 | 图表不可读 | 限制基因数≤4，抽稀显示 Top-N |
|**stats_analyzer.py 重构引入回归** | **高** | **现有单基因模式崩溃** | 保持原函数签名不变，新增模式参数用默认值 `"classic"` 向后兼容；每个新模式增加独立测试用例 |
| PyInstaller 打包体积增大 | 中 | .exe 超过 120MB | 条件导入，按需加载新模块 |
| 多基因性状依赖 scipy.stats | 中 | 打包需含 scipy | 备选：纯 NumPy 实现正态拟合 |
| 性染色体性别-性状耦合逻辑错误 | 中 | X 连锁计算结果与生物实际不符 | 编写完整单元测试矩阵（6 种亲本组合 × 男/女） |
| 多基因独立分配笛卡尔积合并性能衰减 | 中 | 3 基因×100 万次合并变慢 | 用 `np.column_stack` + `np.char.add` 全程向量化 |
| Matplotlib 中文在新图表中失效 | 低 | 热力图/饼图显示方框 | 统一在 `chart_widget.py` 开头配置 `rcParams['font.sans-serif']` |
| 复等位基因表现型映射歧义 | 低 | ABO 血型归类错误 | `ABO_PHENOTYPE_MAP` 字典覆盖全部 6 种基因型 |
