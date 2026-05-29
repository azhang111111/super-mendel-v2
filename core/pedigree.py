"""家系遗传分析引擎 — 三代模拟 + 疾病概率推算 (v2: X连锁支持)"""

import random
import numpy as np
from core.crossover_engine import simulate_crossover_vectorized
from core.sex_chromosome import simulate_sex_chromosome_crossover


def simulate_pedigree(founder_gtypes, inheritance="autosomal", generations=3,
                      children_per_couple=2, num_simulations=10000):
    """
    模拟多代家系遗传。

    founder_gtypes: {"祖父": {"gender":"male","genotype":"X^H Y"}, "祖母": {...}, ...}
    inheritance: "autosomal" | "x_linked"
    generations: 模拟代数 (2-4)
    children_per_couple: 每对夫妻子女人数
    num_simulations: 蒙特卡洛模拟次数

    返回: {
        "generation_1": [{"id": "祖父", "gender": "male", "genotype": "X^H Y", "phenotype": "正常"}, ...],
        "generation_2": [...],
        "generation_3": [...],
        "stats": {...}
    }
    """
    pedigree = {}
    for gen_idx in range(1, generations + 1):
        if gen_idx == 1:
            members = [{"id": name, **info} for name, info in founder_gtypes.items()]
            for m in members:
                if "phenotype" not in m:
                    m["phenotype"] = _classify_phenotype(m["genotype"], inheritance)
        else:
            prev_gen = pedigree[f"generation_{gen_idx - 1}"]
            members = _generate_children(prev_gen, inheritance, children_per_couple)
        pedigree[f"generation_{gen_idx}"] = members

    pedigree["stats"] = _calc_pedigree_stats(pedigree, inheritance)
    return pedigree


def _generate_children(parents, inheritance, children_per_couple):
    """从父母列表模拟产生子代"""
    children = []
    males = [p for p in parents if p.get("gender") == "male"]
    females = [p for p in parents if p.get("gender") == "female"]

    for i in range(min(len(males), len(females))):
        father = males[i]
        mother = females[i]
        for c in range(children_per_couple):
            if inheritance == "x_linked":
                child_gender, child_gt = _make_x_linked_child(mother, father)
            else:
                child_gender, child_gt = _make_autosomal_child(mother, father)

            children.append({
                "id": f"子女{father['id']}-{mother['id']}-{c + 1}",
                "gender": child_gender,
                "genotype": child_gt,
                "phenotype": _classify_phenotype(child_gt, inheritance),
                "father": father["id"],
                "mother": mother["id"],
            })
    return children


def _make_x_linked_child(mother, father):
    """X连锁遗传: 用性染色体引擎生成一个子代"""
    mother_alleles = mother["genotype"].split()
    father_parts = father["genotype"].split()
    father_x = father_parts[0]  # "X^H Y" → "X^H"

    result = simulate_sex_chromosome_crossover(mother_alleles, father_x, 1)
    child_gender = "male" if result["儿子数"] > 0 else "female"
    if child_gender == "male":
        child_gt = list(result["儿子"].keys())[0] if result["儿子"] else "??"
    else:
        child_gt = list(result["女儿"].keys())[0] if result["女儿"] else "??"
    return child_gender, child_gt


def _make_autosomal_child(mother, father):
    """常染色体遗传: 用常染色体引擎生成一个子代"""
    result, _, _ = simulate_crossover_vectorized(
        list(mother["genotype"]), list(father["genotype"]), 1
    )
    child_gender = random.choice(["male", "female"])
    child_gt = list(result.keys())[0] if result else "??"
    return child_gender, child_gt


def _classify_phenotype(genotype, inheritance="autosomal"):
    """根据基因型和遗传方式分类表现型"""
    if genotype == "??":
        return "未知"
    if inheritance == "x_linked":
        return _classify_x_linked(genotype)
    return _classify_autosomal(genotype)


