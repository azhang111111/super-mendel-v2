"""全局配置：现代医疗/基因实验室风格样式与常量"""

# ── 颜色系统（国际生物信息学软件风格）──
COLOR_BG_MAIN = "#f8fafc"          # 主窗口背景：极简亮白灰
COLOR_BG_PANEL = "#ffffff"          # 控制面板背景：纯白
COLOR_BORDER = "#e2e8f0"            # 灰色描边
COLOR_DOMINANT = "#3b82f6"          # 显性性状：科技靛蓝
COLOR_RECESSIVE = "#f43f5e"         # 隐性性状：玫瑰粉红
COLOR_THEORY_LINE = "#10b981"       # 理论参考线：薄荷荧光绿
COLOR_TEXT_PRIMARY = "#1e293b"      # 主文字色
COLOR_TEXT_SECONDARY = "#64748b"    # 次要文字色
COLOR_ACCENT = "#8b5cf6"            # 强调色：紫色

# ── 图表样式 ──
CHART_DPI = 100
CHART_FIGSIZE_BAR = (6, 4)
CHART_FIGSIZE_CONVERGENCE = (6, 4)
CHART_TITLE_SIZE = 14
CHART_LABEL_SIZE = 11
CHART_TICK_SIZE = 9

# ── 全局QSS样式表 ──
GLOBAL_QSS = f"""
QMainWindow {{
    background-color: {COLOR_BG_MAIN};
}}

QGroupBox {{
    background-color: {COLOR_BG_PANEL};
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    margin-top: 12px;
    padding: 16px;
    font-size: 13px;
    font-weight: bold;
    color: {COLOR_TEXT_PRIMARY};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: {COLOR_ACCENT};
}}

QLabel {{
    color: {COLOR_TEXT_PRIMARY};
    font-size: 12px;
}}

QComboBox {{
    background-color: {COLOR_BG_PANEL};
    border: 1px solid {COLOR_BORDER};
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 12px;
    color: {COLOR_TEXT_PRIMARY};
    min-width: 100px;
}}

QComboBox:hover {{
    border-color: {COLOR_DOMINANT};
}}

QComboBox::drop-down {{
    border: none;
    padding-right: 8px;
}}

QSpinBox {{
    background-color: {COLOR_BG_PANEL};
    border: 1px solid {COLOR_BORDER};
    border-radius: 4px;
    padding: 6px 8px;
    font-size: 12px;
    color: {COLOR_TEXT_PRIMARY};
}}

QSlider::groove:horizontal {{
    background: {COLOR_BORDER};
    height: 6px;
    border-radius: 3px;
}}

QSlider::handle:horizontal {{
    background: {COLOR_DOMINANT};
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}}

QPushButton {{
    background-color: {COLOR_DOMINANT};
    color: white;
    border: none;
    border-radius: 6px;
    padding: 10px 20px;
    font-size: 13px;
    font-weight: bold;
}}

QPushButton:hover {{
    background-color: #2563eb;
}}

QPushButton:pressed {{
    background-color: #1d4ed8;
}}

QPushButton:disabled {{
    background-color: #94a3b8;
}}

QProgressBar {{
    border: none;
    border-radius: 4px;
    background-color: {COLOR_BORDER};
    height: 8px;
    text-align: center;
    font-size: 10px;
}}

QProgressBar::chunk {{
    background-color: {COLOR_DOMINANT};
    border-radius: 4px;
}}

QTabWidget::pane {{
    border: 1px solid {COLOR_BORDER};
    border-radius: 6px;
    background-color: {COLOR_BG_PANEL};
}}

QTabBar::tab {{
    background-color: {COLOR_BG_MAIN};
    border: 1px solid {COLOR_BORDER};
    padding: 8px 16px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    font-size: 12px;
    color: {COLOR_TEXT_SECONDARY};
}}

QTabBar::tab:selected {{
    background-color: {COLOR_BG_PANEL};
    color: {COLOR_DOMINANT};
    font-weight: bold;
    border-bottom: 2px solid {COLOR_DOMINANT};
}}

QStatusBar {{
    background-color: {COLOR_BG_PANEL};
    border-top: 1px solid {COLOR_BORDER};
    color: {COLOR_TEXT_SECONDARY};
    font-size: 11px;
}}
"""

# ── 默认模拟次数选项 ──
SIMULATION_PRESETS = [100, 1000, 10000, 100000, 1000000]

# ── 基因型选项 ──
GENOTYPE_OPTIONS = ["AA", "Aa", "aa"]

# ── 理论比例 ──
THEORY_GENOTYPE_RATIO = {"AA": 0.25, "Aa": 0.50, "aa": 0.25}
THEORY_PHENOTYPE_RATIO = {"显性": 0.75, "隐性": 0.25}

# ── 遗传模式 ──
GENETIC_MODES = {
    "classic": "单基因孟德尔 (经典)",
    "multigene": "二因子/三因子杂交",
    "sex": "性染色体遗传 (X 连锁)",
    "multi_allele": "复等位基因 (ABO 血型)",
    "polygenic": "多基因数量性状",
    "disease": "疾病模拟",
}

# ── ABO 血型系统 ──
ABO_GENOTYPES = ["I^A I^A", "I^A i", "I^B I^B", "I^B i", "I^A I^B", "i i"]
ABO_PHENOTYPES = ["A型", "B型", "AB型", "O型"]
ABO_PHENOTYPE_MAP = {
    ("I^A", "I^A"): "A型", ("I^A", "i"): "A型",
    ("I^B", "I^B"): "B型", ("I^B", "i"): "B型",
    ("I^A", "I^B"): "AB型",
    ("i", "i"): "O型",
}

# ── X 连锁等位基因 ──
X_ALLELES = ["X^A", "X^a"]  # A=正常, a=突变 (如色盲)

