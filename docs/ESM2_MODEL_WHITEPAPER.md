# EpitopeRank · ESM-2-650M LoRA（v4 + v5-beta）新抗原免疫原性模型技术白皮书与系统接入方案

> **文档用途**：本技术文稿完整阐述自研 **ESM-2-650M LoRA（v4 + v5-beta）HLA-I 限制性新抗原免疫原性预测与多组学临床融合模型** 的核心原理、20 篇顶刊论文湿实验验证数据、线上 128 核推理服务规范，以及**无缝接入 `EpitopeRank`（`E:\SpliceGAIP`）主系统的分步工程落地指南**。可直接用于科研论文方法学撰写、竞赛/项目申报支撑材料以及研发团队工程对接。

---

## 一、模型定位与解决的核心痛点

在传统肿瘤新抗原与剪接新抗原筛选流程中（包括 `EpitopeRank` 当前的 5 维打分体系：`binding`、`processing`、`expression`、`effect`、`novelty`），存在两个长期痛点：

1. **“能结合 MHC” ≠ “能激活 T 细胞”**：传统工具（如 NetMHCpan、MHCflurry）只预测肽段与 HLA 的结合亲和力或呈递概率，但临床湿实验（如 *Cell* 2020 TESLA 联盟）表明，**强结合候选肽段中仅有约 6% 能真正诱发 CD8+ T 细胞免疫应答**。
2. **缺乏残基级可解释性与突变/野生型（Mut–WT）辨别**：传统黑盒打分无法告诉临床/实验团队“肽段上哪几个氨基酸是 TCR 识别热点”，也难以评估非锚位（P4–P8）单氨基酸突变相对于野生型自身肽段打破免疫耐受的潜力。

**本模型（EpitopeRank-ESM2）的定位**：作为 `EpitopeRank` 的**第 6 个核心打分维度（`immunogenicity`）**与**临床多组学融合引擎**，专门补齐“**T 细胞免疫原性预测 + 残基级 TCR 热点可解释性 + 突变/野生型生物物理校准**”三大短板。

---

## 二、模型具体架构与关键技术创新

### 2.1 模型核心规格

| 维度 | 具体规格 |
|---|---|
| **预训练底座** | Meta AI `facebook/esm2_t33_650M_UR50D`（33 层 Transformer，6.5 亿参数，1280 维隐层） |
| **参数高效微调** | PEFT **LoRA**（`r=16, alpha=32, dropout=0.08`，作用于全层 `query / key / value / dense`），每折仅 48 MB 轻量增量权重 |
| **联合序列编码** | `<cls> 候选短肽(8–15 aa) <eos> HLA-I 结合槽 34-aa 伪序列 <eos>`，覆盖 **18 个高频人类 HLA-I 等位基因**（覆盖全球 >90% 人群） |
| **可解释分类头** | 肽段聚焦 **AttentionPoolHead**（仅在短肽 token 上做 Masked Softmax 注意力池化），同时输出 **免疫原性概率** 与 **逐氨基酸注意力权重（P1–P15 热点热力图）** |
| **概率校准与集成** | 严格按 3-mer 同源聚类分组的 **5 折分层交叉验证（StratifiedGroupKFold，防同源泄漏）** + 独立验证集 **温度缩放（Temperature Scaling）** + **5 折概率集成** |
| **两阶段解耦训练** | **阶段 1**（混合负样本 + HLA 错配负样本 + 低复杂度诱饵）：学习 pMHC 结合与 HLA 等位基因特异性；<br>**阶段 2**（纯湿实验 Positive vs Negative，小学习率 `5e-5` + Label Smoothing）：专注精调 T 细胞免疫原性 |
| **v5-beta 零遗忘孪生头** | **冻结 v4 权重** + 轻量级生物物理 Mut–WT 残差校准头：当提供等长野生型 `wt_peptide` 时，在 `<0.01 ms` 内提取突变位点的 **Kyte-Doolittle 疏水性增益（`d_kd`）**、**生理电荷跃迁（`d_chg`）** 与 **TCR 接触区位置（`is_tcr`, P4–P(L-2)）** 对 logit 进行可解释校准，100% 保留 v4 原有泛化能力 |
| **多组学临床融合引擎** | 基于 TESLA (*Cell* 2020) 真实患者严格留一患者交叉验证（LOPO-CV）标定，融合 `ESM-2 v5-beta (+0.976)`、`NetMHCpan -log10(IC50) (+1.048)`、`RNA log1p(TPM) (+0.716)`、`pMHC 结合稳定性 (+0.257)` 与克隆丰度 `CCF`，输出 **Tier-1 / Tier-2 / Tier-3** 临床合成优先级 |
| **权重永久托管** | Hugging Face Model Hub：`https://huggingface.co/ZhouRitian/epitoperank-esm2-650m-lora-v4`（5 折完整权重，244 MB） |

