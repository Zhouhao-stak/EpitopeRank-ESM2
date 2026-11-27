# EpitopeRank-ESM2

[简体中文](README.md) · **繁體中文** · [English](README.en.md)

**基於 ESM-2-650M LoRA 與 BigMHC-IM 雙引擎異構融合的可變剪接新抗原免疫原性預測平台**

[![Tests](https://github.com/Zhouhao-stak/EpitopeRank-ESM2/actions/workflows/test.yml/badge.svg)](https://github.com/Zhouhao-stak/EpitopeRank-ESM2/actions/workflows/test.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Base Model: ESM-2-650M](https://img.shields.io/badge/ESM--2--650M-PEFT%20LoRA%205--Fold-green.svg)](https://huggingface.co/ZhouRitian/epitoperank-esm2-650m-lora-v4)
[![Dual Engine: ESM-2 + BigMHC-IM](https://img.shields.io/badge/Dual--Engine-ESM2%20%2B%20BigMHC--IM-orange.svg)](#五10-篇真實頂刊-sota-同台對比與嚴格零洩漏審計)
[![UI: 简体 / 繁體 / EN](https://img.shields.io/badge/UI-简体%20%7C%20繁體%20%7C%20EN-blueviolet.svg)](#八快速開始與接入配置)
[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](LICENSE)

> **專案演進說明**：本儲存庫為原專案 **[Zhouhao-stak/EpitopeRank](https://github.com/Zhouhao-stak/EpitopeRank)** 的蛋白質大模型與多引擎免疫原性升級版（`SpliceGAIP_ESM2`）。
> 在完整保留 rMATS 可變剪接統計分析、ORF 自動重建、多智能體報告與可復現軌跡回放的基礎上，新增 **ESM-2-650M LoRA 兩階段 5 折集成**、**v5-beta Mut–WT 生物物理孿生殘差頭**、**TESLA 多組學臨床融合引擎**、**ESM-2 + BigMHC-IM 雙引擎合作打分**，以及 **Web UI 簡體中文 / 繁體中文 / English 三語言即時切換**。

---

## 目錄

- [核心升級亮點](#一核心升級亮點)
- [系統架構與模型設計](#二系統架構與模型設計)
- [訓練資料集建構與兩階段 5 折微調指標](#三訓練資料集建構與兩階段-5-折微調指標)
- [v5-beta 孿生殘差頭與 TESLA 多組學臨床融合](#四v5-beta-孿生殘差頭與-tesla-多組學臨床融合)
- [10 篇真實頂刊 SOTA 同台對比與嚴格零洩漏審計](#五10-篇真實頂刊-sota-同台對比與嚴格零洩漏審計)
- [20 篇權威文獻廣度基準驗證](#六20-篇權威文獻廣度基準驗證n3260)
- [完整互動式報告與可復現資產](#七完整互動式報告與可復現資產)
- [快速開始與接入配置](#八快速開始與接入配置)
- [致謝與引用](#九致謝與引用)

---

## 一、核心升級亮點

1. **補齊「能結合 MHC ≠ 能激活 T 細胞」的免疫原性空白**
   傳統工具（如 NetMHCpan、MHCflurry）主要預測 pMHC 結合親和力，但臨床濕實驗顯示強結合候選肽段中僅約 6% 能真正誘發 CD8+ T 細胞應答。本專案基於 Meta AI `facebook/esm2_t33_650M_UR50D`（6.5 億參數）進行參數高效微調（PEFT LoRA），直接建模 **肽段–HLA 結合槽** 的免疫原性激活機率與逐殘基 TCR 接觸熱點。
2. **於可變剪接新抗原領域顯著領先傳統模型**
   在 3 篇 2023–2026 年剪接新抗原頂刊佇列（*Cell* 2025、*Genome Res* 2026、*PNAS* 2023 IRIS）上，單靠 MHC 結合預測（IEDB NetMHCpan-4.1）宏平均 AUROC 僅 `0.5848`，而 **ESM-2-650M LoRA 單模型達到 `0.7007`（+0.1159）**。
3. **發現異構正交互補，建構雙引擎合作打分**
   實測顯示微調後的 ESM-2 與領域專用模型 `BigMHC-IM`（*Nature Machine Intelligence* 2023）高度正交互補（零洩漏 Spearman $\rho = 0.2489$，Top-20% Jaccard 重疊度僅 `0.2079`）。雙引擎合作打分在 10 篇頂刊（`N=2,136`）上將宏平均 AUROC 推高至 **`0.7355`**，全樣本 Pooled AUROC 達 **`0.8070`**，Pooled AUPRC 提升 **+24.6%**；嚴格剔除 927 條 BigMHC-IM 訓練集重疊樣本後，零洩漏 Top-50 陽性命中率由單模型的 32%/34% 躍升至 **50%–52%**。
4. **三語言自由切換與生產級 CPU INT8 量化微服務**
   Web UI 內建 **簡體中文 / 繁體中文 / English** 一鍵即時切換（內建離線 OpenCC 繁簡轉換資源，無需外部 CDN）；推論端支援 LoRA 權重合併與 CPU 動態 INT8 量化，離線時自動優雅降級。

---

## 二、系統架構與模型設計

```text
rMATS JC 五類剪接事件 + 樣本中繼資料 / 臨床肽段表
   │
   ├─► 1. ORF 自動重建 & 剪接連接肽生成 (epitoperank/splicing/orf_builder.py)
   ├─► 2. IEDB NetMHCpan-4.1 EL 結合與加工預測 (binding, processing)
   ├─► 3. 人類正常蛋白組去重比對 (novelty / self_hit)
   ├─► 4. 【新增】ESM-2-650M LoRA + BigMHC-IM 雙引擎免疫原性服務
   │       ├─ 聯合編碼: <cls> 肽段(8–14 aa) <eos> 34-aa HLA-I 結合槽偽序列 <eos>
   │       ├─ AttentionPoolHead: 肽段聚焦注意力池化 + 逐殘基 TCR 熱點熱力圖
   │       ├─ v5-beta 孿生殘差頭: Mut–WT 疏水性/電荷/TCR 接觸區生物物理校準
   │       └─ TESLA 多組學臨床融合: 結合親和力 + 穩定性 + RNA TPM + 克隆豐度 CCF
   ▼
   5. 6 維透明加權綜合排序 & Tier A/B/C/D / Clinical Tier-1/2/3 分級
   ▼
   6. Web UI（簡體/繁體/EN 切換）/ 桌面端 / HTML & PDF 論文級分析報告
```

### 核心模型規格

| 元件 | 規格說明 |
|---|---|
| **預訓練底座** | `facebook/esm2_t33_650M_UR50D`（33 層 Transformer，hidden_size = `1280`） |
| **PEFT LoRA** | `r=16, lora_alpha=32, lora_dropout=0.08`，作用於全層 `["query", "key", "value", "dense"]` |
| **聯合輸入格式** | `<cls> peptide(8–14 aa) <eos> HLA_34aa_pseudosequence <eos>`（涵蓋 18 個高頻人類 HLA-I 等位基因） |
| **可解釋分類頭** | 肽段聚焦 `AttentionPoolHead`（僅於肽段位置計算 Masked Softmax 池化，輸出逐殘基 TCR 權重） |
| **訓練策略** | 兩階段解耦訓練（Stage 1 混合分佈預熱 pMHC 與 HLA 特異性；Stage 2 純實測資料低學習率精調）+ Temperature Scaling 溫度校準 |
| **權重託管** | Hugging Face Model Hub：[`ZhouRitian/epitoperank-esm2-650m-lora-v4`](https://huggingface.co/ZhouRitian/epitoperank-esm2-650m-lora-v4)（5 折權重，244 MB） |

---

## 三、訓練資料集建構與兩階段 5 折微調指標

訓練與評測參考腳本收錄於 [`training/`](training/)：
- [`training/01_build_v4_dataset.py`](training/01_build_v4_dataset.py)：資料集建構與防洩漏切分
- [`training/02_train_v4_twostage.py`](training/02_train_v4_twostage.py)：兩階段 LoRA 訓練與溫度校準
- [`training/03_eval_v4_ensemble.py`](training/03_eval_v4_ensemble.py)：5 折集成獨立留出集評測

### 3.1 資料工程與防洩漏策略
- **正樣本來源**：整合 **IEDB**（`tcell_search`）與 **CEDAR** 癌症表位專庫，涵蓋 18 個高頻人類 HLA-I 等位基因（7 個 HLA-A + 11 個 HLA-B），每等位基因上限 `800` 條實測陽性（`max_offset=4500`，嚴格留出 `offset >= 5000` 作為獨立盲測留出集）。
- **4 類困難負樣本（正負比 `1 : 1.25`）**：`50%` 實測困難陰性 + `25%` UniProt 人類正常蛋白背景採樣 + `13%` 跨等位基因 HLA 錯配負樣本 + `12%` 亂序與低複雜度陷阱。
- **防同源洩漏切分**：按肽段 **3-mer 同源聚類** 分配 `cluster_id`，再執行 **`StratifiedGroupKFold(n_splits=5)`** 切分。

### 3.2 5 折交叉驗證逐折實測表現（v4）

| 折號 | 純實驗驗證 Hard AUROC | 純實驗驗證 Hard AUPRC | F1 | 最優溫度 $T$ | 校準誤差 ECE |
|---|---:|---:|---:|---:|---:|
| **Fold 0** | 0.7141 | 0.7782 | 0.7181 | 2.20 | 0.0771 |
| **Fold 1** | 0.7119 | 0.7813 | 0.7325 | 2.20 | 0.0820 |
| **Fold 2** | 0.7613 | 0.8300 | 0.7382 | 1.55 | 0.1144 |
| **Fold 3** | 0.7248 | 0.7876 | 0.7340 | 2.05 | 0.0853 |
| **Fold 4** | 0.7391 | 0.8036 | 0.7281 | 2.45 | 0.0886 |
| **5 折均值 ± 標準差** | **0.7302 ± 0.0183** | **0.7961** | **0.7302** | — | — |

**獨立留出集（5 折集成，`offset >= 5000`）**：
- Hard Benchmark（30 陽 / 60 陰）：**AUROC = `0.7817`** ｜ **AUPRC = `0.6056`** ｜ **Recall = `90.0%`（27/30）**
- 經典腫瘤表位均分：**`0.7031`**（KRAS G12D `0.8074`、HER2 `0.7399`、MAGE-A3 `0.7382`、MART-1 `0.7124`）
- **HLA 錯配特異性差值**（正確 HLA − 錯配 HLA）：**`+0.2765`** ｜ 低複雜度陷阱均分：`0.2522`

---

## 四、v5-beta 孿生殘差頭與 TESLA 多組學臨床融合

實作腳本見 [`training/clinical_fusion.py`](training/clinical_fusion.py)：

1. **v5-beta Mut–WT 生物物理孿生殘差頭**：
   在 **ITSNdb 176 對** 臨床突變/野生型（Mut–WT）配對資料集上按嚴格 5 折作者分組（OOF）擬合，凍結 v4 底座參數（`<0.01 ms` 推論，無 WT 時 100% 零遺忘退回 v4 分數）：
   $$\text{logit}_{\text{v5b}} = \text{logit}(\text{v4}) + 0.095 \cdot \frac{\Delta\text{KD}}{3.0} + 0.141 \cdot (\Delta\text{Chg} - 0.35) + 0.077 \cdot (\text{is\_tcr} - 0.5)$$
   - ITSNdb 5 折 OOF AUROC 由 `0.6919` 提升至 **`0.7066`**。
2. **TESLA 多組學臨床融合引擎**（Wells et al., *Cell* 2020，6 名黑色素瘤/NSCLC 患者，`N=511`，陽性率 6.46%）：
   基於嚴格 **留一患者交叉驗證（LOPO-CV）** 標定：
   - 單純 ESM-2 v4 序列 AUROC：**`0.7097`**，Top-20 命中率 **`48.5%`**（vs DeepHLApan `0.4544` / `18.2%`）；
   - 接入 TESLA 多組學臨床融合後，LOPO-CV AUROC 躍升至 **`0.8251`**，按患者 **Top-20 命中率達 `72.7%`（24/33）**。

---

## 五、10 篇真實頂刊 SOTA 同台對比與嚴格零洩漏審計

所有資料集均直接自 IEDB Query API 按真實 PubMed ID 拉取（零合成資料），原始資料與逐條預測表完整開源於 [`benchmarks/datasets/`](benchmarks/datasets/) 與 [`benchmarks/results/`](benchmarks/results/)。

### 5.1 10 篇真實發表論文全量 SOTA 同台對比（`N = 2,136`，含 3 篇剪接新抗原頂刊）

| 模型 / 融合策略 | 10 篇宏平均 AUROC | 3 篇剪接 AUROC | 3 篇剪接 AUPRC | 全樣本 Pooled AUROC | 全樣本 Pooled AUPRC | 宏平均 Top-10 PPV |
|---|---:|---:|---:|---:|---:|---:|
| Calis 理化基線 | 0.5636 | 0.5538 | 0.2889 | 0.5223 | 0.1300 | 35.0% |
| MixMHCpred 3.0 | 0.6209 | 0.5478 | 0.2577 | 0.7183 | 0.2461 | 36.0% |
| IEDB NetMHCpan-4.1 EL | 0.6328 | 0.5848 | 0.2664 | 0.7383 | 0.2559 | 51.0% |
| BigMHC-EL (7 折) | 0.6364 | 0.6493 | 0.2857 | 0.7051 | 0.2149 | 37.0% |
| PRIME 2.1 (*Cell Systems* 2023) | 0.6630 | 0.6122 | 0.3422 | 0.7269 | 0.2571 | 45.0% |
| BigMHC-IM (*NMI* 2023, 7 折) | 0.6921 | 0.5677 | 0.3459 | 0.7651 | 0.2992 | 49.0% |
| **ESM-2-650M LoRA (5 折單模型)** | 0.6618 | **0.7007** | 0.3724 | 0.6947 | 0.2034 | 34.0% |
| EpitopeRank 剪接最佳化版 (IEDB+ESM-2) | 0.6904 | 0.6908 | 0.3730 | 0.7688 | 0.2841 | 41.0% |
| **新·雙引擎合作 (`0.55×ESM-2 + 0.45×BigMHC-IM`)** | **0.7355** | 0.6655 | **0.4011** | 0.7855 | 0.3473 | **53.0%** |
| **新·EpitopeRank 合作剪接版** | **0.7170** | 0.6652 | **0.3895** | **0.8070** | **0.3539** | **53.0%** |

### 5.2 嚴格零洩漏去重驗證（Zero-Leakage Audit）

剔除 BigMHC 官方 `im_train.csv` + `im_val.csv` 重疊的 **927 條** 樣本後（淨剩 **`N = 1,209`，陽 222 / 陰 987**）：

| 零洩漏評測策略（`N = 1,209`） | 9 篇宏平均 AUROC | 3 篇剪接 AUROC | 3 篇剪接 AUPRC | Pooled AUROC | Pooled AUPRC | **Pooled Top-50 PPV** |
|---|---:|---:|---:|---:|---:|---:|
| 單獨 ESM-2-650M LoRA | 0.6667 | **0.7007** | 0.3724 | 0.6696 | 0.2671 | **32.0% (16/50)** |
| 單獨 BigMHC-IM | 0.6972 | 0.5677 | 0.3459 | 0.6863 | 0.2949 | **34.0% (17/50)** |
| **雙引擎合作（50/50 機率融合）** | 0.7323 | 0.6505 | 0.3915 | 0.7161 | 0.3455 | **52.0% (26/50)** |
| **雙引擎合作（50/50 秩融合）** | **0.7384** | 0.6702 | **0.4233** | 0.7229 | 0.3588 | **50.0% (25/50)** |
| **三引擎協同（IEDB+ESM-2+BigMHC-IM）** | 0.7348 | 0.6536 | 0.3814 | **0.7457** | **0.3710** | **50.0% (25/50)** |

---

## 六、20 篇權威文獻廣度基準驗證（`N=3,260`）

詳見 [`benchmarks/results/bench20_summary.json`](benchmarks/results/bench20_summary.json)：
- **10 篇二分類基準佇列（`N=2,595`）**：樣本加權 AUROC **`0.7257`**。
- **8 篇臨床疫苗與病毒真陽性佇列（`N=592`）**：平均 Recall@0.5 達 **`91.1%`**（Zhang SQ *Nat Biotech* `97.3%`、Ott NeoVax `90.9%`、Sahin BioNTech `85.7%`、登革熱 *PNAS* `92.0%`、新冠康復者 *BiB* 2021 `82.9%` vs DeepImmuno `30.5%`）。

---

## 七、完整互動式報告與可復現資產

| 資產檔案 | 內容說明 |
|---|---|
| [`benchmarks/BENCHMARK_REPORT.md`](benchmarks/BENCHMARK_REPORT.md) | 10 篇真實頂刊基準評測 Markdown 報告 |
| [`benchmarks/EpitopeRank_ESM2_Benchmark_Report.html`](benchmarks/EpitopeRank_ESM2_Benchmark_Report.html) | 10 篇頂刊 + 雙引擎合作 + 零洩漏審計互動式 HTML 報告 |
| [`docs/reports/ESM2_LoRA_20篇权威论文基准检验报告.html`](docs/reports/ESM2_LoRA_20篇权威论文基准检验报告.html) | 20 篇權威文獻（`N=3,260`）盲測完整互動式 HTML 報告 |
| [`docs/reports/ESM2_LoRA_四代迭代实验报告.html`](docs/reports/ESM2_LoRA_四代迭代实验报告.html) | v1 → v4 四代迭代消融實驗與超參數演進報告 |
| [`docs/reports/ESM2_LoRA_v4_六大真实论文基准评测报告.html`](docs/reports/ESM2_LoRA_v4_六大真实论文基准评测报告.html) | v4 六大經典佇列基準詳細評測報告 |
| [`docs/ESM2_MODEL_WHITEPAPER.md`](docs/ESM2_MODEL_WHITEPAPER.md) | ESM-2-650M LoRA（v4 + v5-beta）技術白皮書與工程接入方案 |

---

## 八、快速開始與接入配置

```bash
python -m venv venv
venv\Scripts\activate            # Windows
# source venv/bin/activate       # macOS / Linux

pip install -r requirements.txt
python serve_ui.py --port 8800
# 瀏覽器開啟 http://127.0.0.1:8800/，右上角可一鍵切換「简体 / 繁體 / EN」
```

複製 `.env.example` 為 `.env` 以接入 ESM-2 雙引擎免疫原性微服務（未配置時自動降級為 5 維基礎打分）：

```ini
EPITOPERANK_ESM2_URL=https://esm2.immich.pw
EPITOPERANK_ESM2_API_KEY=<your-api-key>
EPITOPERANK_ESM2_ENSEMBLE=true
EPITOPERANK_ESM2_TIMEOUT=45
```

---

## 九、致謝與引用

- 原版基礎平台：[Zhouhao-stak/EpitopeRank](https://github.com/Zhouhao-stak/EpitopeRank)
- 蛋白質語言模型底座：[Meta AI ESM-2 (`esm2_t33_650M_UR50D`)](https://github.com/facebookresearch/esm)
- 異構合作模型參考：[BigMHC (*Nature Machine Intelligence*, 2023)](https://github.com/KarchinLab/bigmhc)
- 臨床多組學基線佇列：TESLA Consortium (*Cell*, 2020) · ITSNdb · IEDB & CEDAR
