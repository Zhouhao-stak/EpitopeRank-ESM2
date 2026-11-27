"""EpitopeRank (SpliceGAIP_ESM2) 10-Paper Real Published Data Benchmark.

Fetches 10 real, peer-reviewed cancer & splicing neoantigen datasets directly
from the official IEDB Query API (indexed by PubMed ID), saves each dataset as
an auditable TSV under benchmarks/datasets/, and evaluates the actual
EpitopeRank scoring stack:
  1. Calis physicochemical baseline (epitoperank.peptide.properties)
  2. IEDB NetMHCpan-4.1 EL binding (epitoperank.peptide.iedb)
  3. ESM-2-650M LoRA 5-fold ensemble (epitoperank.peptide.esm2_client)
  4. EpitopeRank Composite (epitoperank.peptide.scoring: binding + ESM-2)
"""

from __future__ import annotations

import csv
import json
import math
import os
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import requests
from scipy.stats import mannwhitneyu

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from epitoperank.llm.envfile import load_env_values
from epitoperank.peptide import esm2_client, properties, scoring
from epitoperank.peptide.iedb import IedbClient

load_env_values()

BENCH_DIR = ROOT / "benchmarks"
DATA_DIR = BENCH_DIR / "datasets"
OUT_DIR = BENCH_DIR / "results"
DATA_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR.mkdir(parents=True, exist_ok=True)

SUPPORTED_HLAS = esm2_client.SUPPORTED_HLAS

# 10 real, peer-reviewed cancer & mis-splicing neoantigen papers (2015-2026)
PAPERS: list[dict[str, str]] = [
    {"id": "P01", "pmid": "40273911", "short": "Cell 2025 (Mis-splicing Neoantigens)", "category": "Splicing Neoantigen"},
    {"id": "P02", "pmid": "42680560", "short": "Genome Res 2026 (Neojunction Splicing)", "category": "Splicing Neoantigen"},
    {"id": "P03", "pmid": "37192158", "short": "PNAS 2023 (IRIS Alternative Splicing)", "category": "Splicing Neoantigen"},
    {"id": "P04", "pmid": "39753970", "short": "Nat Med 2025 (Melanoma Neoantigen TCR)", "category": "Clinical Neoantigen"},
    {"id": "P05", "pmid": "33479501", "short": "Nat Med 2021 (Neoantigen Vaccine Memory)", "category": "Clinical Neoantigen"},
    {"id": "P06", "pmid": "27198675", "short": "Science 2016 (Stronen Melanoma)", "category": "Cancer Neoantigen"},
    {"id": "P07", "pmid": "25837513", "short": "Science 2015 (Carreno DC Vaccine)", "category": "Cancer Neoantigen"},
    {"id": "P08", "pmid": "38244726", "short": "Gastroenterology 2024 (Lynch CRC)", "category": "Cancer Neoantigen"},
    {"id": "P09", "pmid": "37586771", "short": "JITC 2023 (TNBC Neoantigen Vaccine)", "category": "Cancer Neoantigen"},
    {"id": "P10", "pmid": "39840067", "short": "Front Immunol 2024 (VACCIMEL Melanoma)", "category": "Cancer Vaccine"},
]


def auroc(y_true: list[int], y_score: list[float]) -> float | None:
    pairs = [(y, s) for y, s in zip(y_true, y_score) if s is not None and math.isfinite(s)]
    pos = [s for y, s in pairs if y == 1]
    neg = [s for y, s in pairs if y == 0]
    if not pos or not neg:
        return None
    u_stat, _ = mannwhitneyu(pos, neg, alternative="greater")
    return float(u_stat) / (len(pos) * len(neg))


def auprc(y_true: list[int], y_score: list[float]) -> float | None:
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


def topk_precision(y_true: list[int], y_score: list[float], k: int = 10) -> float | None:
    pairs = [(y, s) for y, s in zip(y_true, y_score) if s is not None and math.isfinite(s)]
    if not pairs:
        return None
    pairs.sort(key=lambda x: -x[1])
    k_eff = min(k, len(pairs))
    return sum(y for y, _ in pairs[:k_eff]) / k_eff


