#!/usr/bin/env python3
"""v4 冲分版 · 步骤 3：5 折集成（Ensemble）体检脚本。

自动加载输出目录下所有已训练完成的 fold_0..fold_4 权重，对每条 (peptide, allele)
取多折校准概率均值，显著降低单折方差并提升独立留出集 Hard AUROC 与校准度。
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import statistics
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parent.parent


def _load_v3_eval():
    here = Path(__file__).resolve().parent
    for cand in (here / "03_evaluate_v3_hla.py", LAB_ROOT / "stage3_hla" / "03_evaluate_v3_hla.py"):
        if cand.is_file():
            spec = importlib.util.spec_from_file_location("v3e", cand)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod
    raise FileNotFoundError("请将 03_evaluate_v3_hla.py 放在同级目录或 ../stage3_hla/ 下")


def score_ensemble(fold_dirs: list[Path], pairs: list[tuple[str, str]], v3e) -> list[float]:
    """依次加载各折轻量权重并累加校准概率，最后取均值（省显存）。"""
    acc = [0.0] * len(pairs)
    for fdir in fold_dirs:
        scorer = v3e.LocalPMhcScorer(fdir)
        res = scorer.score_pairs(pairs)
        for i, item in enumerate(res):
            acc[i] += item["score"]
        del scorer
    n = max(1, len(fold_dirs))
    return [round(v / n, 4) for v in acc]


def main() -> None:
    parser = argparse.ArgumentParser(description="v4 5 折集成体检")
    parser.add_argument("--outputs_dir", type=Path, required=True, help="包含 fold_0..fold_4 的目录")
    parser.add_argument("--out_json", type=Path, default=Path("eval_v4_ensemble_report.json"))
    args = parser.parse_args()

    v3e = _load_v3_eval()
    fold_dirs = sorted([d for d in args.outputs_dir.glob("fold_*") if (d / "meta.json").is_file()])
    if not fold_dirs:
        raise FileNotFoundError(f"在 {args.outputs_dir} 下未找到任何 fold_* 权重目录")
    print(f"[v4 集成体检] 检测到 {len(fold_dirs)} 个折权重：{[d.name for d in fold_dirs]}")

    # 1. 经典表位 + HLA 错配
    cor_pairs = [(p, al) for p, al, _, _ in v3e.CLASSIC_PMHC_CASES]
    mis_pairs = [(p, bad) for p, _, bad, _ in v3e.CLASSIC_PMHC_CASES]
    decoys = [("AAAAAAAAA", "HLA-A*02:01"), ("LALALALAL", "HLA-A*02:01"), ("GGGGGGGGG", "HLA-A*02:01"), ("PPPPPPPPP", "HLA-B*07:02")]

    # 2. 拉取远离 v4 训练集（offset=5000）的独立留出集
    test_alleles = ["HLA-A*02:01", "HLA-A*01:01", "HLA-A*03:01", "HLA-A*11:01", "HLA-A*24:02", "HLA-B*07:02", "HLA-B*08:01"]
    h_pos, h_neg = v3e.fetch_hla_holdout(test_alleles, per_allele=30, offset=5000)
    all_pairs = cor_pairs + mis_pairs + decoys + h_pos + h_neg
    all_scores = score_ensemble(fold_dirs, all_pairs, v3e)

    n1 = len(cor_pairs)
    n2 = len(mis_pairs)
    n3 = len(decoys)
    cor_s = all_scores[:n1]
    mis_s = all_scores[n1 : n1 + n2]
    dec_s = all_scores[n1 + n2 : n1 + n2 + n3]
    h_scores = all_scores[n1 + n2 + n3 :]

    print("\n--- 1. 经典表位 & HLA 错配特异性（多折集成） ---")
    for (p, al, bad, desc), s1, s2 in zip(v3e.CLASSIC_PMHC_CASES, cor_s, mis_s):
        print(f"  {p:12s} | 正确 {al:11s}: {s1:.4f} vs 错配 {bad:11s}: {s2:.4f} (差={s1-s2:+.4f}) | {desc}")
    print(f"  ==> 正确均分={statistics.mean(cor_s):.4f} | 错配均分={statistics.mean(mis_s):.4f} | 特异性差值={statistics.mean(cor_s)-statistics.mean(mis_s):+.4f}")
    print(f"\n--- 2. 低复杂度陷阱均分：{statistics.mean(dec_s):.4f} ---")

    y_true = [1] * len(h_pos) + [0] * len(h_neg)
    m = v3e.calc_metrics(y_true, h_scores)
    print(f"\n--- 3. IEDB 带 HLA 独立留出集（offset=5000，正={len(h_pos)}, 负={len(h_neg)}）---")
    print(f"  Ensemble Hard AUROC={m['auroc']} | AUPRC={m['auprc']} | ECE={m['ece']} | TP={m['tp']} FP={m['fp']} TN={m['tn']} FN={m['fn']}")

    report = {
        "n_folds_ensembled": len(fold_dirs),
        "correct_mean": round(statistics.mean(cor_s), 4),
        "mismatch_mean": round(statistics.mean(mis_s), 4),
        "hla_specificity_gap": round(statistics.mean(cor_s) - statistics.mean(mis_s), 4),
        "decoy_mean": round(statistics.mean(dec_s), 4),
        "hard_hla_benchmark": {"n_pos": len(h_pos), "n_neg": len(h_neg), **m},
    }
    args.out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nv4 集成体检报告已保存至：{args.out_json}")


if __name__ == "__main__":
    main()
