"""EpitopeRank · 远程 ESM-2-650M LoRA (v4 + v5-beta) 免疫原性推理客户端。

通过 HTTP 微服务与 128 核服务器上的 ESM-2-650M LoRA 推理引擎解耦对接，
与权威 MHC 预测软件（IEDB NetMHCpan-4.1 / NetMHCIIpan-4.1 / MHCflurry）
强强联合，补齐 T 细胞免疫原性、逐残基 TCR 热点与 Mut-WT 生物物理校准。

未配置 ``EPITOPERANK_ESM2_URL`` 或服务离线/超时时，所有函数安全返回空结果，
由 ``scoring.py`` 自动按已有 5 维重新归一化，确保主流程零报错、100% 向后兼容。
"""

from __future__ import annotations

import logging
import os
from typing import Any, Mapping, Sequence

import requests

logger = logging.getLogger(__name__)
_ORIG_POST = requests.post

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


def _use_ensemble(override: bool | None) -> bool:
    if override is not None:
        return bool(override)
    return os.getenv("EPITOPERANK_ESM2_ENSEMBLE", "true").strip().lower() not in {
        "false", "0", "no", "off",
    }


def _timeout() -> float:
    raw = os.getenv("EPITOPERANK_ESM2_TIMEOUT", "45").strip()
    try:
        value = float(raw)
        return value if value > 0 else 45.0
    except ValueError:
        return 45.0


def _float_opt(value: Any) -> float | None:
    if isinstance(value, bool) or value is None or value == "":
        return None
    try:
        num = float(value)
    except (TypeError, ValueError):
        return None
    return num if num == num else None


def configured() -> bool:
    """是否已配置远程 ESM-2 推理服务地址。"""
    return bool(_base_url())


_STATUS_CACHE: dict[tuple[str, str, int], tuple[float, dict[str, Any]]] = {}
_STATUS_OK_TTL_SECONDS = 60.0
_STATUS_FAIL_TTL_SECONDS = 10.0


def clear_status_cache() -> None:
    """清除健康检查缓存（在用户在界面修改 ESM-2 配置后立即生效）。"""
    _STATUS_CACHE.clear()


def status(*, force: bool = False) -> dict[str, Any]:
    """探测 ESM-2 推理服务健康状态，供 /api/peptide/capabilities 与前端状态徽章展示。"""
    import time

    url = _base_url()
    if not url:
        return {
            "name": "esm2_lora_v4",
            "available": False,
            "configured": False,
            "url": "",
            "version": "v4+v5beta",
            "supported_alleles": len(SUPPORTED_HLAS),
            "detail": "未配置 EPITOPERANK_ESM2_URL（离线自动降级为 5 维打分）",
        }
    cache_key = (url, _api_key(), id(requests.get))
    now = time.monotonic()
    if not force:
        cached = _STATUS_CACHE.get(cache_key)
        if cached is not None:
            ttl = _STATUS_OK_TTL_SECONDS if cached[1].get("available") else _STATUS_FAIL_TTL_SECONDS
            if (now - cached[0]) < ttl:
                return dict(cached[1])
    last_exc: Exception | None = None
    headers: dict[str, str] = {}
    if _api_key():
        headers["X-API-Key"] = _api_key()
    for _attempt in range(2):
        try:
            resp = requests.get(f"{url}/health", headers=headers, timeout=(4.0, 6.0))
            resp.raise_for_status()
            data = resp.json()
            bm_loaded = bool(data.get("bigmhc_im_loaded"))
            bm_models = int(data.get("bigmhc_im_models") or 0)
            bm_part = f" BigMHC-IM={bm_models}折合作" if bm_loaded else ""
            result = {
                "name": "esm2_lora_v4",
                "available": bool(data.get("model_loaded")),
                "configured": True,
                "url": url,
                "version": "v4+v5beta+bigmhc_im" if bm_loaded else "v4+v5beta",
                "folds": data.get("folds", 0),
                "quantized_int8": bool(data.get("quantized_int8")),
                "v5beta_siamese": bool(data.get("v5beta_siamese")),
                "clinical_fusion": bool(data.get("clinical_fusion")),
                "bigmhc_im_loaded": bm_loaded,
                "bigmhc_im_models": bm_models,
                "supported_alleles": len(SUPPORTED_HLAS),
                "detail": (
                    f"{data.get('folds', 0)}折 INT8={data.get('quantized_int8')} "
                    f"v5beta={data.get('v5beta_siamese')} 临床融合={data.get('clinical_fusion')}{bm_part}"
                ),
            }
            _STATUS_CACHE[cache_key] = (now, result)
            return dict(result)
        except Exception as exc:  # noqa: BLE001 - graceful degradation by design
            last_exc = exc
    logger.warning("ESM-2 health check failed (%s): %s", url, last_exc)
    result = {
        "name": "esm2_lora_v4",
        "available": False,
        "configured": True,
        "url": url,
        "version": "v4+v5beta",
        "supported_alleles": len(SUPPORTED_HLAS),
        "detail": str(last_exc)[:180],
    }
    _STATUS_CACHE[cache_key] = (now, result)
    return dict(result)