def fetch_paper_dataset(paper: dict[str, str]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    pmid = paper["pmid"]
    url = "https://query-api.iedb.org/tcell_search"
    rows_raw: list[dict[str, Any]] = []
    offset = 0
    while True:
        params = {
            "select": "linear_sequence,mhc_allele_name,qualitative_measure,pubmed_id,reference_date,journal_name,reference_title",
            "pubmed_id": f"eq.{pmid}",
            "mhc_class": "eq.I",
            "limit": "5000",
        }
        if offset > 0:
            params["offset"] = str(offset)
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        batch = resp.json()
        rows_raw.extend(batch)
        if len(batch) < 5000:
            break
        offset += 5000

    meta = {
        "id": paper["id"],
        "pmid": pmid,
        "short": paper["short"],
        "category": paper["category"],
        "journal": "",
        "year": "",
        "title": "",
        "authors": "",
    }
    pos_set: set[tuple[str, str]] = set()
    neg_set: set[tuple[str, str]] = set()
    for row in rows_raw:
        if not meta["title"] and row.get("reference_title"):
            meta["journal"] = str(row.get("journal_name") or "")
            meta["year"] = str(row.get("reference_date") or "")
            meta["title"] = str(row.get("reference_title") or "")
            authors = row.get("reference_authors") or []
            meta["authors"] = authors[0][:80] if isinstance(authors, list) and authors else str(authors)[:80]
        pep = str(row.get("linear_sequence") or "").strip().upper()
        hla = str(row.get("mhc_allele_name") or "").strip()
        qual = str(row.get("qualitative_measure") or "").strip()
        if not (8 <= len(pep) <= 11) or not pep.isalpha() or hla not in SUPPORTED_HLAS:
            continue
        if qual.startswith("Positive"):
            pos_set.add((pep, hla))
        elif qual == "Negative":
            neg_set.add((pep, hla))

    neg_set -= pos_set  # If any assay was positive for a peptide-HLA pair, treat as positive
    records: list[dict[str, Any]] = []
    for pep, hla in sorted(pos_set):
        records.append({"peptide": pep, "allele": hla, "label": 1})
    for pep, hla in sorted(neg_set):
        records.append({"peptide": pep, "allele": hla, "label": 0})

    # Save auditable TSV
    tsv_path = DATA_DIR / f"{paper['id']}_PMID{pmid}.tsv"
    with tsv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["peptide", "allele", "label"], delimiter="\t")
        writer.writeheader()
        writer.writerows(records)

    meta["n_pos"] = len(pos_set)
    meta["n_neg"] = len(neg_set)
    meta["n_total"] = len(records)
    meta["tsv_path"] = str(tsv_path)
    return meta, records