### 2.2 128 核 CPU 生产级加速优化

为在无 GPU 的 128 核 Intel Xeon Platinum 8358P 服务器上实现秒级响应，推理服务（`server.py`）实施了三项底层优化：
1. **LoRA 静态融合（`merge_and_unload()`）**：启动时将 5 折 LoRA 低秩矩阵合并进主干线性层，彻底消除推理期 LoRA 分支开销。
2. **CPU 动态 INT8 量化（`quantize_dynamic(..., {nn.Linear}, dtype=torch.qint8)`）**：充分利用 Xeon `AVX-512 VNNI` 指令集。
3. **防线程踩踏调优（`TORCH_NUM_THREADS=16` + `uvicorn --workers 2`）**：避免 128 核 OpenMP 线程池同步锁竞争。

**实测加速效果**：3 条肽段 5 折集成从原始 FP32 的 **32.6 秒** 压缩至 **1.36 秒（提速 24.1 倍）**；单折极速模式仅 **0.23 秒**；1,832 条批量推理平均 **206 ms / 条**。

---

## 三、权威论文验证表现（20 篇顶刊 · 3,260 条湿实验样本）

在**严格零数据泄漏**条件下，于 128 核服务器实装模型上完成了 20 个权威发表论文湿实验队列的全量盲测（完整可视化报告见 `E:\ESM2_Epitope_Lab\stage9_bench20\ESM2_LoRA_20篇权威论文基准检验报告.html`）：

| 评测维度 | 核心指标 | 竞品 / 基线对比 |
|---|---|---|
| **内部独立留出集（v4 5 折集成）** | Hard AUROC **`0.7817`**｜AUPRC **`0.6056`**｜Recall **`90.0%`**｜HLA 错配特异性差值 **`+0.2765`** | 经典肿瘤靶点 `KRAS G12D` 得分 `0.8074`（错配 HLA 仅 `0.3040`） |
| **10 篇二分类权威论文汇总（N=2,595）** | 样本加权 AUROC **`0.7257`**（算术均值 **`0.6920`**） | 纯序列零多组学输入 |
| **TESLA 联盟队列（*Cell* 2020, N=511）** | 纯序列 AUROC **`0.7097`**｜患者 Top-20 命中 **`16/33 (48.5%)`** | DeepHLApan 仅 `0.4544` / `6/33`（**+0.2553 / 2.67×**） |
| **TESLA 多组学临床融合（LOPO-CV, N=503）** | 融合 AUROC **`0.8251`**｜AUPRC **`0.2188`**｜患者 Top-20 命中 **`24/33 (72.7%)`** | 传统 TESLA 多组学 `0.7978` / `22/33`；DeepHLApan 的 **4.0 倍** |
| **Strønen 全筛队列（*Science* 2016, N=1,027）** | AUROC **`0.8122`**（1.66% 极端低阳性率，**3.10×** AUPRC 富集） | 逼近 NetMHCpan (`0.8453`) |
| **Fehlings 队列（*JITC* 2019, N=641）** | AUROC **`0.6066`**（1.46× 富集） | 超越 NetMHCpan (`0.5672`, **+0.0394**) |
| **ITSNdb 176 对临床 Mut–WT（5 折 OOF）** | `v5-beta` AUROC **`0.7066`** | 零遗忘超越冻结 v4 (`0.6919`, **+0.0147**) |
| **8 篇临床疫苗与病毒真阳性队列（N=592）** | 平均 Recall@0.5 **`91.1%`**（Zhang SQ *Nat Biotech* **`97.3%`**、Ott NeoVax **`90.9%`**、Sahin BioNTech **`85.7%`**、登革热 *PNAS* **`92.0%`**） | 新冠康复者（*BiB* 2021）**`82.9%`** vs DeepImmuno **`30.5%`（+52.4%）** |

---

## 四、线上推理服务与 API 协议

