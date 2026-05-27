"""多基因数量性状模拟引擎 (纯 NumPy, 不依赖 scipy)"""

import numpy as np
from core.crossover_engine import simulate_crossover_vectorized


# 默认基因效应大小 (厘米, 相对基准值)
DEFAULT_EFFECTS = [2.0, 1.5, 1.0, 0.5, 0.3, 0.2, 0.15, 0.1, 0.08, 0.05]
MAX_GENES = 4


def simulate_polygenic_trait(num_genes, parent1_gtypes, parent2_gtypes,
                             effects=None, base_value=170.0,
                             noise_std=2.0, num_simulations=100000):
    """
    多基因数量性状模拟。

    num_genes: 参与性状的基因数 (≤ MAX_GENES)
    parent1_gtypes: list[str], 如 ['Aa', 'Aa', 'Aa', 'Aa']
    parent2_gtypes: list[str], 同上
    effects: 每基因效应列表 (None 则用默认值, AA=effect, Aa=effect/2, aa=0)
    base_value: 性状基准值 (如平均身高 170cm)
    noise_std: 环境噪声标准差
    num_simulations: 模拟次数

    返回: ndarray of trait values, shape (N,)
    """
    assert num_genes <= MAX_GENES, f"最多支持 {MAX_GENES} 个基因, 收到 {num_genes}"

    if effects is None:
        effects = DEFAULT_EFFECTS[:num_genes]

    trait_values = np.zeros(num_simulations)

    for i in range(num_genes):
        _, g1, g2 = simulate_crossover_vectorized(
            list(parent1_gtypes[i]), list(parent2_gtypes[i]), num_simulations
        )
        zygote = np.char.add(g1, g2)

        # 加性效应映射
        effect = effects[i]
        gene_values = np.zeros(num_simulations)
        gene_values[zygote == 'AA'] = effect
        gene_values[zygote == 'Aa'] = effect / 2.0
        gene_values[zygote == 'aa'] = 0.0
        # 处理 aA 反转情况
        gene_values[zygote == 'aA'] = effect / 2.0

        trait_values += gene_values

    # 添加基准值 + 环境噪声
    trait_values += base_value
    trait_values += np.random.normal(0, noise_std, num_simulations)

    return trait_values


def fit_normal(values):
    """
    纯 NumPy 正态分布参数估计。

    返回: (mu, sigma)
    """
    mu = np.mean(values)
    sigma = np.std(values, ddof=1)
    return mu, sigma


def compute_normal_pdf(x, mu, sigma):
    """纯 NumPy 正态分布概率密度函数"""
    return (1.0 / (sigma * np.sqrt(2.0 * np.pi))) * \
           np.exp(-0.5 * ((x - mu) / sigma) ** 2)


def analyze_polygenic_stats(values, expected_mean=None):
    """
    计算多基因性状统计量。

    返回: dict with mean, std, skewness, kurtosis, normality_check
    """
    mu = np.mean(values)
    sigma = np.std(values, ddof=1)

    # 偏度 (Skewness)
    n = len(values)
    skew = (np.sum((values - mu) ** 3) / n) / (sigma ** 3) if sigma > 0 else 0

    # 峰度 (Excess Kurtosis)
    kurt = (np.sum((values - mu) ** 4) / n) / (sigma ** 4) - 3.0 if sigma > 0 else 0

    # 简化正态性检查: |偏度|<0.1 且 |峰度|<0.3 认为近似正态
    normality_ok = abs(skew) < 0.1 and abs(kurt) < 0.3

    result = {
        "mean": round(mu, 2),
        "std": round(sigma, 2),
        "skewness": round(skew, 4),
        "kurtosis": round(kurt, 4),
        "normality_ok": normality_ok,
    }

    if expected_mean is not None:
        result["mean_deviation"] = round(mu - expected_mean, 2)

    return result
