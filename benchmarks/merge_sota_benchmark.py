"""Merge PRIME 2.1, MixMHCpred 3.0, BigMHC-EL, BigMHC-IM, and Splicing-Opt fusion
into benchmarks/results/benchmark_10papers_summary.json.
"""

from __future__ import annotations

import csv
import json
import math
import time
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import mannwhitneyu

ROOT = Path(__file__).resolve().parent.parent
RES_DIR = ROOT / "benchmarks" / "results"
SUMMARY_PATH = RES_DIR / "benchmark_10papers_summary.json"


def auroc(y_true: list[int], y_score: list[float | None]) -> float | None:
    pairs = [(y, s) for y, s in zip(y_true, y_score) if s is not None and math.isfinite(s)]
    pos = [s for y, s in pairs if y == 1]
    neg = [s for y, s in pairs if y == 0]
    if not pos or not neg:
        return None
    u_stat, _ = mannwhitneyu(pos, neg, alternative="greater")
    return float(u_stat) / (len(pos) * len(neg))


def auprc(y_true: list[int], y_score: list[float | None]) -> float | None:
    pairs = [(y, s) for y, s in zip(y_true, y_score) if s is not None and math.isfinite(s)]
    n_pos = sum(1 for y, _ in pairs if y == 1)
    if n_pos == 0 or n_pos == len(pairs):
        return None
    pairs.sort(key=lambda x: -x[1])
    tp = 0
    ap = 0.0
    for idx, (y, _) in enumerate(pairs, start=1):
        if y == 1:
            tp += 1
            ap += tp / idx
    return ap / n_pos


def topk_precision(y_true: list[int], y_score: list[float | None], k: int = 10) -> float | None:
    pairs = [(y, s) for y, s in zip(y_true, y_score) if s is not None and math.isfinite(s)]
    if not pairs:
        return None
    pairs.sort(key=lambda x: -x[1])
    k_eff = min(k, len(pairs))
    return sum(y for y, _ in pairs[:k_eff]) / k_eff


def load_prime2() -> dict[tuple[str, str], tuple[float, float]]:
    out: dict[tuple[str, str], tuple[float, float]] = {}
    p = RES_DIR / "prime2_predictions.tsv"
    with p.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            out[(r["peptide"].strip().upper(), r["allele"].strip())] = (
                float(r["prime2_score"]),
                -float(r["mixmhcpred_rank"]),
            )
    return out