def _classify_x_linked(genotype):
    """X连锁表现型分类: 男性半合子, 女性双X"""
    parts = genotype.split()
    if "Y" in parts:
        x_alleles = [p for p in parts if p.startswith("X")]
        if not x_alleles:
            return "未知"
        return "患病" if _is_mutant_x(x_alleles[0]) else "正常"
    else:
        mut_count = sum(1 for p in parts if _is_mutant_x(p))
        if mut_count == 0:
            return "正常"
        elif mut_count == 1:
            return "携带者"
        else:
            return "患病"


def _is_mutant_x(allele):
    """判断X等位基因是否为突变型 (^后小写字母)"""
    if '^' in allele:
        idx = allele.index('^')
        if idx + 1 < len(allele):
            return allele[idx + 1].islower()
    return any(c.islower() for c in allele)


def _classify_autosomal(genotype):
    """常染色体表现型分类"""
    has_upper = any(c.isupper() for c in genotype)
    has_lower = any(c.islower() for c in genotype)
    if has_upper and has_lower:
        return "携带者"
    elif has_upper:
        return "正常"
    else:
        return "患病"


def _calc_pedigree_stats(pedigree, inheritance):
    """计算每代表现型统计"""
    stats = {}
    for gen_key in ["generation_1", "generation_2", "generation_3"]:
        members = pedigree.get(gen_key, [])
        if not isinstance(members, list):
            continue
        total = len(members)
        affected = sum(1 for m in members if m.get("phenotype") == "患病")
        carrier = sum(1 for m in members if m.get("phenotype") == "携带者")
        stats[gen_key] = {
            "total": total,
            "affected": affected,
            "carrier": carrier,
            "affected_rate": affected / total if total > 0 else 0,
            "carrier_rate": carrier / total if total > 0 else 0,
        }
    return stats


def calculate_disease_risk(parent1_gt, parent2_gt, inheritance="autosomal"):
    """
    计算单对夫妻的子代患病风险。

    返回: {"患病率": 0.25, "携带率": 0.50, "正常率": 0.25, "total": 4}
    """
    if inheritance == "x_linked":
        return _calculate_x_linked_risk(parent1_gt, parent2_gt)

    result, _, _ = simulate_crossover_vectorized(
        list(parent1_gt), list(parent2_gt), 10000
    )
    return _aggregate_risk(result, _classify_autosomal)


def _calculate_x_linked_risk(mother_gt, father_gt):
    """X连锁子代风险计算"""
    mother_alleles = mother_gt.split()
    father_parts = father_gt.split()
    father_x = father_parts[0]

    result = simulate_sex_chromosome_crossover(mother_alleles, father_x, 10000)
    from core.sex_chromosome import analyze_sex_linked
    stats = analyze_sex_linked(result)

    risk = {"total": result["女儿数"] + result["儿子数"]}
    total_d = stats["女儿"]["正常"] + stats["女儿"]["携带者"] + stats["女儿"]["患病"]
    total_s = stats["儿子"]["正常"] + stats["儿子"]["患病"]
    total_all = total_d + total_s

    if total_all > 0:
        risk["儿子患病率"] = round(stats["儿子"]["患病"] / total_all, 4)
        risk["女儿患病率"] = round(stats["女儿"]["患病"] / total_all, 4)
        risk["女儿携带率"] = round(stats["女儿"]["携带者"] / total_all, 4)
        risk["正常率"] = round(
            (stats["女儿"]["正常"] + stats["儿子"]["正常"]) / total_all, 4
        )
    return risk


def _aggregate_risk(result, classifier):
    """聚合风险统计"""
    total = sum(result.values())
    affected = 0
    carrier = 0
    normal = 0
    for gt, count in result.items():
        pheno = classifier(gt)
        if pheno == "患病":
            affected += count
        elif pheno == "携带者":
            carrier += count
        else:
            normal += count
    return {
        "患病率": round(affected / total, 4) if total > 0 else 0,
        "携带率": round(carrier / total, 4) if total > 0 else 0,
        "正常率": round(normal / total, 4) if total > 0 else 0,
        "total": total,
    }