- **128 核本机内网地址（同机部署 `EpitopeRank` 时强烈推荐，延迟仅 ~1.5 ms）**：`http://127.0.0.1:8090`
- **公网 HTTPS 穿透地址（桌面端/异地调用）**：`https://esm2.immich.pw`
- **鉴权方式**：请求头携带 `X-API-Key: <ESM2_API_KEY>`（或 `Authorization: Bearer <ESM2_API_KEY>`）
- **核心端点**：
  - `GET /health`：健康检查（返回 `model_loaded`、`folds`、`quantized_int8`、`v5beta_siamese`、`clinical_fusion`）
  - `GET /api/v1/alleles`：查询支持的 18 个 HLA-I 等位基因
  - `POST /api/v1/score`：单一 HLA 批量打分（最多 2,000 条/次，可选传 `wt_peptides`、`affinity_nm`、`stability_hours`、`rna_tpm`、`ccf`）
  - `POST /api/v1/score_clinical`：多 HLA 结构化临床打分（推荐用于 `EpitopeRank` 主流程对接，最多 1,000 条/次）

---

## 五、如何接入 `EpitopeRank`（`E:\SpliceGAIP`）完整工程方案

通过审计 `E:\SpliceGAIP\epitoperank\` 现有代码结构，你的主系统已经具备极佳的模块化扩展点（`peptide/local_models.py`、`peptide/scoring.py`、`peptide/pipeline.py`、`api/app.py`、`interface/web_ui.py`、`report/antigens.py`）。

**推荐采用“HTTP 微服务解耦接入 + 优雅降级”架构**（而非把 2.5 GB PyTorch 模型直接打进 Windows `.exe` 安装包），优点：
1. `EpitopeRank-Desktop.exe` 体积保持 **102 MB** 不膨胀；
2. 推理算力全部由 128 核服务器承担，桌面端秒出结果；
3. 当 ESM-2 服务未配置或暂时离线时，`peptide/scoring.py` 自动按已有 5 个维度重新归一化权重，**主流程零报错、100% 向后兼容**。

### 总体数据流架构

```text
EpitopeRank 剪接/变异候选肽段 (peptides + allele + 可选 WT/IC50/TPM/ΔPSI)
   │
   ├─► 1. IEDB / MHCflurry 结合与加工预测 (binding, processing)
   ├─► 2. 正常蛋白组去重比对 (novelty / self_hit)
   ├─► 3. 【新增】epitoperank/peptide/esm2_client.py
   │       └─► POST /api/v1/score_clinical (128 核私有服务)
   │           返回: esm2_v4_score, v5beta_score, residue_weights (热点), mut_wt_detail, clinical_fusion
   │
   ▼
4. epitoperank/peptide/scoring.py (6 维透明加权综合排序)
   ├─► 接入第 6 维: immunogenicity (权重 0.25)
   ├─► 证据分层升级: Tier A/B/C/D + Clinical Tier-1/2/3
   ▼
5. Web UI (web_ui.py) & HTML 报告 (report/antigens.py)
   └─► 展示免疫原性分、v5-beta 突变位点徽章与逐残基注意力热力图
```

---

### Step 1：配置环境变量（`.env` / `epitoperank/config.py`）

在 `E:\SpliceGAIP\.env`（以及配置向导）中新增 4 个可选环境变量（绝不硬编码明文密码进代码仓库）：

```env
# ESM-2-650M LoRA 推理服务地址（128核本机部署用 http://127.0.0.1:8090，桌面端用公网 HTTPS）
EPITOPERANK_ESM2_URL=https://esm2.immich.pw
# 服务端设置的 ESM2_API_KEY（纯英文/数字）
EPITOPERANK_ESM2_API_KEY=你的API密码
# 是否默认启用 5 折集成（true=高精度~2秒，false=单折极速~1秒）
EPITOPERANK_ESM2_ENSEMBLE=true
# 单次 HTTP 超时秒数
EPITOPERANK_ESM2_TIMEOUT=45
```

---

### Step 2：新增推理客户端 `epitoperank/peptide/esm2_client.py`

在 `E:\SpliceGAIP\epitoperank\peptide\` 下新建 `esm2_client.py`（结构对齐现有的 `local_models.py`）：

```python
"""EpitopeRank · 远程 ESM-2-650M LoRA (v4 + v5-beta) 免疫原性推理客户端。"""
from __future__ import annotations

import os
from typing import Any, Mapping, Sequence
import requests