def main() -> None:
    print("=== EpitopeRank (SpliceGAIP_ESM2) 10-Paper Real Benchmark ===", flush=True)
    esm_st = esm2_client.status()
    print("ESM-2 status:", json.dumps(esm_st, ensure_ascii=False), flush=True)
    if not esm_st.get("available"):
        raise RuntimeError(f"ESM-2 service unavailable: {esm_st}")

    iedb = IedbClient(cache_dir=BENCH_DIR / "iedb_cache", timeout=45, min_interval=0.15)

    all_papers_meta: list[dict[str, Any]] = []
    all_records_by_paper: dict[str, list[dict[str, Any]]] = {}
    unique_pairs: set[tuple[str, str]] = set()

    print("\n[1/4] Fetching 10 real published datasets from IEDB...", flush=True)
    for paper in PAPERS:
        meta, recs = fetch_paper_dataset(paper)
        all_papers_meta.append(meta)
        all_records_by_paper[paper["id"]] = recs
        for r in recs:
            unique_pairs.add((r["peptide"], r["allele"]))
        print(
            f"  {meta['id']} PMID:{meta['pmid']} | {meta['short']} | "
            f"pos={meta['n_pos']}, neg={meta['n_neg']}, total={meta['n_total']}",
            flush=True,
        )

    print(f"\nTotal unique (peptide, HLA) pairs across 10 papers: {len(unique_pairs)}", flush=True)

    # 2. Score all unique pairs with IEDB NetMHCpan-4.1 EL (grouped by allele)
    print("\n[2/4] Running IEDB NetMHCpan-4.1 EL binding predictions...", flush=True)
    by_allele: dict[str, list[str]] = {}
    for pep, hla in sorted(unique_pairs):
        by_allele.setdefault(hla, []).append(pep)

    iedb_map: dict[tuple[str, str], float] = {}
    t0 = time.perf_counter()
    for hla, peps in sorted(by_allele.items()):
        # Batch by length to be safe and clean with IEDB NetMHCpan
        by_len: dict[int, list[str]] = {}
        for p in peps:
            by_len.setdefault(len(p), []).append(p)
        for length, lpeps in sorted(by_len.items()):
            for start in range(0, len(lpeps), 100):
                chunk = lpeps[start : start + 100]
                try:
                    preds = iedb.predict_mhci(chunk, [hla], lengths=[length], method="netmhcpan_el")
                    for row in preds:
                        p_key = str(row.get("peptide") or "").strip().upper()
                        a_key = str(row.get("allele") or "").strip()
                        pr = row.get("percentile_rank")
                        if p_key and a_key and pr is not None:
                            pr_f = float(pr)
                            prev = iedb_map.get((p_key, a_key))
                            if prev is None or pr_f < prev:
                                iedb_map[(p_key, a_key)] = pr_f
                except Exception as exc:
                    print(f"  [WARN] IEDB failed for {hla} len={length} offset={start}: {exc}", flush=True)
    print(f"  IEDB scored {len(iedb_map)}/{len(unique_pairs)} pairs in {time.perf_counter() - t0:.1f}s", flush=True)

    # 3. Score all unique pairs with 128-core remote ESM-2-650M LoRA (v4 + v5-beta 5-fold)
    print("\n[3/4] Running 128-core ESM-2-650M LoRA (v4 + v5-beta 5-fold) immunogenicity scoring...", flush=True)
    t1 = time.perf_counter()
    esm_rows = [{"peptide": p, "allele": a} for p, a in sorted(unique_pairs)]
    esm_map = esm2_client.score_candidates(esm_rows, ensemble=True, batch_size=200)
    print(f"  ESM-2 scored {len(esm_map)}/{len(unique_pairs)} pairs in {time.perf_counter() - t1:.1f}s", flush=True)

    # 4. Evaluate per-paper and overall metrics
    print("\n[4/4] Computing benchmark metrics across all 10 published papers...", flush=True)
    results_summary: list[dict[str, Any]] = []
    pooled_y: list[int] = []
    pooled_scores: dict[str, list[float]] = {
        "calis": [],
        "iedb_binding": [],
        "esm2_lora": [],
        "epitoperank_composite": [],
    }

    for meta in all_papers_meta:
        pid = meta["id"]
        recs = all_records_by_paper[pid]
        y_true: list[int] = []
        s_calis: list[float] = []
        s_bind: list[float] = []
        s_esm2: list[float] = []
        s_comp: list[float] = []
        scored_rows: list[dict[str, Any]] = []

        for r in recs:
            pep, hla, label = r["peptide"], r["allele"], r["label"]
            calis_val = float(properties.immunogenicity_score(pep) or 0.0)
            pr = iedb_map.get((pep, hla))
            esm = esm_map.get((pep, hla), {})
            esm_imm = esm.get("final_score")
            if esm_imm is None:
                esm_imm = esm.get("immunogenicity_score")
            if esm_imm is None:
                esm_imm = esm.get("v4_score")

            row_for_scoring = {
                "peptide": pep,
                "allele": hla,
                "percentile_rank": pr,
                "esm2_immunogenicity": esm_imm,
            }
            comp_out = scoring.composite(row_for_scoring)
            bind_val = comp_out["components"].get("binding")
            comp_val = float(comp_out["composite_score"])

            y_true.append(label)
            s_calis.append(calis_val)
            s_bind.append(bind_val)
            s_esm2.append(float(esm_imm) if esm_imm is not None else None)
            s_comp.append(comp_val)

            scored_rows.append({
                "peptide": pep,
                "allele": hla,
                "label": label,
                "iedb_percentile_rank": pr,
                "binding_score": bind_val,
                "calis_score": calis_val,
                "esm2_immunogenicity": esm_imm,
                "epitoperank_composite": comp_val,
            })

        # Save per-paper predictions
        pred_path = OUT_DIR / f"{pid}_PMID{meta['pmid']}_predictions.tsv"
        with pred_path.open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(scored_rows[0].keys()), delimiter="\t")
            w.writeheader()
            w.writerows(scored_rows)

        pooled_y.extend(y_true)
        pooled_scores["calis"].extend(s_calis)
        pooled_scores["iedb_binding"].extend(s_bind)
        pooled_scores["esm2_lora"].extend(s_esm2)
        pooled_scores["epitoperank_composite"].extend(s_comp)

        m = {
            **meta,
            "pos_rate": round(meta["n_pos"] / meta["n_total"], 4) if meta["n_total"] else 0.0,
            "auroc_calis": auroc(y_true, s_calis),
            "auroc_iedb": auroc(y_true, s_bind),
            "auroc_esm2": auroc(y_true, s_esm2),
            "auroc_composite": auroc(y_true, s_comp),
            "auprc_calis": auprc(y_true, s_calis),
            "auprc_iedb": auprc(y_true, s_bind),
            "auprc_esm2": auprc(y_true, s_esm2),
            "auprc_composite": auprc(y_true, s_comp),
            "top10_prec_iedb": topk_precision(y_true, s_bind, 10),
            "top10_prec_esm2": topk_precision(y_true, s_esm2, 10),
            "top10_prec_composite": topk_precision(y_true, s_comp, 10),
        }
        results_summary.append(m)
        def _fmt(v: float | None) -> str:
            return f"{v:.3f}" if v is not None else "  N/A"
        print(
            f"  {pid} ({meta['short']:38s}) N={meta['n_total']:4d} (+{meta['n_pos']:2d}) | "
            f"AUROC: Calis={_fmt(m['auroc_calis'])}, IEDB={_fmt(m['auroc_iedb'])}, "
            f"ESM2={_fmt(m['auroc_esm2'])}, Composite={_fmt(m['auroc_composite'])}",
            flush=True,
        )

    def macro_avg(key: str) -> float:
        vals = [r[key] for r in results_summary if r[key] is not None]
        return float(np.mean(vals)) if vals else 0.0

    summary_payload = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "esm2_status": esm_st,
        "scoring_weights": scoring.DEFAULT_WEIGHTS,
        "total_papers": len(results_summary),
        "total_pairs": len(pooled_y),
        "total_positives": sum(pooled_y),
        "macro_average": {
            "auroc_calis": round(macro_avg("auroc_calis"), 4),
            "auroc_iedb": round(macro_avg("auroc_iedb"), 4),
            "auroc_esm2": round(macro_avg("auroc_esm2"), 4),
            "auroc_composite": round(macro_avg("auroc_composite"), 4),
            "auprc_calis": round(macro_avg("auprc_calis"), 4),
            "auprc_iedb": round(macro_avg("auprc_iedb"), 4),
            "auprc_esm2": round(macro_avg("auprc_esm2"), 4),
            "auprc_composite": round(macro_avg("auprc_composite"), 4),
            "top10_prec_iedb": round(macro_avg("top10_prec_iedb"), 4),
            "top10_prec_esm2": round(macro_avg("top10_prec_esm2"), 4),
            "top10_prec_composite": round(macro_avg("top10_prec_composite"), 4),
        },
        "pooled_overall": {
            "auroc_calis": round(auroc(pooled_y, pooled_scores["calis"]) or 0.0, 4),
            "auroc_iedb": round(auroc(pooled_y, pooled_scores["iedb_binding"]) or 0.0, 4),
            "auroc_esm2": round(auroc(pooled_y, pooled_scores["esm2_lora"]) or 0.0, 4),
            "auroc_composite": round(auroc(pooled_y, pooled_scores["epitoperank_composite"]) or 0.0, 4),
            "auprc_calis": round(auprc(pooled_y, pooled_scores["calis"]) or 0.0, 4),
            "auprc_iedb": round(auprc(pooled_y, pooled_scores["iedb_binding"]) or 0.0, 4),
            "auprc_esm2": round(auprc(pooled_y, pooled_scores["esm2_lora"]) or 0.0, 4),
            "auprc_composite": round(auprc(pooled_y, pooled_scores["epitoperank_composite"]) or 0.0, 4),
        },
        "papers": results_summary,
    }

    summary_path = OUT_DIR / "benchmark_10papers_summary.json"
    summary_path.write_text(json.dumps(summary_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\n=== MACRO-AVERAGE ACROSS 10 REAL PAPERS ===")
    print(json.dumps(summary_payload["macro_average"], indent=2))
    print("\n=== POOLED OVERALL ACROSS ALL 10 PAPERS ===")
    print(json.dumps(summary_payload["pooled_overall"], indent=2))
    print(f"\nSaved full summary to: {summary_path}")


if __name__ == "__main__":
    main()