def load_bigmhc(filename: str, col_hint: str) -> dict[tuple[str, str], float]:
    out: dict[tuple[str, str], float] = {}
    p = RES_DIR / filename
    with p.open(encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        cols = reader.fieldnames or []
        score_col = next((c for c in cols if col_hint.lower() in c.lower()), cols[-1])
        for r in reader:
            pep = r["pep"].strip().upper()
            hla = r["mhc"].strip()
            out[(pep, hla)] = float(r[score_col])
    return out


def main() -> None:
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    prime_map = load_prime2()
    bm_im_map = load_bigmhc("bigmhc_im_predictions.csv", "BigMHC_IM")
    bm_el_map = load_bigmhc("bigmhc_el_predictions.csv", "BigMHC_EL")
    print(f"Loaded PRIME2={len(prime_map)}, BigMHC_IM={len(bm_im_map)}, BigMHC_EL={len(bm_el_map)}")

    # Splicing-optimized weights: binding=0.15, immunogenicity=0.40 (relative 0.2727 / 0.7273)
    w_bind_sp = 0.15 / (0.15 + 0.40)
    w_esm_sp = 0.40 / (0.15 + 0.40)
    # Default weights: binding=0.30, immunogenicity=0.25
    w_bind_def = 0.30 / (0.30 + 0.25)
    w_esm_def = 0.25 / (0.30 + 0.25)
    # Deployed server cooperative immunogenicity: 0.55 * ESM-2 + 0.45 * BigMHC-IM
    w_coop_bm = 0.45
    w_coop_esm = 1.0 - w_coop_bm

    pooled_y: list[int] = []
    pooled: dict[str, list[float | None]] = {
        k: []
        for k in [
            "calis",
            "iedb",
            "mixmhcpred",
            "prime2",
            "bigmhc_el",
            "bigmhc_im",
            "esm2",
            "coop_imm",
            "composite",
            "composite_splicing",
            "composite_coop_default",
            "composite_coop",
        ]
    }

    for paper in summary["papers"]:
        pid = paper["id"]
        pmid = paper["pmid"]
        pred_file = RES_DIR / f"{pid}_PMID{pmid}_predictions.tsv"
        with pred_file.open(encoding="utf-8") as fh:
            recs = list(csv.DictReader(fh, delimiter="\t"))

        y = [int(r["label"]) for r in recs]
        scores: dict[str, list[float | None]] = {k: [] for k in pooled}
        for r in recs:
            key = (r["peptide"].strip().upper(), r["allele"].strip())
            b = float(r["binding_score"])
            e = float(r["esm2_immunogenicity"])
            p2, mix = prime_map.get(key, (None, None))
            bm_im = bm_im_map.get(key)
            coop_imm = (w_coop_esm * e + w_coop_bm * bm_im) if bm_im is not None else e
            scores["calis"].append(float(r["calis_score"]))
            scores["iedb"].append(b)
            scores["mixmhcpred"].append(mix)
            scores["prime2"].append(p2)
            scores["bigmhc_el"].append(bm_el_map.get(key))
            scores["bigmhc_im"].append(bm_im)
            scores["esm2"].append(e)
            scores["coop_imm"].append(coop_imm)
            scores["composite"].append(float(r["epitoperank_composite"]))
            scores["composite_splicing"].append(w_bind_sp * b + w_esm_sp * e)
            scores["composite_coop_default"].append(w_bind_def * b + w_esm_def * coop_imm)
            scores["composite_coop"].append(w_bind_sp * b + w_esm_sp * coop_imm)

        pooled_y.extend(y)
        for k, vals in scores.items():
            pooled[k].extend(vals)
            paper[f"auroc_{k}"] = auroc(y, vals)
            paper[f"auprc_{k}"] = auprc(y, vals)
            paper[f"top10_prec_{k}"] = topk_precision(y, vals, 10)

    def macro(papers_list: list[dict[str, Any]], key: str) -> float:
        vals = [p[key] for p in papers_list if p.get(key) is not None]
        return round(float(np.mean(vals)), 4) if vals else 0.0

    keys = list(pooled.keys())
    splice_papers = [p for p in summary["papers"] if p["category"] == "Splicing Neoantigen"]

    summary["generated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    summary["splicing_weights"] = {
        "binding": 0.15,
        "immunogenicity": 0.40,
        "processing": 0.13,
        "expression": 0.12,
        "effect": 0.12,
        "novelty": 0.08,
    }
    summary["macro_average"] = {}
    summary["splice_macro_average"] = {}
    summary["pooled_overall"] = {}
    for k in keys:
        summary["macro_average"][f"auroc_{k}"] = macro(summary["papers"], f"auroc_{k}")
        summary["macro_average"][f"auprc_{k}"] = macro(summary["papers"], f"auprc_{k}")
        summary["macro_average"][f"top10_prec_{k}"] = macro(summary["papers"], f"top10_prec_{k}")
        summary["splice_macro_average"][f"auroc_{k}"] = macro(splice_papers, f"auroc_{k}")
        summary["splice_macro_average"][f"auprc_{k}"] = macro(splice_papers, f"auprc_{k}")
        summary["pooled_overall"][f"auroc_{k}"] = round(auroc(pooled_y, pooled[k]) or 0.0, 4)
        summary["pooled_overall"][f"auprc_{k}"] = round(auprc(pooled_y, pooled[k]) or 0.0, 4)

    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n=== FULL SOTA BENCHMARK SUMMARY (10 PAPERS, N=2,136) ===")
    print(f"{'Model':20s} | {'All10 AUC':>9} | {'Spl3 AUC':>8} | {'Pool AUC':>8} | {'Pool PRC':>8} | {'Spl3 PRC':>8}")
    print("-" * 76)
    for k in keys:
        print(
            f"{k:20s} | {summary['macro_average'][f'auroc_{k}']:9.4f} | "
            f"{summary['splice_macro_average'][f'auroc_{k}']:8.4f} | "
            f"{summary['pooled_overall'][f'auroc_{k}']:8.4f} | "
            f"{summary['pooled_overall'][f'auprc_{k}']:8.4f} | "
            f"{summary['splice_macro_average'][f'auprc_{k}']:8.4f}"
        )


if __name__ == "__main__":
    main()
