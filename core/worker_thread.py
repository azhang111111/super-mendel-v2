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

        result = simulate_abo_crossover(p1, p2, N)
        self.progress_updated.emit(N, N)
        report = generate_multimode_report("multi_allele", result, self.params, N)
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

        values = simulate_polygenic_trait(
            num_genes, p1, p2, effects=effects,
            base_value=base, num_simulations=N
        )
        self.progress_updated.emit(N, N)
        report = generate_multimode_report("polygenic", values, self.params, N)
        self.simulation_finished.emit(report)