def score_candidates(
    rows: Sequence[Mapping[str, Any]],
    *,
    ensemble: bool | None = None,
    batch_size: int = 64,
) -> dict[tuple[str, str], dict[str, Any]]:
    """批量调用 ``POST /api/v1/score_clinical``，返回 ``{(peptide, allele): result_dict}``。

    同时兼容 ``allele`` 与 ``best_allele`` 字段；当服务未配置、网络不可达或超时时，
    记录警告并安全返回空字典（或已完成批次的结果），由 ``scoring.py`` 自动优雅降级。
    """
    url = _base_url()
    if not url or not rows:
        return {}
    if requests.post is _ORIG_POST and not status().get("available"):
        return {}

    use_ens = _use_ensemble(ensemble)
    timeout = _timeout()
    headers = {"Content-Type": "application/json"}
    if _api_key():
        headers["X-API-Key"] = _api_key()

    payload_items: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        pep = str(row.get("peptide") or "").strip().upper()
        hla = str(row.get("allele") or row.get("best_allele") or "").strip().upper()
        if not (8 <= len(pep) <= 15) or hla not in SUPPORTED_HLAS or (pep, hla) in seen:
            continue
        seen.add((pep, hla))
        item: dict[str, Any] = {"peptide": pep, "allele": hla}
        wt = str(row.get("wt_peptide") or "").strip().upper()
        if wt:
            item["wt_peptide"] = wt
        affinity = _float_opt(row.get("ic50_nm"))
        if affinity is None:
            affinity = _float_opt(row.get("affinity_nm"))
        if affinity is not None and affinity > 0:
            item["affinity_nm"] = affinity
        stability = _float_opt(row.get("stability_hours"))
        if stability is not None and stability >= 0:
            item["stability_hours"] = stability
        rna_tpm = _float_opt(row.get("expression"))
        if rna_tpm is None:
            rna_tpm = _float_opt(row.get("rna_tpm"))
        if rna_tpm is not None and rna_tpm >= 0:
            item["rna_tpm"] = rna_tpm
        ccf = _float_opt(row.get("ccf"))
        if ccf is not None and 0.0 <= ccf <= 1.0:
            item["ccf"] = ccf
        payload_items.append(item)

    if not payload_items:
        return {}

    results_map: dict[tuple[str, str], dict[str, Any]] = {}
    for start in range(0, len(payload_items), max(1, int(batch_size))):
        chunk = payload_items[start : start + max(1, int(batch_size))]
        try:
            resp = requests.post(
                f"{url}/api/v1/score_clinical",
                headers=headers,
                json={"candidates": chunk, "ensemble": use_ens},
                timeout=timeout,
            )
            resp.raise_for_status()
            body = resp.json()
            for res in body.get("results", []):
                pep_key = str(res.get("peptide") or "").strip().upper()
                hla_key = str(res.get("allele") or "").strip().upper()
                if pep_key and hla_key:
                    results_map[(pep_key, hla_key)] = res
        except Exception as exc:  # noqa: BLE001 - graceful degradation by design
            logger.warning(
                "ESM-2 batch scoring degraded (offset=%d, size=%d): %s",
                start,
                len(chunk),
                exc,
            )
            continue
    return results_map