SUPPORTED_HLAS: frozenset[str] = frozenset({
    "HLA-A*01:01", "HLA-A*02:01", "HLA-A*03:01", "HLA-A*11:01",
    "HLA-A*24:02", "HLA-A*26:01", "HLA-A*68:01", "HLA-B*07:02",
    "HLA-B*08:01", "HLA-B*15:01", "HLA-B*27:05", "HLA-B*35:01",
    "HLA-B*40:01", "HLA-B*44:02", "HLA-B*44:03", "HLA-B*51:01",
    "HLA-B*57:01", "HLA-B*58:01",
})


def _base_url() -> str:
    return os.getenv("EPITOPERANK_ESM2_URL", "").strip().rstrip("/")


def _api_key() -> str:
    return os.getenv("EPITOPERANK_ESM2_API_KEY", "").strip()


def status() -> dict[str, Any]:
    """探测 ESM-2 推理服务健康状态，供 /api/status 与前端状态徽章展示。"""
    url = _base_url()
    if not url:
        return {"name": "esm2_lora_v4", "available": False, "detail": "未配置 EPITOPERANK_ESM2_URL"}
    try:
        r = requests.get(f"{url}/health", timeout=5)
        r.raise_for_status()
        data = r.json()
        return {
            "name": "esm2_lora_v4",
            "available": bool(data.get("model_loaded")),
            "version": "v4+v5beta",
            "detail": f"{data.get('folds', 0)}折 INT8={data.get('quantized_int8')} 临床融合={data.get('clinical_fusion')}",
        }
    except Exception as exc:
        return {"name": "esm2_lora_v4", "available": False, "detail": str(exc)[:180]}


def score_candidates(
    rows: Sequence[Mapping[str, Any]],
    *,
    ensemble: bool | None = None,
    batch_size: int = 200,
) -> dict[tuple[str, str], dict[str, Any]]:
    """
    批量调用 /api/v1/score_clinical，返回 {(peptide, allele): result_dict}。
    若服务未配置或超时，安全返回空字典，由 scoring.py 自动优雅降级。
    """
    url = _base_url()
    if not url or not rows:
        return {}
    use_ens = ensemble if ensemble is not None else (os.getenv("EPITOPERANK_ESM2_ENSEMBLE", "true").lower() != "false")
    timeout = float(os.getenv("EPITOPERANK_ESM2_TIMEOUT", "45"))
    headers = {"Content-Type": "application/json"}
    if _api_key():
        headers["X-API-Key"] = _api_key()

    # 过滤出支持的 18 个 HLA 与合法 8-15 aa 肽段
    payload_items: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        pep = str(row.get("peptide") or "").strip().upper()
        hla = str(row.get("allele") or "").strip().upper()
        if not (8 <= len(pep) <= 15) or hla not in SUPPORTED_HLAS or (pep, hla) in seen:
            continue
        seen.add((pep, hla))
        item: dict[str, Any] = {"peptide": pep, "allele": hla}
        if row.get("wt_peptide"):
            item["wt_peptide"] = str(row["wt_peptide"]).strip().upper()
        if row.get("ic50_nm") is not None:
            item["affinity_nm"] = float(row["ic50_nm"])
        if row.get("stability_hours") is not None:
            item["stability_hours"] = float(row["stability_hours"])
        if row.get("expression") is not None:
            item["rna_tpm"] = float(row["expression"])
        if row.get("ccf") is not None:
            item["ccf"] = float(row["ccf"])
        payload_items.append(item)

    results_map: dict[tuple[str, str], dict[str, Any]] = {}
    for start in range(0, len(payload_items), batch_size):
        chunk = payload_items[start : start + batch_size]
        try:
            resp = requests.post(
                f"{url}/api/v1/score_clinical",
                headers=headers,
                json={"candidates": chunk, "ensemble": use_ens},
                timeout=timeout,
            )
            resp.raise_for_status()
            for res in resp.json().get("results", []):
                results_map[(res["peptide"], res["allele"])] = res
        except Exception:
            # 单个批次失败不中断主分析管线，保留已成功结果或优雅降级
            continue
    return results_map
