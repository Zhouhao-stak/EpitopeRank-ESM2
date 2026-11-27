#!/usr/bin/env python3
"""v4 冲分版 · 步骤 1：扩容版 HLA-I 数据集构建（支持 CEDAR 自动合并 + HLA 错配负样本）。

相比 v3 的 3 项提分升级：
1. 数据量翻倍：18 个高频人类 HLA-I 等位基因，每等位基因扩容至 800 条实测 Positive / Negative。
2. 自动尝试合并 CEDAR 癌症表位专库（Colab 海外环境可直连；若不可达自动跳过不中断）。
3. 负样本加入 10%「HLA 错配负样本」（把 A*02:01 强表位配给 B*07:02 等不兼容等位基因），
   强化模型对 HLA 结合槽互补关系的精准识别。
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import random
import time
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parent.parent


def _load_v3_builder():
    here = Path(__file__).resolve().parent
    for cand in (here / "01_build_hla_dataset.py", LAB_ROOT / "stage3_hla" / "01_build_hla_dataset.py"):
        if cand.is_file():
            spec = importlib.util.spec_from_file_location("b3", cand)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod
    raise FileNotFoundError("请将 01_build_hla_dataset.py 放在同级目录或 ../stage3_hla/ 下")


def fetch_from_endpoint(
    base_url: str,
    alleles: list[str],
    measure: str,
    per_allele: int,
    max_offset: int,
    source_tag: str,
    v3,
) -> list[dict]:
    """从指定 IEDB/CEDAR Query API 按等位基因拉取实测记录。"""
    label = 1 if measure == "Positive" else 0
    collected: dict[tuple[str, str], dict] = {}
    for allele in alleles:
        got = 0
        offset = 0
        while got < per_allele and offset < max_offset:
            params = urllib.parse.urlencode({
                "mhc_restriction": f"eq.{allele}",
                "qualitative_measure": f"eq.{measure}",
                "select": "tcell_id,linear_sequence,mhc_restriction",
                "order": "tcell_id.asc",
                "limit": 500,
                "offset": offset,
            })
            try:
                rows = v3.http_get_json(f"{base_url}?{params}", timeout=30)
            except Exception as exc:
                print(f"  ! [{source_tag}] {allele} ({measure}) 跳过：{exc}")
                break
            if not rows:
                break
            for r in rows:
                pep = v3.clean_peptide(r.get("linear_sequence", ""), min_len=8, max_len=14)
                if not pep or (pep, allele) in collected:
                    continue
                collected[(pep, allele)] = {
                    "peptide": pep,
                    "allele": allele,
                    "hla_pseudo": v3.HLA_PSEUDO_SEQS[allele],
                    "label": label,
                    "source": source_tag,
                }
                got += 1
                if got >= per_allele:
                    break
            offset += 500
            if len(rows) < 500:
                break
        if got:
            print(f"  [{source_tag} | {measure:8s}] {allele:12s}: {got:4d} 条")
        time.sleep(0.1)
    return list(collected.values())


def build_hla_mismatch_negatives(
    pos_records: list[dict],
    excluded: set[tuple[str, str]],
    target_total: int,
    v3,
    seed: int = 42,
) -> list[dict]:
    """构造 HLA 错配负样本：把真实阳性表位配给同族差异大的错误 HLA 等位基因。"""
    rng = random.Random(seed)
    # 明确不兼容的等位基因映射（例如 A*02 疏水锚定 vs A*11 碱性锚定 vs B*07 脯氨酸锚定）
    incompatible = {
        "HLA-A*02:01": ["HLA-A*11:01", "HLA-B*07:02", "HLA-B*27:05", "HLA-A*01:01"],
        "HLA-A*11:01": ["HLA-A*02:01", "HLA-B*07:02", "HLA-B*44:02"],
        "HLA-A*03:01": ["HLA-A*02:01", "HLA-B*07:02", "HLA-B*44:02"],
        "HLA-A*24:02": ["HLA-A*11:01", "HLA-B*07:02", "HLA-B*27:05"],
        "HLA-B*07:02": ["HLA-A*02:01", "HLA-A*11:01", "HLA-B*44:02"],
        "HLA-B*08:01": ["HLA-A*02:01", "HLA-B*44:02", "HLA-A*24:02"],
    }
    all_alleles = list(v3.HLA_PSEUDO_SEQS.keys())
    pool = list(pos_records)
    rng.shuffle(pool)
    results: dict[tuple[str, str], dict] = {}
    for r in pool:
        if len(results) >= target_total:
            break
        pep, orig_al = r["peptide"], r["allele"]
        cands = incompatible.get(orig_al) or [a for a in all_alleles if a != orig_al]
        wrong_al = rng.choice(cands)
        if (pep, wrong_al) in excluded or (pep, wrong_al) in results:
            continue
        results[(pep, wrong_al)] = {
            "peptide": pep,
            "allele": wrong_al,
            "hla_pseudo": v3.HLA_PSEUDO_SEQS[wrong_al],
            "label": 0,
            "source": "hla_mismatch_negative",
        }
    print(f"  已生成 HLA 错配负样本：{len(results)} 条")
    return list(results.values())


def main() -> None:
    parser = argparse.ArgumentParser(description="构建 v4 扩容版 HLA-I 5 折数据集")
    parser.add_argument("--output", type=Path, default=Path("data/dataset_v4_hla_5fold.csv"))
    parser.add_argument("--per_allele", type=int, default=800, help="每个 HLA 最多拉取的正样本数（v3 为 350）")
    parser.add_argument("--neg_ratio", type=float, default=1.25)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    v3 = _load_v3_builder()
    alleles = list(v3.HLA_PSEUDO_SEQS.keys())

    print(f"[1/6] 从 IEDB 主库扩容拉取 {len(alleles)} 个 HLA-I 正样本（每等位基因上限 {args.per_allele}）...")
    pos_map: dict[tuple[str, str], dict] = {}
    for r in fetch_from_endpoint(
        "https://query-api.iedb.org/tcell_search", alleles, "Positive", args.per_allele, 4500, "iedb_hla_positive", v3
    ):
        pos_map[(r["peptide"], r["allele"])] = r

    print("\n[2/6] 尝试合并 CEDAR 癌症表位专库正样本（若网络不可达自动跳过）...")
    for r in fetch_from_endpoint(
        "https://query-api.cedar.iedb.org/tcell_search", alleles, "Positive", 250, 1500, "cedar_cancer_positive", v3
    ):
        pos_map[(r["peptide"], r["allele"])] = r

    pos_records = list(pos_map.values())
    pos_keys = set(pos_map.keys())
    print(f"  正样本去重汇总：{len(pos_records)} 条")

    total_neg = int(round(len(pos_records) * args.neg_ratio))
    n_hard = int(round(total_neg * 0.50))
    n_normal = int(round(total_neg * 0.25))
    n_mismatch = int(round(total_neg * 0.13))
    n_shuf = max(150, total_neg - n_hard - n_normal - n_mismatch)

    print(f"\n[3/6] 拉取 IEDB + CEDAR 实测 Negative 困难负样本（目标 {n_hard} 条）...")
    per_al_neg = max(150, int(n_hard / len(alleles) * 1.8))
    neg_hard_map: dict[tuple[str, str], dict] = {}
    for r in fetch_from_endpoint(
        "https://query-api.iedb.org/tcell_search", alleles, "Negative", per_al_neg, 4500, "iedb_hla_negative_hard", v3
    ):
        if (r["peptide"], r["allele"]) not in pos_keys:
            neg_hard_map[(r["peptide"], r["allele"])] = r
    for r in fetch_from_endpoint(
        "https://query-api.cedar.iedb.org/tcell_search", alleles, "Negative", 200, 1500, "cedar_cancer_negative_hard", v3
    ):
        if (r["peptide"], r["allele"]) not in pos_keys:
            neg_hard_map[(r["peptide"], r["allele"])] = r
    hard_neg = list(neg_hard_map.values())
    random.Random(args.seed).shuffle(hard_neg)
    hard_neg = hard_neg[:n_hard]
    excluded = pos_keys | {(r["peptide"], r["allele"]) for r in hard_neg}
    print(f"  保留困难负样本：{len(hard_neg)} 条")

    print(f"\n[4/6] 采样 UniProt 人类正常蛋白负样本（目标 {n_normal} 条）...")
    proteins = v3.fetch_uniprot_human_proteins(max_proteins=1800)
    normal_neg = v3.sample_normal_pairs(proteins, pos_records, excluded, target_total=n_normal, seed=args.seed)
    excluded |= {(r["peptide"], r["allele"]) for r in normal_neg}

    print(f"\n[5/6] 生成 HLA 错配负样本（{n_mismatch} 条）与乱序/陷阱负样本（{n_shuf} 条）...")
    mismatch_neg = build_hla_mismatch_negatives(pos_records, excluded, target_total=n_mismatch, v3=v3, seed=args.seed)
    excluded |= {(r["peptide"], r["allele"]) for r in mismatch_neg}
    shuf_neg = v3.build_shuffled_and_decoy_pairs(pos_records, excluded, target_total=n_shuf, seed=args.seed)

    print("\n[6/6] 合并与防泄漏 5 折切分...")
    all_records = pos_records + hard_neg + normal_neg + mismatch_neg + shuf_neg
    random.Random(args.seed).shuffle(all_records)
    all_records = v3.assign_folds(all_records, n_splits=5, seed=args.seed)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = ["peptide", "allele", "hla_pseudo", "label", "fold", "cluster_id", "length", "source"]
    with args.output.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in all_records:
            w.writerow({
                "peptide": r["peptide"],
                "allele": r["allele"],
                "hla_pseudo": r["hla_pseudo"],
                "label": r["label"],
                "fold": r["fold"],
                "cluster_id": r["cluster_id"],
                "length": len(r["peptide"]),
                "source": r["source"],
            })

    print(f"\nv4 扩容数据集已保存至：{args.output}（共 {len(all_records)} 条）")
    print("  来源构成：", dict(Counter(r["source"] for r in all_records)))


if __name__ == "__main__":
    main()
