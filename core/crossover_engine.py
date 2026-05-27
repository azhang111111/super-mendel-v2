"""NumPy 向量化基因杂交计算核心引擎"""

import numpy as np


def simulate_crossover_vectorized(parent1_alleles, parent2_alleles, num_simulations):
    """
    使用 NumPy 向量化进行大规模基因杂交模拟。

    参数：
        parent1_alleles: 列表/元组，如 ['A', 'a']
        parent2_alleles: 列表/元组，如 ['A', 'a']
        num_simulations: 模拟实验总次数 (如 1,000,000)

    返回：
        result_dict: dict，各基因型的计数 {'AA': N_AA, 'Aa': N_Aa, 'aa': N_aa}
        gametes1: ndarray，parent1 提供的配子数组
        gametes2: ndarray，parent2 提供的配子数组
    """
    # 1. 随机生成 parent1/parent2 提供哪种配子的索引矩阵 (0 或 1)
    p1_indices = np.random.randint(0, 2, size=num_simulations)
    p2_indices = np.random.randint(0, 2, size=num_simulations)

    # 2. 将输入转为 NumPy 数组
    p1_pool = np.array(parent1_alleles)
    p2_pool = np.array(parent2_alleles)

    # 3. 向量化提取配子
    gametes1 = p1_pool[p1_indices]
    gametes2 = p2_pool[p2_indices]

    # 4. 合并为子代基因型（确保排序，避免 'Aa' 和 'aA' 被算作两种）
    zygotes = np.char.add(gametes1, gametes2)
    zygotes = np.where(zygotes == 'aA', 'Aa', zygotes)

    # 5. 使用 np.unique 快速秒级统计数量
    genotypes, counts = np.unique(zygotes, return_counts=True)
    result_dict = dict(zip(genotypes, counts))

    # 6. 确保所有可能的基因型都在结果中
    for gt in ['AA', 'Aa', 'aa']:
        if gt not in result_dict:
            result_dict[gt] = 0

    return result_dict, gametes1, gametes2


def calculate_convergence_curve(gametes1, gametes2, max_points=2000):
    """
    计算随着次数增加，显性比例如何向 0.75 收敛的数据流。

    参数：
        gametes1, gametes2: crossover_engine 输出的配子数组
        max_points: 采样抽稀后的最大点数

    返回：
        attempts: 采样后的实验次数序列
        convergence_ratios: 采样后的累计显性比例序列
    """
    # 只要组合中含有 'A' 即为显性表现型
    is_dominant = (gametes1 == 'A') | (gametes2 == 'A')

    # 计算累计和（进行到第几步时，总共有多少个显性）
    cumulative_dominant = np.cumsum(is_dominant)

    # 计算累计比例: cumulative_dominant / [1, 2, 3, ..., N]
    total = len(is_dominant)
    attempts = np.arange(1, total + 1)
    convergence_ratios = cumulative_dominant / attempts

    # 采样抽稀（防止 Matplotlib 在百万点时卡死）
    sample_rate = max(1, total // max_points)
    return attempts[::sample_rate], convergence_ratios[::sample_rate]


def simulate_multigene_crossover(parent1_gtypes, parent2_gtypes, num_simulations):
    """
    多基因独立分配模拟 (孟德尔第二定律)。

    parent1_gtypes: list[str], 如 ["Aa", "Bb", "CC"]
    parent2_gtypes: list[str], 如 ["Aa", "Bb", "CC"]
    num_simulations: int

    返回: dict, 键为 "AA|Bb|CC" (|分隔防歧义), 值为计数
    """
    num_genes = len(parent1_gtypes)

    all_zygote_parts = []
    for i in range(num_genes):
        _, g1, g2 = simulate_crossover_vectorized(
            list(parent1_gtypes[i]), list(parent2_gtypes[i]), num_simulations
        )
        z = np.char.add(g1, g2)
        mask = np.char.islower(g1) & np.char.isupper(g2)
        z[mask] = np.char.add(g2[mask], g1[mask])
        all_zygote_parts.append(z)

    stacked = np.column_stack(all_zygote_parts)
    combined = stacked[:, 0]
    for j in range(1, num_genes):
        combined = np.char.add(combined, "|")
        combined = np.char.add(combined, stacked[:, j])

    genotypes, counts = np.unique(combined, return_counts=True)
    return dict(zip(genotypes, counts.astype(int)))