# ── 多基因性状默认参数 ──
DEFAULT_POLYGENIC_GENE_COUNT = 5
DEFAULT_POLYGENIC_EFFECT_SIZES = [2.0, 1.5, 1.0, 0.5, 0.3]

# ── 多基因模式限制 ──
MAX_GENES = 4  # 最多支持 4 个基因

# ── 遗传模式说明（v2.0 新增）──
MODE_DESCRIPTIONS = {
    "classic": "经典孟德尔单基因杂交实验。选择 AA/Aa/aa 亲本，观察子代 1:2:1 基因型比例和 3:1 表现型分离比。大数定律收敛曲线展示随机偏离→理论值的过程。",
    "multigene": "二因子/三因子杂交实验。每对基因独立分配到子代，验证孟德尔自由组合定律。下拉选择基因数(2-4)，为每个基因选亲本基因型(AA/Aa/aa)。右侧热力图展示基因型分布。",
    "sex": "X 连锁遗传模拟。母亲选两条 X 等位基因组合，父亲选 X 等位基因。儿子为半合子(仅一条 X)，性状完全由母亲决定。典型案例：红绿色盲/血友病。",
    "multi_allele": "ABO 血型遗传系统。I^A 和 I^B 共显性，i 隐性。6 种基因型→4 种表现型(A/B/AB/O)。支持所有血型亲本组合。",
    "polygenic": "多基因数量性状模拟。多个基因独立杂交，每个基因对性状产生加性效应，总体呈正态分布。演示数量遗传学核心概念——中心极限定理。可调节基因数/基准值/噪声。",
    "disease": "经典遗传病场景库 + 三代家系分析。选择10种常见遗传病之一，加载预设参数后进行家系模拟，推算子代/孙代患病概率。",
}

# ══════════════════════════════════════════════
# v3.0 疾病模拟
# ══════════════════════════════════════════════

# 疾病场景库
DISEASE_LIBRARY = {
    "红绿色盲": {
        "mode": "sex",
        "inheritance": "X连锁隐性",
        "description": "最常见的色觉障碍，男性发病率约8%。母亲为携带者时，儿子有50%概率患病。",
        "params": {"mother_X": "X^C X^c", "father_X": "X^C"},
        "offspring_risk": {"儿子患病率": 0.50, "女儿携带率": 0.50, "女儿患病率": 0.00}
    },
    "血友病A": {
        "mode": "sex",
        "inheritance": "X连锁隐性",
        "description": "凝血因子VIII缺乏，著名王室遗传病。男性发病率约1/5000。",
        "params": {"mother_X": "X^H X^h", "father_X": "X^H"},
        "offspring_risk": {"儿子患病率": 0.50, "女儿携带率": 0.50, "女儿患病率": 0.00}
    },
    "杜氏肌营养不良": {
        "mode": "sex",
        "inheritance": "X连锁隐性",
        "description": "进行性肌肉萎缩，男性发病率约1/3500。通常3-5岁发病。",
        "params": {"mother_X": "X^D X^d", "father_X": "X^D"},
        "offspring_risk": {"儿子患病率": 0.50, "女儿携带率": 0.50, "女儿患病率": 0.00}
    },
    "白化病": {
        "mode": "classic",
        "inheritance": "常染色体隐性",
        "description": "黑色素合成障碍，发病率约1/17000。父母均为携带者时子女患病率25%。",
        "params": {"female": "Aa", "male": "Aa"},
        "offspring_risk": {"患病率": 0.25, "携带率": 0.50, "正常率": 0.25}
    },
    "苯丙酮尿症": {
        "mode": "classic",
        "inheritance": "常染色体隐性",
        "description": "PKU，苯丙氨酸代谢障碍。中国发病率约1/11000。新生儿筛查必查项目。",
        "params": {"female": "Pp", "male": "Pp"},
        "offspring_risk": {"患病率": 0.25, "携带率": 0.50, "正常率": 0.25}
    },
    "囊性纤维化": {
        "mode": "classic",
        "inheritance": "常染色体隐性",
        "description": "CFTR基因突变导致黏液分泌异常。白种人发病率约1/2500。",
        "params": {"female": "Ff", "male": "Ff"},
        "offspring_risk": {"患病率": 0.25, "携带率": 0.50, "正常率": 0.25}
    },
    "亨廷顿舞蹈症": {
        "mode": "classic",
        "inheritance": "常染色体显性",
        "description": "HTT基因CAG重复扩增，中年发病。子女有50%概率遗传致病基因。",
        "params": {"female": "hh", "male": "Hh"},
        "offspring_risk": {"患病率": 0.50, "正常率": 0.50}
    },
    "马凡综合征": {
        "mode": "classic",
        "inheritance": "常染色体显性",
        "description": "FBN1基因突变，影响结缔组织。发病率约1/5000。",
        "params": {"female": "mm", "male": "Mm"},
        "offspring_risk": {"患病率": 0.50, "正常率": 0.50}
    },
    "家族性高胆固醇血症": {
        "mode": "classic",
        "inheritance": "常染色体显性",
        "description": "LDLR基因突变，杂合子发病率约1/250。早发心血管病风险显著升高。",
        "params": {"female": "ff", "male": "Ff"},
        "offspring_risk": {"患病率": 0.50, "正常率": 0.50}
    },
    "镰刀型贫血": {
        "mode": "classic",
        "inheritance": "常染色体共显性",
        "description": "HBB基因突变，杂合子有疟疾抗性。非洲裔发病率约1/500。",
        "params": {"female": "HbA HbS", "male": "HbA HbS"},
        "offspring_risk": {"患病率": 0.25, "携带率": 0.50, "正常率": 0.25}
    },
}
