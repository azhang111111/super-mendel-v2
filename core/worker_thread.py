"""QThread 多线程封装 — 防止百万次大计算导致 GUI 线程卡死"""

from PyQt6.QtCore import QThread, pyqtSignal

from core.crossover_engine import simulate_crossover_vectorized, calculate_convergence_curve
from core.stats_analyzer import generate_summary_report, generate_multimode_report


class SimulationWorker(QThread):
    """后台模拟计算工作线程 (v2.0: 多模式支持)"""

    progress_updated = pyqtSignal(int, int)
    simulation_finished = pyqtSignal(dict)
    simulation_error = pyqtSignal(str)

    def __init__(self, parent1=None, parent2=None, num_simulations=None,
                 mode="classic", params=None, parent=None):
        """
        向后兼容:
          - 传 parent1, parent2, num_simulations → classic 模式
          - 传 mode + params → 新模式

        mode: "classic" | "multigene" | "sex" | "multi_allele" | "polygenic"
        params: dict, 包含对应模式所需的参数
        """
        super().__init__(parent)
        self.mode = mode
        if params is None:
            params = {
                "parent1": parent1 or "Aa",
                "parent2": parent2 or "Aa",
                "num_simulations": num_simulations or 10000,
            }
        self.params = params

    def run(self):
        """在后台线程中执行计算"""
        try:
            self.progress_updated.emit(0, self.params.get("num_simulations", 10000))
            dispatchers = {
                "classic": self._run_classic,
                "multigene": self._run_multigene,
                "sex": self._run_sex,
                "multi_allele": self._run_multi_allele,
                "polygenic": self._run_polygenic,
                "disease": self._run_disease,
            }
            handler = dispatchers.get(self.mode, self._run_classic)
            handler()
        except Exception as e:
            import traceback
            self.simulation_error.emit(f"{e}\n{traceback.format_exc()}")

    def _run_classic(self):
        """经典单基因模式 (v1.0 兼容)"""
        p1 = self.params["parent1"]
        p2 = self.params["parent2"]
        N = self.params["num_simulations"]

        result_dict, gametes1, gametes2 = simulate_crossover_vectorized(
            list(p1), list(p2), N
        )
        self.progress_updated.emit(N // 2, N)
        convergence_data = calculate_convergence_curve(gametes1, gametes2)
        self.progress_updated.emit(N, N)

        report = generate_summary_report(result_dict, N, p1, p2, convergence_data)
        report["mode"] = "classic"
        self.simulation_finished.emit(report)

    def _run_multigene(self):
        """多基因独立分配模式"""
        from core.crossover_engine import simulate_multigene_crossover
        p1 = self.params["parent1_gtypes"]
        p2 = self.params["parent2_gtypes"]
        N = self.params["num_simulations"]

        result = simulate_multigene_crossover(p1, p2, N)
        self.progress_updated.emit(N, N)
        report = generate_multimode_report("multigene", result, self.params, N)
        self.simulation_finished.emit(report)

    def _run_sex(self):
        """性染色体模式"""
        from core.sex_chromosome import simulate_sex_chromosome_crossover
        mother_X = self.params["mother_X"]
        father_X = self.params["father_X"]
        N = self.params["num_simulations"]

        # 如果传入的是字符串 "X^A X^a"，拆分为列表 ['X^A', 'X^a']
        if isinstance(mother_X, str):
            mother_X = mother_X.strip().split()
            if len(mother_X) == 0:
                raise ValueError("母亲 X 等位基因不能为空")
            if len(mother_X) != 2:
                raise ValueError(f"母亲 X 等位基因需要恰好 2 个，收到 {len(mother_X)} 个: {mother_X}")

        # 父亲只有一条 X（生物学上），支持字符串传入但保持标量类型
        # 如果误传了多等位基因字符串，检测并报错
        if isinstance(father_X, str):
            father_X = father_X.strip()
            if " " in father_X:
                raise ValueError(f"父亲 X 等位基因应为单个值（如 'X^A'），收到含空格的字符串: '{father_X}'")

        result = simulate_sex_chromosome_crossover(mother_X, father_X, N)
        # 附加亲本信息供统计使用
        result["_mother_alleles"] = mother_X
        result["_father_allele"] = father_X
        self.progress_updated.emit(N, N)
        report = generate_multimode_report("sex", result, self.params, N)
        self.simulation_finished.emit(report)

    def _run_multi_allele(self):
        """复等位基因模式 (ABO)"""
        from core.multi_allele import simulate_abo_crossover
        p1 = self.params["parent1_genotype"]
        p2 = self.params["parent2_genotype"]
        N = self.params["num_simulations"]

        # 如果传入的是字符串 "I^A I^A"，拆分为列表 ['I^A', 'I^A']
        if isinstance(p1, str):
            p1 = p1.strip().split()
            if len(p1) == 0:
                raise ValueError("母本 ABO 基因型不能为空")
            if len(p1) != 2:
                raise ValueError(f"母本 ABO 基因型需要恰好 2 个等位基因，收到 {len(p1)} 个: {p1}")
        if isinstance(p2, str):
            p2 = p2.strip().split()
            if len(p2) == 0:
                raise ValueError("父本 ABO 基因型不能为空")
            if len(p2) != 2:
                raise ValueError(f"父本 ABO 基因型需要恰好 2 个等位基因，收到 {len(p2)} 个: {p2}")

        result = simulate_abo_crossover(p1, p2, N)
        self.progress_updated.emit(N, N)
        report = generate_multimode_report("multi_allele", result, self.params, N)
        self.simulation_finished.emit(report)

    def _run_disease(self):
        """疾病模拟模式 — 根据DISEASE_LIBRARY用Punnett方格生成确定性家系报告"""
        from config import DISEASE_LIBRARY
        params = self.params
        disease_name = params.get("disease_name", "")
        disease_info = DISEASE_LIBRARY.get(disease_name, {})
        inheritance = disease_info.get("inheritance", "")
        disease_params = disease_info.get("params", {})

        pedigree_report = _build_pedigree_report(disease_name, inheritance, disease_params)

        risk = disease_info.get("offspring_risk", {})
        self.progress_updated.emit(100, 100)

        report = {
            "mode": "disease",
            "total_simulations": 1,
            "disease_name": disease_name,
            "inheritance": inheritance,
            "offspring_risk": risk,
            "pedigree_report": pedigree_report,
        }
        self.simulation_finished.emit(report)

    def _run_polygenic(self):
        """多基因数量性状模式"""
        from core.polygenic import simulate_polygenic_trait
        num_genes = self.params["num_genes"]
        p1 = self.params["parent1_gtypes"]
        p2 = self.params["parent2_gtypes"]
        N = self.params["num_simulations"]
        effects = self.params.get("effects")
        base = self.params.get("base_value", 170.0)

        noise_std = self.params.get("noise_std", 2.0)
        values = simulate_polygenic_trait(
            num_genes, p1, p2, effects=effects,
            base_value=base, noise_std=noise_std, num_simulations=N
        )
        self.progress_updated.emit(N, N)
        report = generate_multimode_report("polygenic", values, self.params, N)
        self.simulation_finished.emit(report)


# ══════════════════════════════════════════════════════════════
# 疾病家系分析 — Punnett 方格确定性报告 (替代随机模拟)
# ══════════════════════════════════════════════════════════════

def _build_pedigree_report(disease_name, inheritance, params):
    """根据疾病类型构建确定性的家系文字报告"""
    lines = []
    lines.append(f"遗传病: {disease_name}")
    lines.append(f"遗传方式: {inheritance}")
    lines.append("")

    if "X连锁隐性" in inheritance:
        mother = params.get("mother_X", "X^H X^h")
        father = params.get("father_X", "X^H")
        lines.append(_x_linked_recessive_report(mother, father))
    elif "X连锁显性" in inheritance:
        mother = params.get("mother_X", "X^H X^h")
        father = params.get("father_X", "X^H")
        lines.append(_x_linked_dominant_report(mother, father))
    elif "常染色体隐性" in inheritance:
        female = params.get("female", "Aa")
        male = params.get("male", "Aa")
        lines.append(_autosomal_recessive_report(female, male))
    elif "常染色体显性" in inheritance:
        female = params.get("female", "hh")
        male = params.get("male", "Hh")
        lines.append(_autosomal_dominant_report(female, male))
    elif "常染色体共显性" in inheritance:
        female = params.get("female", "HbA HbS")
        male = params.get("male", "HbA HbS")
        lines.append(_autosomal_codominant_report(female, male))

    return "\n".join(lines)


def _x_linked_recessive_report(mother, father):
    """X连锁隐性遗传家系报告 (如: 母亲携带者 X^H X^h × 父亲正常 X^H Y)"""
    mother_alleles = mother.split()  # ["X^H", "X^h"]
    return f"""┌─────────────────────────────────────────────────────┐
│  Punnett 方格推算 (X连锁隐性)                        │
│  母本配子: {mother_alleles[0]}  /  {mother_alleles[1]}                     │
│  父本配子: {father}  /  Y                           │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Ⅰ代:  正常男性（□，{father} Y） —— 女性携带者（◐，{mother}） │
│                  ↓                                  │
│  Ⅱ代:  儿子50% 正常（□，{mother_alleles[0]} Y）          │
│         儿子50% 患病（■，{mother_alleles[1]} Y）                │
│         女儿50% 正常（○，{mother_alleles[0]} {mother_alleles[0]}）        │
│         女儿50% 携带（◐，{mother_alleles[0]} {mother_alleles[1]}）   │
│                  ↓（患病儿子与正常女性结婚）           │
│  Ⅲ代:  女儿100% 携带（◐，{mother_alleles[0]} {mother_alleles[1]}）   │
│         儿子100% 正常（□，{mother_alleles[0]} Y）         │
│                                                     │
└─────────────────────────────────────────────────────┘"""


def _x_linked_dominant_report(mother, father):
    """X连锁显性遗传家系报告"""
    mother_alleles = mother.split()
    return f"""┌─────────────────────────────────────────────────────┐
│  Punnett 方格推算 (X连锁显性)                        │
│  母本配子: {mother_alleles[0]}  /  {mother_alleles[1]}                     │
│  父本配子: {father}  /  Y                           │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Ⅰ代:  患病男性（■，{father} Y） —— 正常女性（○，{mother}）  │
│                  ↓                                  │
│  Ⅱ代:  儿子100% 正常（□，{mother_alleles[0]} Y）         │
│         女儿100% 患病（●，{mother_alleles[0]} {father}）  │
│                  ↓（患病女儿与正常男性结婚）           │
│  Ⅲ代:  子女50% 患病，50% 正常                       │
│                                                     │
└─────────────────────────────────────────────────────┘"""


def _autosomal_recessive_report(female, male):
    """常染色体隐性遗传家系报告 (如白化病 Aa × Aa)"""
    return f"""┌─────────────────────────────────────────────────────┐
│  Punnett 方格推算 (常染色体隐性)                      │
│  亲本: {female} × {male}                                        │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Ⅰ代:  携带者男性（◐，{male}） —— 携带者女性（◐，{female}） │
│                  ↓                                  │
│  Ⅱ代:  子女25% 正常（□/○，AA）                      │
│         子女50% 携带（◐，Aa）                        │
│         子女25% 患病（■/●，aa）                      │
│                  ↓                                  │
│  Ⅲ代:  取决于Ⅱ代配偶的基因型                         │
│        （如与正常纯合子结婚，子女均为携带者）          │
│                                                     │
└─────────────────────────────────────────────────────┘"""


def _autosomal_dominant_report(female, male):
    """常染色体显性遗传家系报告 (如亨廷顿舞蹈症 hh × Hh)"""
    return f"""┌─────────────────────────────────────────────────────┐
│  Punnett 方格推算 (常染色体显性)                      │
│  亲本: {female} × {male}                                        │
├─────────────────────────────────────────────────────┤
│  Ⅰ代:  患病男性（■，{male}） —— 正常女性（○，{female}）   │
│                  ↓                                  │
│  Ⅱ代:  子女50% 患病（■/●，Hh）                      │
│         子女50% 正常（□/○，hh）                      │
│                                                     │
└─────────────────────────────────────────────────────┘"""


def _autosomal_codominant_report(female, male):
    """常染色体共显性遗传家系报告 (如镰刀型贫血 HbA HbS × HbA HbS)"""
    return f"""┌─────────────────────────────────────────────────────┐
│  Punnett 方格推算 (常染色体共显性)                    │
│  亲本: {female} × {male}                                        │
├─────────────────────────────────────────────────────┤
│  Ⅰ代:  携带者男性（◐，{male}） —— 携带者女性（◐，{female}） │
│                  ↓                                  │
│  Ⅱ代:  子女25% 正常（□/○，AA）                      │
│         子女50% 携带/轻症（◐，Aa）                   │
│         子女25% 患病（■/●，aa）                      │
│                                                     │
└─────────────────────────────────────────────────────┘"""
