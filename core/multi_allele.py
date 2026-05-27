"""复等位基因引擎 (ABO 血型系统)"""

import numpy as np

# ABO 表现型映射表: 排序后的基因型元组 → 表现型
ABO_PHENOTYPE_MAP = {
    ("I^A", "I^A"): "A型",
    ("I^A", "i"):   "A型",
    ("I^B", "I^B"): "B型",
    ("I^B", "i"):   "B型",
    ("I^A", "I^B"): "AB型",
    ("i", "i"):     "O型",
}


def simulate_abo_crossover(p1_genotype, p2_genotype, num_simulations):
    """
    ABO 血型遗传模拟。

    p1_genotype: 个体基因型 (2 个等位基因), 如 ['I^A', 'i']
    p2_genotype: 同上, 如 ['I^B', 'i']

    返回: {
        "genotype_counts": {"I^A I^B": count, ...},
        "phenotype_counts": {"A型": count, "B型": count, "AB型": count, "O型": count}
    }
    """
    p1_pool = np.array(p1_genotype)
    p2_pool = np.array(p2_genotype)

    p1_idx = np.random.randint(0, len(p1_pool), size=num_simulations)
    p2_idx = np.random.randint(0, len(p2_pool), size=num_simulations)

    g1 = p1_pool[p1_idx]
    g2 = p2_pool[p2_idx]

    # 排序确保 "i I^A" → "I^A i"（字典序确保唯一规范化）
    need_swap = g2 < g1
    a1 = np.where(need_swap, g2, g1)
    a2 = np.where(need_swap, g1, g2)

    zygotes = np.char.add(np.char.add(a1, ' '), a2)
    genotypes, counts = np.unique(zygotes, return_counts=True)
    result_dict = dict(zip(genotypes, counts.astype(int)))

    pheno_counts = {"A型": 0, "B型": 0, "AB型": 0, "O型": 0}
    for gt, count in result_dict.items():
        alleles = tuple(gt.split(' '))
        pheno = ABO_PHENOTYPE_MAP.get(alleles)
        if pheno is None:
            pheno = ABO_PHENOTYPE_MAP.get((alleles[1], alleles[0]), "未知")
        if pheno in pheno_counts:
            pheno_counts[pheno] += count

    return {
        "genotype_counts": result_dict,
        "phenotype_counts": pheno_counts,
    }


def analyze_abo_results(result, p1_genotype, p2_genotype):
    """
    计算 ABO 表现型比例 + 卡方检验。

    根据亲本基因型计算理论比例，做拟合优度检验。
    """
    total = sum(result["phenotype_counts"].values())
    ratios = {
        k: v / total for k, v in result["phenotype_counts"].items()
    }

    # 用 Punnett Square 计算理论比例
    theory = _abo_theory_ratios(p1_genotype, p2_genotype)

    # 卡方检验
    chi2 = 0.0
    df = 0
    for pheno in ["A型", "B型", "AB型", "O型"]:
        observed = result["phenotype_counts"].get(pheno, 0)
        expected = theory.get(pheno, 0) * total
        if expected > 0:
            chi2 += (observed - expected) ** 2 / expected
            df += 1

    df = max(df - 1, 1)
    # df=3 临界值 7.815 (p=0.05)
    verdict = "符合预期 (p > 0.05)" if chi2 < 7.815 else "显著偏离 (p < 0.05)"

    return {
        "phenotype_ratios": ratios,
        "theory_ratios": theory,
        "chi2": round(chi2, 3),
        "verdict": verdict,
    }


def _abo_theory_ratios(p1, p2):
    """Punnett Square 穷举 ABO 理论比例"""
    offspring = []
    for a1 in p1:
        for a2 in p2:
            alleles = tuple(sorted([a1, a2]))
            pheno = ABO_PHENOTYPE_MAP.get(alleles, "未知")
            offspring.append(pheno)
    total = len(offspring)
    return {p: offspring.count(p) / total for p in set(offspring)}
