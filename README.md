<p align="center">
  <img src="docs/assets/logo.png" alt="EpitopeRank-ESM2 Logo" width="128" height="128" />
</p>

# EpitopeRank-ESM2

**简体中文** · [繁體中文](README.zh-TW.md) · [English](README.en.md)

**基于 ESM-2-650M LoRA 与 BigMHC-IM 双引擎异构融合的可变剪接新抗原免疫原性预测平台**

[![Tests](https://github.com/Zhouhao-stak/EpitopeRank-ESM2/actions/workflows/test.yml/badge.svg)](https://github.com/Zhouhao-stak/EpitopeRank-ESM2/actions/workflows/test.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Base Model: ESM-2-650M](https://img.shields.io/badge/ESM--2--650M-PEFT%20LoRA%205--Fold-green.svg)](https://huggingface.co/ZhouRitian/epitoperank-esm2-650m-lora-v4)
[![Dual Engine: ESM-2 + BigMHC-IM](https://img.shields.io/badge/Dual--Engine-ESM2%20%2B%20BigMHC--IM-orange.svg)](#五10-篇真实顶刊-sota-同台对比与严格零泄露审计)
[![UI: 简体 / 繁體 / EN](https://img.shields.io/badge/UI-简体%20%7C%20繁體%20%7C%20EN-blueviolet.svg)](#八快速开始与接入配置)
[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](LICENSE)

> **项目演进说明**：本仓库是原项目 **[Zhouhao-stak/EpitopeRank](https://github.com/Zhouhao-stak/EpitopeRank)** 的大模型与多引擎免疫原性升级版（`SpliceGAIP_ESM2`）。
> 在完整保留 rMATS 可变剪接统计分析、ORF 自动重建、多智能体报告与可复现轨迹回放的基础上，新增 **ESM-2-650M LoRA 两阶段 5 折集成**、**v5-beta Mut–WT 生物物理孪生残差头**、**TESLA 多组学临床融合引擎** 以及 **ESM-2 + BigMHC-IM 双引擎合作打分**。

---

## 目录

- [核心升级亮点](#一核心升级亮点)
- [系统架构与模型设计](#二系统架构与模型设计)
- [训练数据集构建与两阶段 5 折微调指标](#三训练数据集构建与两阶段-5-折微调指标)
- [v5-beta 孪生残差头与 TESLA 多组学临床融合](#四v5-beta-孪生残差头与-tesla-多组学临床融合)
- [10 篇真实顶刊 SOTA 同台对比与严格零泄露审计](#五10-篇真实顶刊-sota-同台对比与严格零泄露审计)
- [20 篇权威文献广度基准验证](#六20-篇权威文献广度基准验证n3260)
- [完整交互式报告与可复现资产](#七完整交互式报告与可复现资产)
- [快速开始与接入配置](#八快速开始与接入配置)
- [致谢与引用](#九致谢与引用)

---

## 一、核心升级亮点

1. **填补「能结合 MHC ≠ 能激活 T 细胞」的免疫原性空白**
   传统工具（如 NetMHCpan、MHCflurry）主要预测 pMHC 结合亲和力，而临床湿实验表明强结合肽段中仅约 6% 能真正诱发 CD8+ T 细胞应答。本项目基于 Meta AI `facebook/esm2_t33_650M_UR50D`（6.5 亿参数）进行参数高效微调（PEFT LoRA），直接建模 **肽段–HLA 结合槽** 的免疫原性激活概率与逐残基 TCR 接触热点。
2. **在可变剪接新抗原领域显著领先传统模型**
   在 3 篇 2023–2026 年剪接新抗原顶刊队列（*Cell* 2025、*Genome Res* 2026、*PNAS* 2023 IRIS）上，单靠 MHC 结合预测（IEDB NetMHCpan-4.1）宏平均 AUROC 仅 `0.5848`，而 **ESM-2-650M LoRA 单模型达到 `0.7007`（+0.1159）**。
3. **发现异构正交互补，构建双引擎合作打分**
   实测显示微调后的 ESM-2 与领域专用模型 `BigMHC-IM`（*Nature Machine Intelligence* 2023）呈高度正交互补（零泄露 Spearman $\rho = 0.2489$，Top-20% Jaccard 重叠度仅 `0.2079`）。双引擎合作打分在 10 篇顶刊（`N=2,136`）上将宏平均 AUROC 推高至 **`0.7355`**，全样本 Pooled AUROC 达 **`0.8070`**，Pooled AUPRC 提升 **+24.6%**；严格剔除 927 条 BigMHC-IM 训练集重叠样本后，零泄露 Top-50 阳性命中率从单模型的 32%/34% 跃升至 **50%–52%**。
4. **生产级 CPU INT8 量化与解耦微服务**
   桌面端可通过轻量 HTTP 客户端接入部署于 128 核服务器的 INT8 量化推理微服务（支持 `merge_and_unload()` 合并 LoRA 与 BigMHC-IM 4× 逐行 INT8 压缩），无需本地 GPU，离线时自动优雅降级。

---

## 二、系统架构与模型设计

```text
rMATS JC 五类剪接事件 + 样本元数据 / 临床肽段表
   │
   ├─► 1. ORF 自动重建 & 剪接连接肽生成 (epitoperank/splicing/orf_builder.py)
   ├─► 2. IEDB NetMHCpan-4.1 EL 结合与加工预测 (binding, processing)
   ├─► 3. 人类正常蛋白组去重比对 (novelty / self_hit)
   ├─► 4. 【新增】ESM-2-650M LoRA + BigMHC-IM 双引擎免疫原性服务
   │       ├─ 联合编码: <cls> 肽段(8–14 aa) <eos> 34-aa HLA-I 结合槽伪序列 <eos>
   │       ├─ AttentionPoolHead: 肽段聚焦注意力池化 + 逐残基 TCR 热点热力图
   │       ├─ v5-beta 孪生残差头: Mut–WT 疏水性/电荷/TCR 接触区生物物理校准
   │       └─ TESLA 多组学临床融合: 结合亲和力 + 稳定性 + RNA TPM + 克隆丰度 CCF
   ▼
   5. 6 维透明加权综合排序 & Tier A/B/C/D / Clinical Tier-1/2/3 分级
   ▼
   6. Web UI / 桌面客户端 / HTML & PDF 论文级分析报告
```

### 核心模型规格

| 组件 | 规格说明 |
|---|---|
| **预训练底座** | `facebook/esm2_t33_650M_UR50D`（33 层 Transformer，hidden_size = `1280`） |
| **PEFT LoRA** | `r=16, lora_alpha=32, lora_dropout=0.08`，作用于全层 `["query", "key", "value", "dense"]` |
| **联合输入格式** | `<cls> peptide(8–14 aa) <eos> HLA_34aa_pseudosequence <eos>`（覆盖 18 个高频人类 HLA-I 等位基因） |
| **可解释分类头** | 肽段聚焦 `AttentionPoolHead`（仅在肽段位置计算 Masked Softmax 池化，输出逐残基 TCR 权重） |
| **训练策略** | 两阶段解耦训练（Stage 1 混合分布预热 pMHC 与 HLA 特异性；Stage 2 纯实测数据低学习率精调）+ Temperature Scaling 温度校准 |
| **权重托管** | Hugging Face Model Hub：[`ZhouRitian/epitoperank-esm2-650m-lora-v4`](https://huggingface.co/ZhouRitian/epitoperank-esm2-650m-lora-v4)（5 折权重，244 MB） |

---

## 三、训练数据集构建与两阶段 5 折微调指标

训练与评估参考脚本已收录于 [`training/`](training/)：
- [`training/01_build_v4_dataset.py`](training/01_build_v4_dataset.py)：数据集构建与防泄漏切分
- [`training/02_train_v4_twostage.py`](training/02_train_v4_twostage.py)：两阶段 LoRA 训练与温度校准
- [`training/03_eval_v4_ensemble.py`](training/03_eval_v4_ensemble.py)：5 折集成独立留出集评测

### 3.1 数据工程与防泄漏策略
- **正样本来源**：整合 **IEDB**（`tcell_search`）与 **CEDAR** 癌症表位专库，覆盖 18 个高频人类 HLA-I 等位基因（7 个 HLA-A + 11 个 HLA-B），每等位基因上限 `800` 条实测阳性（`max_offset=4500`，严格留出 `offset >= 5000` 作为独立盲测留出集）。
- **4 类困难负样本（正负比 `1 : 1.25`）**：
  1. `50%` 实测困难阴性（IEDB + CEDAR 同一 HLA 批内实测 `Negative`）
  2. `25%` 人类正常蛋白组采样（UniProt 已审校人类蛋白按相同长度与 HLA 分布切取）
  3. `13%` 跨等位基因 HLA 错配负样本（将真实阳性肽段配给结合槽冲突的错误 HLA，强迫模型建模 HLA 伪序列）
  4. `12%` 乱序对照与低复杂度陷阱（防止同聚体高分误报）
- **防同源泄露切分**：按肽段 **3-mer 同源聚类** 分配 `cluster_id`，再使用 **`StratifiedGroupKFold(n_splits=5)`** 切分，确保同源点突变肽段不跨折泄露。

### 3.2 5 折交叉验证逐折实测表现（v4）

| 折号 | 纯实验验证 Hard AUROC | 纯实验验证 Hard AUPRC | F1 | 最优温度 $T$ | 校准误差 ECE |
|---|---:|---:|---:|---:|---:|
| **Fold 0** | 0.7141 | 0.7782 | 0.7181 | 2.20 | 0.0771 |
| **Fold 1** | 0.7119 | 0.7813 | 0.7325 | 2.20 | 0.0820 |
| **Fold 2** | 0.7613 | 0.8300 | 0.7382 | 1.55 | 0.1144 |
| **Fold 3** | 0.7248 | 0.7876 | 0.7340 | 2.05 | 0.0853 |
| **Fold 4** | 0.7391 | 0.8036 | 0.7281 | 2.45 | 0.0886 |
| **5 折均值 ± 标准差** | **0.7302 ± 0.0183** | **0.7961** | **0.7302** | — | — |

**独立留出集（5 折集成，`offset >= 5000`）**：
- Hard Benchmark（30 阳 / 60 阴）：**AUROC = `0.7817`** ｜ **AUPRC = `0.6056`** ｜ **Recall = `90.0%`（27/30）**
- 经典肿瘤表位均分：**`0.7031`**（KRAS G12D `0.8074`、HER2 `0.7399`、MAGE-A3 `0.7382`、MART-1 `0.7124`）
- **HLA 错配特异性差值**（正确 HLA − 错配 HLA）：**`+0.2765`** ｜ 低复杂度陷阱均分：`0.2522`

---

## 四、v5-beta 孪生残差头与 TESLA 多组学临床融合

实现脚本见 [`training/clinical_fusion.py`](training/clinical_fusion.py)：

1. **v5-beta Mut–WT 生物物理孪生残差头**：
   在 **ITSNdb 176 对** 临床突变/野生型（Mut–WT）配对数据集上按严格 5 折作者分组（OOF）拟合，冻结 v4 底座参数（`<0.01 ms` 推理，无 WT 时 100% 零遗忘退回 v4 分数）：
   $$\text{logit}_{\text{v5b}} = \text{logit}(\text{v4}) + 0.095 \cdot \frac{\Delta\text{KD}}{3.0} + 0.141 \cdot (\Delta\text{Chg} - 0.35) + 0.077 \cdot (\text{is\_tcr} - 0.5)$$
   - ITSNdb 5 折 OOF AUROC 从 `0.6919` 提升至 **`0.7066`**。
2. **TESLA 多组学临床融合引擎**（Wells et al., *Cell* 2020，6 名黑色素瘤/NSCLC 患者，`N=511`，阳性率 6.46%）：
   基于严格 **留一患者交叉验证（LOPO-CV）** 标定，融合序列免疫原性（`+0.976`）、MHC 结合亲和力（`+1.048`）、pMHC 稳定性（`+0.257`）、肿瘤 RNA 表达量（`+0.716`）与克隆丰度 CCF（`+0.25`）：
   - 单纯 ESM-2 v4 序列 AUROC：**`0.7097`**，Top-20 命中率 **`48.5%`**（vs DeepHLApan `0.4544` / `18.2%`）；
   - 接入 TESLA 多组学临床融合后，LOPO-CV AUROC 跃升至 **`0.8251`**，按患者 **Top-20 命中率达 `72.7%`（24/33）**。

---

## 五、10 篇真实顶刊 SOTA 同台对比与严格零泄露审计

所有数据集均直接从 IEDB Query API 按真实 PubMed ID 拉取（零合成数据），原始数据与逐条预测表均完整开源于 [`benchmarks/datasets/`](benchmarks/datasets/) 与 [`benchmarks/results/`](benchmarks/results/)。

### 5.1 10 篇真实发表论文全量 SOTA 同台对比（`N = 2,136`，含 3 篇剪接新抗原顶刊）

> 包含 P01 *Cell* (2025, PMID: `40273911`)、P02 *Genome Res* (2026, PMID: `42680560`)、P03 *PNAS* (2023 IRIS, PMID: `37192158`)、P04 *Nat Med* (2025)、P05 *Nat Med* (2021)、P06 *Science* (2016)、P07 *Science* (2015)、P08 *Gastroenterology* (2024)、P09 *JITC* (2023)、P10 *Front Immunol* (2024)。

| 模型 / 融合策略 | 10 篇宏平均 AUROC | 3 篇剪接 AUROC | 3 篇剪接 AUPRC | 全样本 Pooled AUROC | 全样本 Pooled AUPRC | 宏平均 Top-10 PPV |
|---|---:|---:|---:|---:|---:|---:|
| Calis 理化基线 | 0.5636 | 0.5538 | 0.2889 | 0.5223 | 0.1300 | 35.0% |
| MixMHCpred 3.0 | 0.6209 | 0.5478 | 0.2577 | 0.7183 | 0.2461 | 36.0% |
| IEDB NetMHCpan-4.1 EL | 0.6328 | 0.5848 | 0.2664 | 0.7383 | 0.2559 | 51.0% |
| BigMHC-EL (7 折) | 0.6364 | 0.6493 | 0.2857 | 0.7051 | 0.2149 | 37.0% |
| PRIME 2.1 (*Cell Systems* 2023) | 0.6630 | 0.6122 | 0.3422 | 0.7269 | 0.2571 | 45.0% |
| BigMHC-IM (*NMI* 2023, 7 折) | 0.6921 | 0.5677 | 0.3459 | 0.7651 | 0.2992 | 49.0% |
| **ESM-2-650M LoRA (5 折单模型)** | 0.6618 | **0.7007** | 0.3724 | 0.6947 | 0.2034 | 34.0% |
| EpitopeRank 剪接优化版 (IEDB+ESM-2) | 0.6904 | 0.6908 | 0.3730 | 0.7688 | 0.2841 | 41.0% |
| **新·双引擎合作 (`0.55×ESM-2 + 0.45×BigMHC-IM`)** | **0.7355** | 0.6655 | **0.4011** | 0.7855 | 0.3473 | **53.0%** |
| **新·EpitopeRank 合作剪接版** | **0.7170** | 0.6652 | **0.3895** | **0.8070** | **0.3539** | **53.0%** |

### 5.2 严格零泄露去重验证（Zero-Leakage Audit）

从 BigMHC 官方 Mendeley 数据仓（`doi:10.17632/dvmz6pkzvb`）提取全部 `im_train.csv`（6,185 条）与 `im_val.csv`（688 条）进行严格样本级去重后，发现早期队列 P05–P07 存在大量重叠，而 2023–2026 年 6 篇新论文重叠为 `0`。剔除全部 **927 条** 重叠样本后（净剩 **`N = 1,209`，阳 222 / 阴 987**）：

| 零泄露评测策略（`N = 1,209`） | 9 篇宏平均 AUROC | 3 篇剪接 AUROC | 3 篇剪接 AUPRC | Pooled AUROC | Pooled AUPRC | **Pooled Top-50 PPV** |
|---|---:|---:|---:|---:|---:|---:|
| 单独 ESM-2-650M LoRA | 0.6667 | **0.7007** | 0.3724 | 0.6696 | 0.2671 | **32.0% (16/50)** |
| 单独 BigMHC-IM | 0.6972 | 0.5677 | 0.3459 | 0.6863 | 0.2949 | **34.0% (17/50)** |
| **双引擎合作（50/50 概率融合）** | 0.7323 | 0.6505 | 0.3915 | 0.7161 | 0.3455 | **52.0% (26/50)** |
| **双引擎合作（50/50 秩融合）** | **0.7384** | 0.6702 | **0.4233** | 0.7229 | 0.3588 | **50.0% (25/50)** |
| **三引擎协同（IEDB+ESM-2+BigMHC-IM）** | 0.7348 | 0.6536 | 0.3814 | **0.7457** | **0.3710** | **50.0% (25/50)** |

---

## 六、20 篇权威文献广度基准验证（`N=3,260`）

除上述 10 篇同台 SOTA 对比外，我们还在 20 篇真实文献队列（共 `3,260` 条湿实验记录，汇总结果见 [`benchmarks/results/bench20_summary.json`](benchmarks/results/bench20_summary.json)）上进行了盲测：
- **10 篇二分类基准队列（`N=2,595`）**：样本加权 AUROC **`0.7257`**（Strønen *Science* 2016 `0.8122`、Fehlings *JITC* 2019 `0.6066` 超越 NetMHCpan `0.5672`）。
- **8 篇临床疫苗与病毒真阳性队列（`N=592`）**：平均 Recall@0.5 达 **`91.1%`**（Zhang SQ *Nat Biotech* `97.3%`、Ott NeoVax `90.9%`、Sahin BioNTech `85.7%`、登革热 *PNAS* `92.0%`、新冠康复者 *BiB* 2021 `82.9%` vs DeepImmuno `30.5%`）。

---

## 七、完整交互式报告与可复现资产

| 资产文件 | 内容说明 |
|---|---|
| [`benchmarks/BENCHMARK_REPORT.md`](benchmarks/BENCHMARK_REPORT.md) | 10 篇真实顶刊基准评测 Markdown 报告 |
| [`benchmarks/EpitopeRank_ESM2_Benchmark_Report.html`](benchmarks/EpitopeRank_ESM2_Benchmark_Report.html) | 10 篇顶刊 + 双引擎合作 + 零泄露审计交互式 HTML 报告 |
| [`docs/reports/ESM2_LoRA_20篇权威论文基准检验报告.html`](docs/reports/ESM2_LoRA_20篇权威论文基准检验报告.html) | 20 篇权威文献（`N=3,260`）盲测完整交互式 HTML 报告 |
| [`docs/reports/ESM2_LoRA_四代迭代实验报告.html`](docs/reports/ESM2_LoRA_四代迭代实验报告.html) | v1 → v4 四代迭代消融实验与超参数演进报告 |
| [`docs/reports/ESM2_LoRA_v4_六大真实论文基准评测报告.html`](docs/reports/ESM2_LoRA_v4_六大真实论文基准评测报告.html) | v4 六大经典队列基准详细评测报告 |
| [`docs/ESM2_MODEL_WHITEPAPER.md`](docs/ESM2_MODEL_WHITEPAPER.md) | ESM-2-650M LoRA（v4 + v5-beta）技术白皮书与工程接入方案 |
| [`benchmarks/results/benchmark_10papers_summary.json`](benchmarks/results/benchmark_10papers_summary.json) | 10 篇顶刊全量评测原始汇总 JSON |
| [`benchmarks/results/bench20_summary.json`](benchmarks/results/bench20_summary.json) | 20 篇文献广度基准原始汇总 JSON |

---

## 八、快速开始与接入配置

### 8.1 从源码运行

```bash
# 1. 创建虚拟环境（Python >= 3.10）
python -m venv venv
venv\Scripts\activate            # Windows
# source venv/bin/activate       # macOS / Linux

pip install -r requirements.txt

# 2. 启动 Web 服务与界面
python serve_ui.py --port 8800
# 浏览器访问 http://127.0.0.1:8800/
```

### 8.2 接入 ESM-2 双引擎免疫原性服务

复制 `.env.example` 为 `.env`，配置以下可选参数（未配置或服务离线时自动退化为 5 维基础打分，不影响主流程）：

```ini
EPITOPERANK_ESM2_URL=https://esm2.immich.pw
EPITOPERANK_ESM2_API_KEY=<your-api-key>
EPITOPERANK_ESM2_ENSEMBLE=true
EPITOPERANK_ESM2_TIMEOUT=45
```

### 8.3 复现 10 篇顶刊 Benchmark

```bash
# 基于 benchmarks/datasets/ 与缓存预测结果重跑 10 篇论文评测与 HTML 报告生成
python benchmarks/run_10paper_benchmark.py
python benchmarks/merge_sota_benchmark.py
python benchmarks/generate_html_report.py
```

---

## 九、致谢与引用

- 原版基础平台：[Zhouhao-stak/EpitopeRank](https://github.com/Zhouhao-stak/EpitopeRank)
- 蛋白质语言模型底座：[Meta AI ESM-2 (`esm2_t33_650M_UR50D`)](https://github.com/facebookresearch/esm)
- 异构合作模型参考：[BigMHC (*Nature Machine Intelligence*, 2023)](https://github.com/KarchinLab/bigmhc)
- 临床多组学基线队列：TESLA Consortium (*Cell*, 2020) · ITSNdb · IEDB & CEDAR

如本平台对您的研究有所帮助，欢迎 Star 本仓库及原仓库 [EpitopeRank](https://github.com/Zhouhao-stak/EpitopeRank)。
