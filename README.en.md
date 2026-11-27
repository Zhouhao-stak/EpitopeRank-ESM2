# EpitopeRank-ESM2

[简体中文](README.md) · [繁體中文](README.zh-TW.md) · **English**

**AI-Driven Alternative Splicing & Neoantigen Immunogenicity Platform Powered by ESM-2-650M LoRA + BigMHC-IM Dual-Engine Fusion**

[![Tests](https://github.com/Zhouhao-stak/EpitopeRank-ESM2/actions/workflows/test.yml/badge.svg)](https://github.com/Zhouhao-stak/EpitopeRank-ESM2/actions/workflows/test.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Base Model: ESM-2-650M](https://img.shields.io/badge/ESM--2--650M-PEFT%20LoRA%205--Fold-green.svg)](https://huggingface.co/ZhouRitian/epitoperank-esm2-650m-lora-v4)
[![Dual Engine: ESM-2 + BigMHC-IM](https://img.shields.io/badge/Dual--Engine-ESM2%20%2B%20BigMHC--IM-orange.svg)](#5-sota-benchmarking-across-10-peer-reviewed-studies--zero-leakage-audit)
[![UI: 简体 / 繁體 / EN](https://img.shields.io/badge/UI-简体%20%7C%20繁體%20%7C%20EN-blueviolet.svg)](#8-quick-start--configuration)
[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](LICENSE)

> **Project Lineage**: This repository is the protein language model (PLM) and dual-engine immunogenicity upgrade of **[Zhouhao-stak/EpitopeRank](https://github.com/Zhouhao-stak/EpitopeRank)** (`SpliceGAIP_ESM2`).
> Retaining the full rMATS splicing analytics, automated ORF reconstruction, autonomous agent reporting, and deterministic replay architecture, it introduces **ESM-2-650M LoRA 2-stage 5-fold ensembling**, **v5-beta Mut–WT biophysical Siamese residual head**, **TESLA multi-omics clinical fusion**, **ESM-2 + BigMHC-IM cooperative scoring**, and **instant tri-lingual Web UI switching (Simplified Chinese / Traditional Chinese / English)**.

---

## Table of Contents

- [Key Highlights](#1-key-highlights)
- [Architecture & Model Design](#2-architecture--model-design)
- [Dataset Curation & 2-Stage 5-Fold Fine-Tuning](#3-dataset-curation--2-stage-5-fold-fine-tuning)
- [v5-beta Siamese Residual Head & TESLA Multi-Omics Fusion](#4-v5-beta-siamese-residual-head--tesla-multi-omics-fusion)
- [SOTA Benchmarking Across 10 Peer-Reviewed Studies & Zero-Leakage Audit](#5-sota-benchmarking-across-10-peer-reviewed-studies--zero-leakage-audit)
- [Broad Validation Across 20 Peer-Reviewed Cohorts](#6-broad-validation-across-20-peer-reviewed-cohorts-n3260)
- [Interactive Reports & Reproducible Artifacts](#7-interactive-reports--reproducible-artifacts)
- [Quick Start & Configuration](#8-quick-start--configuration)
- [Acknowledgements](#9-acknowledgements)

---

## 1. Key Highlights

1. **Closing the "MHC Binding ≠ T-Cell Immunogenicity" Gap**
   Conventional predictors (e.g., NetMHCpan, MHCflurry) estimate pMHC presentation, yet clinical wet-lab benchmarks (TESLA, *Cell* 2020) show only ~6% of strong binders elicit CD8+ T-cell responses. We fine-tune Meta AI's `facebook/esm2_t33_650M_UR50D` (650M parameters) with PEFT LoRA to jointly model **peptide + 34-aa HLA-I binding-groove pseudosequences** and output residue-level TCR attention hotspots.
2. **Strong Generalization on Splicing-Derived Neoantigens**
   Across 3 recent splicing neoantigen studies (*Cell* 2025, *Genome Res* 2026, *PNAS* 2023 IRIS), standalone IEDB NetMHCpan-4.1 achieves a macro-average AUROC of `0.5848`, whereas **ESM-2-650M LoRA reaches `0.7007` (+0.1159)**.
3. **Orthogonal Dual-Engine Cooperation with Strict Zero-Leakage Verification**
   Fine-tuned ESM-2 and `BigMHC-IM` (*Nature Machine Intelligence* 2023) are strongly orthogonal (zero-leakage Spearman $\rho = 0.2489$, Top-20% Jaccard overlap `0.2079`). Cooperative scoring (`0.55×ESM-2 + 0.45×BigMHC-IM`) raises 10-study macro AUROC to **`0.7355`**, Pooled AUROC to **`0.8070`**, and Pooled AUPRC by **+24.6%**. After removing all 927 samples overlapping BigMHC-IM's official training/validation sets (`N = 1,209`), Top-50 PPV jumps from 32%/34% (single models) to **50%–52%**.
4. **Tri-Lingual UI & Production CPU INT8 Inference**
   The Web UI supports instant switching between **Simplified Chinese (`简体`)**, **Traditional Chinese (`繁體`, offline OpenCC bundle)**, and **English (`EN`)**. Remote inference runs with merged LoRA weights + dynamic INT8 quantization and gracefully degrades offline.

---

## 2. Architecture & Model Design

```text
rMATS JC Splicing Tables + Sample Metadata / Clinical Peptide Tables
   │
   ├─► 1. Automated ORF Reconstruction & Junction Peptide Generation (orf_builder.py)
   ├─► 2. IEDB NetMHCpan-4.1 EL Binding & Processing Prediction
   ├─► 3. Human Proteome Self-Similarity Filtering (novelty / self_hit)
   ├─► 4. [NEW] ESM-2-650M LoRA + BigMHC-IM Dual-Engine Immunogenicity Microservice
   │       ├─ Joint Encoding: <cls> peptide(8–14 aa) <eos> 34-aa HLA-I pseudosequence <eos>
   │       ├─ AttentionPoolHead: peptide-masked attention pooling + per-residue TCR hotspots
   │       ├─ v5-beta Siamese Residual Head: Mut–WT hydrophobicity/charge/TCR-zone calibration
   │       └─ TESLA Clinical Fusion: affinity + stability + RNA TPM + clonal fraction (CCF)
   ▼
   5. 6-Dimensional Transparent Ranking & Tier A/B/C/D / Clinical Tier-1/2/3 Stratification
   ▼
   6. Tri-Lingual Web UI (简体 / 繁體 / EN) · Desktop App · HTML/PDF Publication Reports
```

### Model Specifications

| Component | Specification |
|---|---|
| **Backbone** | `facebook/esm2_t33_650M_UR50D` (33-layer Transformer, `hidden_size = 1280`) |
| **PEFT LoRA** | `r=16, lora_alpha=32, lora_dropout=0.08`, applied to `["query", "key", "value", "dense"]` |
| **Joint Input** | `<cls> peptide(8–14 aa) <eos> HLA_34aa_pseudosequence <eos>` (18 high-frequency human HLA-I alleles) |
| **Interpretable Head** | Peptide-focused `AttentionPoolHead` (masked softmax over peptide tokens for per-residue TCR attribution) |
| **Training Strategy** | Two-stage decoupled fine-tuning (Stage 1 mixed negatives for pMHC/HLA specificity; Stage 2 experimental-only low-LR refinement) + validation Temperature Scaling |
| **Model Weights** | Hugging Face Hub: [`ZhouRitian/epitoperank-esm2-650m-lora-v4`](https://huggingface.co/ZhouRitian/epitoperank-esm2-650m-lora-v4) (5-fold adapters, 244 MB) |

---

## 3. Dataset Curation & 2-Stage 5-Fold Fine-Tuning

Reference scripts are provided in [`training/`](training/):
- [`training/01_build_v4_dataset.py`](training/01_build_v4_dataset.py) · [`training/02_train_v4_twostage.py`](training/02_train_v4_twostage.py) · [`training/03_eval_v4_ensemble.py`](training/03_eval_v4_ensemble.py)

- **Positives**: Experimental HLA-I T-cell positives from **IEDB** and **CEDAR** across 18 alleles (7 HLA-A, 11 HLA-B; capped at 800 per allele, reserving `offset >= 5000` as an independent holdout benchmark).
- **4 Hard Negative Categories (`1 : 1.25` ratio)**: `50%` experimental HLA-matched negatives, `25%` reviewed human UniProt background peptides, `13%` cross-allele HLA-mismatch negatives, and `12%` shuffled/low-complexity decoys.
- **Leakage Prevention**: Peptide **3-mer homology clustering** + **`StratifiedGroupKFold(n_splits=5)`**.

### 5-Fold Cross-Validation Results (v4)

| Fold | Experimental Hard AUROC | Experimental Hard AUPRC | F1 | Optimal $T$ | ECE |
|---|---:|---:|---:|---:|---:|
| **Fold 0** | 0.7141 | 0.7782 | 0.7181 | 2.20 | 0.0771 |
| **Fold 1** | 0.7119 | 0.7813 | 0.7325 | 2.20 | 0.0820 |
| **Fold 2** | 0.7613 | 0.8300 | 0.7382 | 1.55 | 0.1144 |
| **Fold 3** | 0.7248 | 0.7876 | 0.7340 | 2.05 | 0.0853 |
| **Fold 4** | 0.7391 | 0.8036 | 0.7281 | 2.45 | 0.0886 |
| **5-Fold Mean ± SD** | **0.7302 ± 0.0183** | **0.7961** | **0.7302** | — | — |

**Independent Holdout Ensemble (`offset >= 5000`)**:
- Hard Benchmark (30 pos / 60 neg): **AUROC = `0.7817`** | **AUPRC = `0.6056`** | **Recall = `90.0%` (27/30)**
- **HLA Mismatch Specificity Gap** (matched HLA − mismatched HLA): **`+0.2765`** | Low-complexity decoy mean: `0.2522`

---

## 4. v5-beta Siamese Residual Head & TESLA Multi-Omics Fusion

Implemented in [`training/clinical_fusion.py`](training/clinical_fusion.py):

1. **v5-beta Mut–WT Biophysical Residual Head**: Frozen v4 backbone + lightweight `<0.01 ms` biophysical calibration fitted via 5-fold author-grouped OOF on **ITSNdb (176 Mut–WT pairs)** — raising OOF AUROC from `0.6919` to **`0.7066`** with zero catastrophic forgetting.
2. **TESLA Clinical Multi-Omics Fusion** (Wells et al., *Cell* 2020; 6 melanoma/NSCLC patients, `N = 511`): Strict leave-one-patient-out CV (LOPO-CV) lifts AUROC from `0.7097` (sequence-only, Top-20 recall `48.5%`) to **`0.8251`** and patient-level **Top-20 recall to `72.7%` (24/33)** (vs DeepHLApan `0.4544` / `18.2%`).

---

## 5. SOTA Benchmarking Across 10 Peer-Reviewed Studies & Zero-Leakage Audit

All raw datasets and per-peptide predictions are open-sourced in [`benchmarks/datasets/`](benchmarks/datasets/) and [`benchmarks/results/`](benchmarks/results/).

### 5.1 Full 10-Study SOTA Comparison (`N = 2,136`, including 3 Splicing Neoantigen Studies)

| Model / Strategy | 10-Study Macro AUROC | 3-Study Splicing AUROC | 3-Study Splicing AUPRC | Pooled AUROC | Pooled AUPRC | Macro Top-10 PPV |
|---|---:|---:|---:|---:|---:|---:|
| Calis Physicochemical Baseline | 0.5636 | 0.5538 | 0.2889 | 0.5223 | 0.1300 | 35.0% |
| MixMHCpred 3.0 | 0.6209 | 0.5478 | 0.2577 | 0.7183 | 0.2461 | 36.0% |
| IEDB NetMHCpan-4.1 EL | 0.6328 | 0.5848 | 0.2664 | 0.7383 | 0.2559 | 51.0% |
| BigMHC-EL (7-fold) | 0.6364 | 0.6493 | 0.2857 | 0.7051 | 0.2149 | 37.0% |
| PRIME 2.1 (*Cell Systems* 2023) | 0.6630 | 0.6122 | 0.3422 | 0.7269 | 0.2571 | 45.0% |
| BigMHC-IM (*NMI* 2023, 7-fold) | 0.6921 | 0.5677 | 0.3459 | 0.7651 | 0.2992 | 49.0% |
| **ESM-2-650M LoRA (5-fold solo)** | 0.6618 | **0.7007** | 0.3724 | 0.6947 | 0.2034 | 34.0% |
| EpitopeRank Splicing-Opt (IEDB+ESM-2) | 0.6904 | 0.6908 | 0.3730 | 0.7688 | 0.2841 | 41.0% |
| **Dual-Engine Cooperative (`0.55×ESM-2 + 0.45×BigMHC-IM`)** | **0.7355** | 0.6655 | **0.4011** | 0.7855 | 0.3473 | **53.0%** |
| **EpitopeRank Cooperative Splicing-Opt** | **0.7170** | 0.6652 | **0.3895** | **0.8070** | **0.3539** | **53.0%** |

### 5.2 Strict Zero-Leakage Audit (`N = 1,209` after removing 927 BigMHC-IM train/val overlaps)

| Zero-Leakage Strategy (`N = 1,209`) | 9-Study Macro AUROC | 3-Study Splicing AUROC | 3-Study Splicing AUPRC | Pooled AUROC | Pooled AUPRC | **Pooled Top-50 PPV** |
|---|---:|---:|---:|---:|---:|---:|
| ESM-2-650M LoRA solo | 0.6667 | **0.7007** | 0.3724 | 0.6696 | 0.2671 | **32.0% (16/50)** |
| BigMHC-IM solo | 0.6972 | 0.5677 | 0.3459 | 0.6863 | 0.2949 | **34.0% (17/50)** |
| **Dual-Engine (50/50 Prob Fusion)** | 0.7323 | 0.6505 | 0.3915 | 0.7161 | 0.3455 | **52.0% (26/50)** |
| **Dual-Engine (50/50 Rank Fusion)** | **0.7384** | 0.6702 | **0.4233** | 0.7229 | 0.3588 | **50.0% (25/50)** |
| **Tri-Engine (IEDB+ESM-2+BigMHC-IM)** | 0.7348 | 0.6536 | 0.3814 | **0.7457** | **0.3710** | **50.0% (25/50)** |

---

## 6. Broad Validation Across 20 Peer-Reviewed Cohorts (`N=3,260`)

Full summary in [`benchmarks/results/bench20_summary.json`](benchmarks/results/bench20_summary.json):
- **10 Binary Classification Cohorts (`N=2,595`)**: Sample-weighted AUROC **`0.7257`**.
- **8 Clinical Vaccine & Viral Positive Cohorts (`N=592`)**: Mean Recall@0.5 **`91.1%`** (Zhang SQ *Nat Biotech* `97.3%`, Ott NeoVax `90.9%`, Sahin BioNTech `85.7%`, Dengue *PNAS* `92.0%`, SARS-CoV-2 *BiB* 2021 `82.9%` vs DeepImmuno `30.5%`).

---

## 7. Interactive Reports & Reproducible Artifacts

| File | Description |
|---|---|
| [`benchmarks/BENCHMARK_REPORT.md`](benchmarks/BENCHMARK_REPORT.md) | 10-study benchmark report (Markdown) |
| [`benchmarks/EpitopeRank_ESM2_Benchmark_Report.html`](benchmarks/EpitopeRank_ESM2_Benchmark_Report.html) | Interactive 10-study SOTA + dual-engine + zero-leakage HTML report |
| [`docs/reports/ESM2_LoRA_20篇权威论文基准检验报告.html`](docs/reports/ESM2_LoRA_20篇权威论文基准检验报告.html) | Interactive 20-study (`N=3,260`) benchmark HTML report |
| [`docs/reports/ESM2_LoRA_四代迭代实验报告.html`](docs/reports/ESM2_LoRA_四代迭代实验报告.html) | v1–v4 ablation and iterative engineering HTML report |
| [`docs/reports/ESM2_LoRA_v4_六大真实论文基准评测报告.html`](docs/reports/ESM2_LoRA_v4_六大真实论文基准评测报告.html) | v4 6-cohort detailed validation HTML report |
| [`docs/ESM2_MODEL_WHITEPAPER.md`](docs/ESM2_MODEL_WHITEPAPER.md) | Model architecture whitepaper & integration specification |

---

## 8. Quick Start & Configuration

```bash
python -m venv venv
venv\Scripts\activate            # Windows
# source venv/bin/activate       # macOS / Linux

pip install -r requirements.txt
python serve_ui.py --port 8800
# Open http://127.0.0.1:8800/ — switch seamlessly between 简体 / 繁體 / EN in the top bar
```

Copy `.env.example` to `.env` to enable remote ESM-2 dual-engine scoring (automatically falls back to 5-dimensional scoring when offline):

```ini
EPITOPERANK_ESM2_URL=https://esm2.immich.pw
EPITOPERANK_ESM2_API_KEY=<your-api-key>
EPITOPERANK_ESM2_ENSEMBLE=true
EPITOPERANK_ESM2_TIMEOUT=45
```

---

## 9. Acknowledgements

- Base Platform: [Zhouhao-stak/EpitopeRank](https://github.com/Zhouhao-stak/EpitopeRank)
- Protein Language Model: [Meta AI ESM-2 (`esm2_t33_650M_UR50D`)](https://github.com/facebookresearch/esm)
- Cooperative Immunogenicity Model: [BigMHC (*Nature Machine Intelligence*, 2023)](https://github.com/KarchinLab/bigmhc)
- Clinical & Experimental Benchmarks: TESLA Consortium (*Cell*, 2020) · ITSNdb · IEDB & CEDAR
