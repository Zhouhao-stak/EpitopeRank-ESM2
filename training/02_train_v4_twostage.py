#!/usr/bin/env python3
"""v4 冲分版 · 步骤 2：两阶段自动串联 + 断点续训 + LoRA r=16 + Label Smoothing。

核心升级：
1. 每折自动完成「阶段 1（混合数据 3 epoch 预热 pMHC 结合）→ 阶段 2（纯实测数据 3 epoch 精调免疫原性）」。
2. 内置断点续训：每折完成后写入 `stage2_done.flag`，Colab 断线重跑自动跳过已完成的折！
3. 模型增强：LoRA r=16 / alpha=32 + 余弦学习率调度 + Label Smoothing (0.05) + 梯度裁剪 + 温度校准。
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from transformers import AutoTokenizer

LAB_ROOT = Path(__file__).resolve().parent.parent


def _load_v3_trainer():
    here = Path(__file__).resolve().parent
    for cand in (here / "02_train_v3_hla.py", LAB_ROOT / "stage3_hla" / "02_train_v3_hla.py"):
        if cand.is_file():
            spec = importlib.util.spec_from_file_location("v3t", cand)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod
    raise FileNotFoundError("请将 02_train_v3_hla.py 放在同级目录或 ../stage3_hla/ 下")


def run_epoch(model, loader, optimizer, criterion, device, amp_dtype, scaler, use_scaler, smooth: float = 0.05) -> float:
    """带 Label Smoothing 与梯度裁剪的单轮训练。"""
    model.train()
    total_loss = 0.0
    for batch in loader:
        optimizer.zero_grad(set_to_none=True)
        labels = batch["labels"].to(device)
        if smooth > 0:
            labels = labels * (1.0 - smooth) + 0.5 * smooth
        with torch.autocast(device_type=device.type, dtype=amp_dtype, enabled=(device.type == "cuda")):
            logits, _ = model(
                batch["input_ids"].to(device),
                batch["attention_mask"].to(device),
                batch["peptide_mask"].to(device),
            )
            loss = criterion(logits, labels)
        if use_scaler:
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            scaler.step(optimizer)
            scaler.update()
        else:
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
        total_loss += float(loss.item())
    return total_loss / max(1, len(loader))


def train_two_stage_fold(rows: list[dict], fold: int, args, v3, tokenizer, device, amp_dtype) -> dict:
    """对单折执行阶段 1 + 阶段 2 完整训练（支持断点续训）。"""
    fold_dir = args.output_dir / f"fold_{fold}"
    done_flag = fold_dir / "stage2_done.flag"
    if done_flag.is_file() and (fold_dir / "meta.json").is_file() and not args.force:
        saved = json.loads((fold_dir / "meta.json").read_text(encoding="utf-8"))
        print(f"\n[跳过 Fold {fold}] 检测到已完成断点：{saved.get('metrics_stage2')}")
        return saved.get("metrics_stage2", {})

    pure_sources = {"iedb_hla_positive", "cedar_cancer_positive", "iedb_hla_negative_hard", "cedar_cancer_negative_hard"}
    s1_train = [r for r in rows if int(r["fold"]) != fold]
    s1_val = [r for r in rows if int(r["fold"]) == fold]
    s2_train = [r for r in rows if int(r["fold"]) != fold and (r["source"] in pure_sources or r["source"] in {"low_complexity_decoy", "hla_mismatch_negative"})]
    s2_val = [r for r in rows if int(r["fold"]) == fold and r["source"] in pure_sources]

    print(f"\n================ Fold {fold} | 阶段1训练={len(s1_train)} | 阶段2纯实验训练={len(s2_train)} / 验证={len(s2_val)} ================")
    collate = v3.make_collate_fn(tokenizer)
    s1_train_loader = DataLoader(v3.PMhcDataset(s1_train), batch_size=args.batch_size, shuffle=True, collate_fn=collate)
    s1_val_loader = DataLoader(v3.PMhcDataset(s1_val), batch_size=args.batch_size * 2, shuffle=False, collate_fn=collate)
    s2_train_loader = DataLoader(v3.PMhcDataset(s2_train), batch_size=args.batch_size, shuffle=True, collate_fn=collate)
    s2_val_loader = DataLoader(v3.PMhcDataset(s2_val), batch_size=args.batch_size * 2, shuffle=False, collate_fn=collate)

    model = v3.PMhcEsm2Scorer(args.model_name, lora_r=args.lora_r, lora_alpha=args.lora_alpha, lora_dropout=0.08).to(device)
    if fold == 0:
        model.encoder.print_trainable_parameters()

    use_scaler = device.type == "cuda" and amp_dtype == torch.float16
    scaler = torch.amp.GradScaler("cuda", enabled=use_scaler)

    # ---- 阶段 1：混合数据预热 pMHC 结合与 HLA 特异性 ----
    opt1 = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=args.lr_stage1, weight_decay=0.01)
    sch1 = torch.optim.lr_scheduler.CosineAnnealingLR(opt1, T_max=args.epochs_stage1)
    crit1 = nn.BCEWithLogitsLoss()
    for ep in range(1, args.epochs_stage1 + 1):
        loss = run_epoch(model, s1_train_loader, opt1, crit1, device, amp_dtype, scaler, use_scaler, smooth=0.05)
        sch1.step()
        m1 = v3.evaluate(model, s1_val_loader, device, amp_dtype)
        print(f"  [阶段1] Epoch {ep}/{args.epochs_stage1} | loss={loss:.4f} | 全量 AUROC={m1['auroc']:.4f} | AUPRC={m1['auprc']:.4f}", flush=True)

    # ---- 阶段 2：纯实测 Positive vs Negative 精调免疫原性 ----
    n_pos = sum(1 for r in s2_train if int(r["label"]) == 1)
    n_neg = sum(1 for r in s2_train if int(r["label"]) == 0)
    pos_weight = torch.tensor([n_neg / max(1, n_pos)], dtype=torch.float32, device=device)
    opt2 = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=args.lr_stage2, weight_decay=0.02)
    sch2 = torch.optim.lr_scheduler.CosineAnnealingLR(opt2, T_max=args.epochs_stage2)
    crit2 = nn.BCEWithLogitsLoss(pos_weight=pos_weight)

    best_m = v3.evaluate(model, s2_val_loader, device, amp_dtype)
    print(f"  [阶段2] Epoch 0 (阶段1基线) | 纯实验 Hard AUROC={best_m['auroc']:.4f} | AUPRC={best_m['auprc']:.4f} | ECE={best_m['ece']:.4f}", flush=True)
    v3.save_checkpoint(model, fold_dir, {
        "version": "v4_hla_twostage", "base_model": args.model_name, "hidden_size": model.head.classifier.in_features,
        "lora_r": args.lora_r, "lora_alpha": args.lora_alpha, "temperature": best_m["temperature"], "fold": fold,
        "metrics_stage2": best_m,
    })

    for ep in range(1, args.epochs_stage2 + 1):
        loss = run_epoch(model, s2_train_loader, opt2, crit2, device, amp_dtype, scaler, use_scaler, smooth=0.03)
        sch2.step()
        m2 = v3.evaluate(model, s2_val_loader, device, amp_dtype)
        print(
            f"  [阶段2] Epoch {ep}/{args.epochs_stage2} | loss={loss:.4f} | "
            f"纯实验 Hard AUROC={m2['auroc']:.4f} | AUPRC={m2['auprc']:.4f} | F1={m2['f1']:.4f} | "
            f"T={m2['temperature']:.2f} | ECE={m2['ece']:.4f}",
            flush=True,
        )
        if m2["auroc"] > best_m["auroc"]:
            best_m = m2
            v3.save_checkpoint(model, fold_dir, {
                "version": "v4_hla_twostage", "base_model": args.model_name, "hidden_size": model.head.classifier.in_features,
                "lora_r": args.lora_r, "lora_alpha": args.lora_alpha, "temperature": m2["temperature"], "fold": fold,
                "best_epoch_stage2": ep, "metrics_stage2": m2,
            })

    done_flag.write_text("ok", encoding="utf-8")
    return best_m


def main() -> None:
    parser = argparse.ArgumentParser(description="v4 两阶段自动串联 + 断点续训 5 折训练")
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--model_name", type=str, default="facebook/esm2_t33_650M_UR50D")
    parser.add_argument("--folds", type=str, default="0,1,2,3,4")
    parser.add_argument("--epochs_stage1", type=int, default=3)
    parser.add_argument("--epochs_stage2", type=int, default=3)
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--lr_stage1", type=float, default=2.5e-4)
    parser.add_argument("--lr_stage2", type=float, default=5e-5)
    parser.add_argument("--lora_r", type=int, default=16)
    parser.add_argument("--lora_alpha", type=int, default=32)
    parser.add_argument("--force", action="store_true", help="忽略断点强制重训")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    v3 = _load_v3_trainer()
    v3.set_seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    amp_dtype = torch.bfloat16 if (device.type == "cuda" and torch.cuda.is_bf16_supported()) else torch.float16
    print(f"[v4 训练] 设备={device} | 精度={amp_dtype if device.type == 'cuda' else 'fp32'} | LoRA r={args.lora_r}")

    with args.data.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    tokenizer = AutoTokenizer.from_pretrained(args.model_name)

    fold_ids = [int(x.strip()) for x in args.folds.split(",") if x.strip()]
    summary = {f"fold_{f}": train_two_stage_fold(rows, f, args, v3, tokenizer, device, amp_dtype) for f in fold_ids}
    aurocs = [m["auroc"] for m in summary.values() if "auroc" in m]
    auprcs = [m["auprc"] for m in summary.values() if "auprc" in m]
    res = {
        "version": "v4_hla_twostage",
        "folds": summary,
        "mean_hard_auroc": round(float(np.mean(aurocs)), 4) if aurocs else 0.0,
        "std_hard_auroc": round(float(np.std(aurocs)), 4) if aurocs else 0.0,
        "mean_hard_auprc": round(float(np.mean(auprcs)), 4) if auprcs else 0.0,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "cv_summary.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n========== v4 两阶段 5 折纯实验汇总 ==========")
    print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
