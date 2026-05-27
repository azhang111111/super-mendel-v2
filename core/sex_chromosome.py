"""X/Y 性染色体遗传模拟引擎"""

import numpy as np


def simulate_sex_chromosome_crossover(mother_X_alleles, father_X_allele, num_simulations):
    """
    性染色体遗传模拟。

    mother_X_alleles: 母亲两条 X 的等位基因, 如 ['X^A', 'X^a']
    father_X_allele:  父亲唯一的 X 等位基因, 如 'X^A'
                       (父亲还有一条Y, 不携带此基因)

    子代性别由父亲决定: 父亲提供X→女儿(XX), 父亲提供Y→儿子(XY)

    返回: {
        "女儿": {"X^A X^A": count, ...},
        "儿子": {"X^A Y": count, "X^a Y": count}
    }
    """
    # 母亲随机提供一条 X (等概率)
    mom_idx = np.random.randint(0, 2, size=num_simulations)
    mom_pool = np.array(mother_X_alleles)
    maternal_gamete = mom_pool[mom_idx]

    # 父亲随机提供 X 或 Y (各 50%)
    is_female = np.random.random(num_simulations) < 0.5
    paternal_gamete = np.where(is_female, father_X_allele, 'Y')

    # 女儿: 两条X, 中间加空格
    daughter_mask = is_female
    daughter_pair = np.char.add(
        np.char.add(maternal_gamete[daughter_mask], ' '),
        paternal_gamete[daughter_mask]
    )
    d_gtypes, d_counts = np.unique(daughter_pair, return_counts=True)

    # 儿子: 母亲的X + Y, 中间加空格 (半合子)
    son_mask = ~is_female
    son_pair = np.char.add(
        np.char.add(maternal_gamete[son_mask], ' '),
        np.full(son_mask.sum(), 'Y')
    )
    s_gtypes, s_counts = np.unique(son_pair, return_counts=True)

    return {
        "女儿": dict(zip(d_gtypes, d_counts.astype(int))),
        "儿子": dict(zip(s_gtypes, s_counts.astype(int))),
        "女儿数": int(daughter_mask.sum()),
        "儿子数": int(son_mask.sum()),
    }


def analyze_sex_linked(result):
    """
    按性别分层统计, 包含半合子表现型判定。

    X连锁隐性遗传: 大写字母 = 正常显性, 小写字母 = 突变隐性
    儿子只有一条X, 直接表现该X上的等位基因。
    女儿需要两条X都带小写才表现隐性。

    返回: dict 包含女儿和儿子各自的正常/患病统计
    """
    def is_mutant(allele_str):
        """判断是否为突变等位基因 (^后紧邻字符为小写即隐性突变)"""
        if '^' in allele_str:
            idx = allele_str.index('^')
            if idx + 1 < len(allele_str):
                return allele_str[idx + 1].islower()
        return any(c.islower() for c in allele_str)

    # 女儿统计: 两条X
    daughters = result.get("女儿", {})
    daughter_normal = 0
    daughter_carrier = 0
    daughter_affected = 0
    for gt, count in daughters.items():
        alleles = gt.split()
        if len(alleles) == 2:
            mut_count = sum(1 for a in alleles if is_mutant(a))
            if mut_count == 0:
                daughter_normal += count
            elif mut_count == 1:
                daughter_carrier += count
            else:
                daughter_affected += count

    # 儿子统计: 一条X + Y
    sons = result.get("儿子", {})
    son_normal = 0
    son_affected = 0
    for gt, count in sons.items():
        if is_mutant(gt):
            son_affected += count
        else:
            son_normal += count

    total_daughters = daughter_normal + daughter_carrier + daughter_affected
    total_sons = son_normal + son_affected

    return {
        "女儿": {
            "正常": daughter_normal,
            "携带者": daughter_carrier,
            "患病": daughter_affected,
            "正常率": daughter_normal / total_daughters if total_daughters > 0 else 0,
        },
        "儿子": {
            "正常": son_normal,
            "患病": son_affected,
            "正常率": son_normal / total_sons if total_sons > 0 else 0,
            "患病率": son_affected / total_sons if total_sons > 0 else 0,
        },
    }
