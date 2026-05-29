"""表现型、基因型比例统计与分离比偏离度结算器"""

import numpy as np


def calculate_theory_ratios(parent1, parent2):
    """
    根据亲本基因型动态计算理论比例。
    用 Punnett Square 穷举所有可能的配子组合。
    """
    # 提取等位基因
    p1_a = list(parent1)  # e.g. ['A', 'a']
    p2_a = list(parent2)  # e.g. ['A', 'a']

    # 穷举所有配子组合（Punnett Square）
    offspring = []
    for a1 in p1_a:
        for a2 in p2_a:
            # 统一排序：确保 Aa 而不是 aA
            if a1 == 'a' and a2 == 'A':
                offspring.append('Aa')
            elif a1 == 'A' and a2 == 'a':
                offspring.append('Aa')
            else:
                offspring.append(a1 + a2)

    total = len(offspring)
    theory_genotype = {
        "AA": offspring.count("AA") / total,
        "Aa": offspring.count("Aa") / total,
        "aa": offspring.count("aa") / total,
    }

    dominant_total = offspring.count("AA") + offspring.count("Aa")
    theory_dominant = dominant_total / total
    theory_recessive = offspring.count("aa") / total

    return theory_genotype, theory_dominant, theory_recessive


def analyze_genotype_ratios(result_dict, total_simulations, parent1, parent2):
    """计算基因型比例和理论偏离度（动态理论值）"""
    theory_genotype, _, _ = calculate_theory_ratios(parent1, parent2)
    ratios = {}
    deviation = {}

    for gt in ["AA", "Aa", "aa"]:
        count = result_dict.get(gt, 0)
        ratio = count / total_simulations
        ratios[gt] = ratio
        deviation[gt] = (ratio - theory_genotype[gt]) * 100

    return ratios, deviation, theory_genotype


def analyze_phenotype_ratios(result_dict, total_simulations, parent1, parent2):
    """计算表现型比例（显性:隐性）（动态理论值）"""
    _, theory_dominant, theory_recessive = calculate_theory_ratios(parent1, parent2)

    dominant_count = result_dict.get("AA", 0) + result_dict.get("Aa", 0)
    recessive_count = result_dict.get("aa", 0)

    phenotype_counts = {"显性": dominant_count, "隐性": recessive_count}
    phenotype_ratios = {
        "显性": dominant_count / total_simulations,
        "隐性": recessive_count / total_simulations,
    }

    deviation = {
        "显性": (phenotype_ratios["显性"] - theory_dominant) * 100,
        "隐性": (phenotype_ratios["隐性"] - theory_recessive) * 100,
    }

    return phenotype_ratios, phenotype_counts, deviation, theory_dominant, theory_recessive


def chi_square_test(observed_dict, total_simulations, parent1, parent2):
    """卡方拟合优度检验（动态理论值）"""
    theory_genotype, _, _ = calculate_theory_ratios(parent1, parent2)

    # 计算实际自由度（排除期望为 0 的类别）
    df = sum(1 for v in theory_genotype.values() if v > 0) - 1
    # 临界值映射：df=0 不检验, df=1→3.841, df=2→5.991
    crit_table = {0: 0, 1: 3.841, 2: 5.991}
    critical = crit_table.get(df, 5.991)

    chi2 = 0.0
    for gt in ["AA", "Aa", "aa"]:
        observed = observed_dict.get(gt, 0)
        exp = theory_genotype[gt] * total_simulations
        if exp > 0:
            chi2 += (observed - exp) ** 2 / exp

    if df == 0:
        p_approx = "无法检验（自由度=0，结果完全确定）"
    else:
        p_approx = "符合预期 (p > 0.05)" if chi2 < critical else "显著偏离 (p < 0.05)"

    return chi2, p_approx, theory_genotype


def generate_summary_report(result_dict, total_simulations,
                            parent1, parent2, convergence_data):
    """生成完整的实验摘要报告（动态理论值）"""
    genotype_ratios, genotype_deviation, theory_genotype = analyze_genotype_ratios(
        result_dict, total_simulations, parent1, parent2)
    pheno_ratios, pheno_counts, pheno_deviation, theory_dominant, theory_recessive = \
        analyze_phenotype_ratios(result_dict, total_simulations, parent1, parent2)
    chi2, chi2_verdict, theory_genotype_for_chi2 = chi_square_test(
        result_dict, total_simulations, parent1, parent2)

    report = {
        "parent1": parent1,
        "parent2": parent2,
        "total_simulations": total_simulations,
        "genotype_counts": {k: int(v) for k, v in result_dict.items()},
        "genotype_ratios": {k: round(v, 4) for k, v in genotype_ratios.items()},
        "genotype_deviation_pct": {k: round(v, 2) for k, v in genotype_deviation.items()},
        "theory_genotype": {k: round(v, 4) for k, v in theory_genotype.items()},
        "theory_dominant": round(theory_dominant, 4),
        "theory_recessive": round(theory_recessive, 4),
        "phenotype_counts": pheno_counts,
        "phenotype_ratios": {k: round(v, 4) for k, v in pheno_ratios.items()},
        "phenotype_deviation_pct": {k: round(v, 2) for k, v in pheno_deviation.items()},
        "chi2_statistic": round(chi2, 3),
        "chi2_verdict": chi2_verdict,
        "convergence_x": convergence_data[0].tolist() if convergence_data else [],
        "convergence_y": convergence_data[1].tolist() if convergence_data else [],
    }

    return report