```

---

### Step 3：升级综合排序引擎 `epitoperank/peptide/scoring.py`

在 `E:\SpliceGAIP\epitoperank\peptide\scoring.py` 中仅需做 **3 处极简改动**：

1. **在 `DEFAULT_WEIGHTS` 中加入 `immunogenicity`**（权重依据 TESLA *Cell* 2020 LOPO-CV 标准化权重标定：`ESM-2 ≈ NetMHCpan > Expression`）：
```python
DEFAULT_WEIGHTS: dict[str, float] = {
    "binding": 0.30,         # MHC-I/II percentile rank
    "immunogenicity": 0.25,  # 【新增】ESM-2-650M LoRA (v4 + v5-beta) T 细胞免疫原性概率
    "processing": 0.15,      # IEDB proteasome + TAP + MHC score
    "expression": 0.12,      # measured event/gene expression (TPM)
    "effect": 0.10,          # |ΔPSI| of the source splicing event
    "novelty": 0.08,         # absent from the supplied normal proteomes
}
```

2. **在 `COMPONENT_DEFINITIONS` 中补充可解释定义**：
```python
"immunogenicity": "ESM-2-650M LoRA (v4 + v5-beta Mut-WT) 5-fold ensemble T-cell immunogenicity probability [0, 1]",
```

3. **在 `component_scores(row)` 中读取 `esm2_immunogenicity` 字段**：
```python
imm = _number(row.get("esm2_immunogenicity"))
if imm is not None:
    components["immunogenicity"] = _clamp(imm)
```

> **优雅降级保障**：由于 `scoring.py` 的 `composite()` 函数天然按 `available` 分量重新归一化分母（`total_weight = sum(weights[name] for name in available)`），因此当 `esm2_immunogenicity` 缺失（如离线模式或非 18 个高频 HLA）时，系统自动退回其余 5 个维度加权，**不会影响任何现有测试用例**！

---

### Step 4：在 `epitoperank/peptide/pipeline.py` 中串联打分

在 `pipeline.py` 调用 `scoring.rank(rows)` **之前**插入约 12 行代码：

```python
from epitoperank.peptide import esm2_client

# 批量调用 ESM-2 v4 + v5-beta 推理服务（未配置或离线时自动返回空字典，不影响主流程）
esm2_map = esm2_client.score_candidates(candidate_rows)
for row in candidate_rows:
    hit = esm2_map.get((str(row.get("peptide", "")).upper(), str(row.get("allele", "")).upper()))
    if hit:
        row["esm2_v4_score"] = hit.get("esm2_v4_score")
        row["esm2_immunogenicity"] = hit.get("v5beta_score", hit.get("immunogenicity_score"))
        row["esm2_residue_weights"] = hit.get("residue_weights")
        row["esm2_mut_wt_detail"] = hit.get("mut_wt_detail")
        if hit.get("clinical_fusion"):
            row["esm2_fusion_score"] = hit["clinical_fusion"]["fusion_score"]
            row["esm2_fusion_tier"] = hit["clinical_fusion"]["fusion_tier"]
```

---

### Step 5：前端 UI（`web_ui.py`）与 HTML 报告（`report/antigens.py`）可视化展示

接入数据后，可在候选新抗原表格与详情抽屉中增加 3 个高辨识度可视化元素：
1. **免疫原性得分列**：显示 `esm2_immunogenicity`（如 `0.8123`）与 `esm2_fusion_tier` 徽章（`Tier-1 优先合成` 绿色、`Tier-2 候选备选` 琥珀色）。
2. **逐残基 TCR 热点条形/热力图**：直接复用 `esm2_residue_weights` 数组（长度等于肽段长度），用与当前推理台相同的青绿色透明度映射渲染每个氨基酸 `P1..Pn`。
3. **健康状态指示灯**：在系统设置页调用 `esm2_client.status()`，展示「ESM-2-650M LoRA 5 折引擎已连接 / 离线降级中」。

---

## 六、上线验收检查清单（Integration QA Checklist）

完成上述 5 步接入后，按以下 4 项验收即可正式发布：
1. **向后兼容回归**：在未设置 `EPITOPERANK_ESM2_URL` 时运行 `pytest tests/integration/test_api.py tests/integration/test_route_hygiene.py`，确保原有 42+ 项测试 100% 通过。
2. **在线联调验收**：配置 `EPITOPERANK_ESM2_URL` 与 `EPITOPERANK_ESM2_API_KEY`，输入 `KRAS G12D`（`VVVGADGVGK` / `WT: VVVGAGGVGK` / `HLA-A*11:01`），确认 `components_used` 包含 `"immunogenicity"`，且返回 `esm2_residue_weights` 与 `Tier-1` 分层。
3. **超时降级验收**：临时填入不可达 URL，确认管线在超时后**无崩溃**、自动退回 5 维打分并在日志记录降级提示。
4. **同机低延迟部署**：将 `EpitopeRank` Web 服务部署到同一台 128 核服务器时，直接将 `EPITOPERANK_ESM2_URL` 改为 `http://127.0.0.1:8090`，消除公网穿透延迟。