# ══════════════════════════════════════════════
# v2.0 新增: 多模式统计分析
# ══════════════════════════════════════════════


def analyze_multigene_ratios(result_dict, total_simulations, parent1_gtypes, parent2_gtypes):
    """
    多基因独立分配统计分析。

    result_dict: 键为 "AA|Bb|CC" 格式
    返回基因型数量 + 表现型按基因拆分统计
    """
    genotype_count = len(result_dict)
    # 计算每个基因的独立表现型比例
    per_gene_stats = {}
    for i, (p1, p2) in enumerate(zip(parent1_gtypes, parent2_gtypes)):
        gene_results = {}
        total = 0
        for combo_key, count in result_dict.items():
            parts = combo_key.split("|")
            if i < len(parts):
                gt = parts[i]
                gene_results[gt] = gene_results.get(gt, 0) + count
                total += count
        per_gene_stats[f"gene_{i}"] = {
            "parental": f"{p1} x {p2}",
            "ratios": {k: round(v / total, 4) for k, v in gene_results.items()} if total > 0 else {},
            "counts": gene_results,
        }

    return {
        "total_genotypes": genotype_count,
        "total_simulations": total_simulations,
        "per_gene_breakdown": per_gene_stats,
        "result_dict": dict(result_dict),
    }


def analyze_sex_linked_stats(result, total_simulations):
    """
    性染色体统计包装 (调用 sex_chromosome.analyze_sex_linked 后格式化输出)
    """
    from core.sex_chromosome import analyze_sex_linked
    analysis = analyze_sex_linked(result)
    return {
        "total_simulations": total_simulations,
        "daughter_count": result.get("女儿数", 0),
        "son_count": result.get("儿子数", 0),
        "daughter_stats": analysis.get("女儿", {}),
        "son_stats": analysis.get("儿子", {}),
    }


def analyze_abo_stats(phenotype_counts, total_simulations):
    """ABO 表现型统计格式化"""
    return {
        "total_simulations": total_simulations,
        "phenotype_counts": phenotype_counts,
        "ratios": {k: round(v / total_simulations, 4)
                   for k, v in phenotype_counts.items()},
    }


def analyze_polygenic_stats_wrapper(values, expected_mean=None):
    """多基因性状统计包装 (调用 polygenic.analyze_polygenic_stats 后格式化)"""
    from core.polygenic import analyze_polygenic_stats, fit_normal
    stats = analyze_polygenic_stats(values, expected_mean)
    mu, sigma = fit_normal(values)
    stats["fit_mean"] = round(mu, 2)
    stats["fit_std"] = round(sigma, 2)
    stats["values"] = values
    stats["min"] = round(float(np.min(values)), 2)
    stats["max"] = round(float(np.max(values)), 2)
    stats["median"] = round(float(np.median(values)), 2)
    return stats


def generate_multimode_report(mode, engine_result, params, total_simulations):
    """
    统一的多模式报告生成入口。

    mode: "classic" | "multigene" | "sex" | "multi_allele" | "polygenic"
    engine_result: 引擎函数返回的原始结果
    params: 参数字典
    total_simulations: 总模拟次数
    """
    report = {
        "mode": mode,
        "total_simulations": total_simulations,
    }

    if mode == "multigene":
        report.update(analyze_multigene_ratios(
            engine_result, total_simulations,
            params.get("parent1_gtypes", []),
            params.get("parent2_gtypes", []),
        ))
    elif mode == "sex":
        report.update(analyze_sex_linked_stats(engine_result, total_simulations))
    elif mode == "multi_allele":
        report.update(analyze_abo_stats(
            engine_result.get("phenotype_counts", {}),
            total_simulations,
        ))
    elif mode == "polygenic":
        report.update(analyze_polygenic_stats_wrapper(
            engine_result,
            params.get("expected_mean"),
        ))
    elif mode == "disease":
        report.update({
            "disease_name": engine_result.get("disease_name", ""),
            "parent1": engine_result.get("parent1", ""),
            "parent2": engine_result.get("parent2", ""),
            "offspring_risk": engine_result.get("offspring_risk", {}),
            "pedigree": engine_result.get("pedigree", {}),
        })
    elif mode == "classic":
        from core.crossover_engine import calculate_convergence_curve
        if isinstance(engine_result, tuple) and len(engine_result) == 3:
            result_dict, gametes1, gametes2 = engine_result
            conv = calculate_convergence_curve(gametes1, gametes2)
            report.update(generate_summary_report(
                result_dict, total_simulations,
                params.get("parent1", "Aa"),
                params.get("parent2", "Aa"),
                conv,
            ))
        else:
            report["error"] = "classic 模式引擎结果格式不符预期"

    return report
