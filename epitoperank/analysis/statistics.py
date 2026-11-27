"""Statistical primitives for alternative-splicing analysis.

The chi-square test and Benjamini-Hochberg adjustment are ported from the
SplicingNexus v2 production implementation (``stage1_docker_adapter``).

``psi_group_test`` 补的是另一件事：2×2 卡方只看 junction 计数，把组内变异抹平了，
所以 n=3 的重复样本即使 PSI 差异很不稳定也可能算「显著」。组间检验直接对重复样本的
PSI 做 Welch t 检验与 Mann-Whitney U，用来回答「这个 ΔPSI 在样本间站不站得住」。
它和 rMATS 自带的 FDR 是互补关系，不是替代——rMATS 用计数层面的 beta-binomial 模型，
这里看的是样本层面的离散度。
"""

from __future__ import annotations

import math
import warnings
from typing import Any, Iterable, Sequence

from epitoperank.splicing.schema import StandardEvent


# 中文备注：统计分析：辅助处理chisquarep值（参数：control_in、control_out、experiment_in、experiment_out）
def chi_square_p_value(
    control_in: float,
    control_out: float,
    experiment_in: float,
    experiment_out: float,
) -> float | None:
    """Two-by-two chi-square test p-value on junction counts.

    Equivalent to rMATS' JC-based test. Returns ``None`` when any marginal
    is zero (undefined test).
    """
    cells = (control_in, control_out, experiment_in, experiment_out)
    total = sum(cells)
    row_control = control_in + control_out
    row_experiment = experiment_in + experiment_out
    column_in = control_in + experiment_in
    column_out = control_out + experiment_out
    if min(total, row_control, row_experiment, column_in, column_out) <= 0:
        return None
    expected = (
        row_control * column_in / total,
        row_control * column_out / total,
        row_experiment * column_in / total,
        row_experiment * column_out / total,
    )
    if any(value <= 0 for value in expected):
        return None
    statistic = sum((observed - target) ** 2 / target for observed, target in zip(cells, expected))
    # Chi-square with 1 degree of freedom: p = erfc(sqrt(statistic / 2)).
    return math.erfc(math.sqrt(max(0.0, statistic) / 2.0))


# 中文备注：统计分析：辅助处理benjaminihochberg（参数：p_values）
def benjamini_hochberg(p_values: Sequence[float | None]) -> list[float | None]:
    """Benjamini-Hochberg FDR adjustment, preserving ``None`` entries."""
    indexed = [
        (index, float(value))
        for index, value in enumerate(p_values)
        if value is not None
    ]
    indexed.sort(key=lambda item: item[1])
    adjusted: dict[int, float] = {}
    running = 1.0
    total = len(indexed)
    for rank_index in range(total - 1, -1, -1):
        row_index, p_value = indexed[rank_index]
        running = min(running, p_value * total / (rank_index + 1))
        adjusted[row_index] = min(1.0, running)
    return [adjusted.get(index) for index in range(len(p_values))]


# 中文备注：统计分析：辅助处理recomputeFDR（参数：events）
def recompute_fdr(events: Sequence[StandardEvent]) -> None:
    """Recompute FDR from p-values in place (BH adjustment)."""
    adjusted = benjamini_hochberg([event.p_value for event in events])
    for event, fdr in zip(events, adjusted):
        if event.fdr is None and fdr is not None:
            event.fdr = round(fdr, 12)


# 中文备注：统计分析：辅助处理effect条数摘要（参数：events）
def effect_size_summary(events: Sequence[StandardEvent]) -> dict[str, Any]:
    """Summarize delta-PSI distribution of an event collection."""
    deltas = [event.delta_psi for event in events if event.delta_psi is not None]
    if not deltas:
        return {"count": 0, "mean_abs_delta_psi": None, "max_abs_delta_psi": None}
    absolute = [abs(value) for value in deltas]
    return {
        "count": len(deltas),
        "mean_abs_delta_psi": round(sum(absolute) / len(absolute), 6),
        "max_abs_delta_psi": round(max(absolute), 6),
    }


# ---------------------------------------------------------------------------
# 组间检验：直接用重复样本的 PSI，而不是把组内变异抹平
# ---------------------------------------------------------------------------
_SCIPY_STATS: Any = None


# 中文备注：统计分析：惰性加载scipy（参数：无）
def _scipy_stats() -> Any:
    """惰性导入 scipy.stats：只在真正做检验时才付出导入成本。"""
    global _SCIPY_STATS
    if _SCIPY_STATS is None:
        from scipy import stats as scipy_stats

        _SCIPY_STATS = scipy_stats
    return _SCIPY_STATS


# 中文备注：统计分析：清洗PSI序列（参数：values）
def _psi_values(values: Iterable[Any]) -> list[float]:
    """把 PSI 序列转成 float，丢掉 None、NaN 与不可转换的值。"""
    out: list[float] = []
    for value in values:
        try:
            number = float(value)
        except (TypeError, ValueError):
            continue
        if math.isnan(number):
            continue
        out.append(number)
    return out


# 中文备注：统计分析：mannwhitney最小可达p（参数：n_control、n_experiment）
def minimum_mann_whitney_p(n_control: int, n_experiment: int) -> float:
    """Mann-Whitney U 双侧精确检验在完全分离时能达到的最小 p 值。

    3 vs 3 为 0.1、2 vs 2 为 0.333：小样本用非参数检验**不可能**达到 0.05。
    这个下界必须显式给出，否则会把「样本不足」误读成「没有差异」。
    样本量超过 12 时改用渐近法，此时下界按 0 处理。
    """
    total = n_control + n_experiment
    if total > 12 or n_control < 1 or n_experiment < 1:
        return 0.0
    return min(1.0, 2.0 / math.comb(total, n_control))


# 中文备注：统计分析：welch t检验（参数：control、experiment）
def welch_t_test(control: Iterable[Any], experiment: Iterable[Any]) -> dict[str, Any] | None:
    """Welch t 检验（不假设两组方差齐性）。任一组重复数 < 2 时返回 None。"""
    left, right = _psi_values(control), _psi_values(experiment)
    if len(left) < 2 or len(right) < 2:
        return None
    with warnings.catch_warnings():
        # 两组都零方差时 scipy 会告警并在下面返回 NaN，这里自己处理，不必刷日志
        warnings.simplefilter("ignore", RuntimeWarning)
        result = _scipy_stats().ttest_ind(left, right, equal_var=False)
    statistic = float(result.statistic)
    p_value = float(result.pvalue)
    if math.isnan(p_value):
        # 两组都零方差时 scipy 返回 NaN：均值相同即无差异，不同即完全分离
        same_mean = math.isclose(sum(left) / len(left), sum(right) / len(right))
        p_value = 1.0 if same_mean else 0.0
        statistic = 0.0 if same_mean else float("nan")
    return {
        "test": "welch_t",
        "statistic": statistic if math.isfinite(statistic) else None,
        "p_value": p_value,
        "n_control": len(left),
        "n_experiment": len(right),
    }


# 中文备注：统计分析：mannwhitney检验（参数：control、experiment、exact_limit）
def mann_whitney_u(
    control: Iterable[Any], experiment: Iterable[Any], *, exact_limit: int = 12
) -> dict[str, Any] | None:
    """Mann-Whitney U 双侧检验；小样本用精确法，大样本用渐近法（含结校正）。"""
    left, right = _psi_values(control), _psi_values(experiment)
    if len(left) < 1 or len(right) < 1 or len(left) + len(right) < 3:
        return None
    stats = _scipy_stats()
    method = "exact" if len(left) + len(right) <= exact_limit else "asymptotic"
    try:
        result = stats.mannwhitneyu(left, right, alternative="two-sided", method=method)
    except ValueError:
        # 结过多时精确法可能不可用，退回渐近法
        method = "asymptotic"
        result = stats.mannwhitneyu(left, right, alternative="two-sided", method=method)
    return {
        "test": "mann_whitney_u",
        "method": method,
        "statistic": float(result.statistic),
        "p_value": float(result.pvalue),
        "n_control": len(left),
        "n_experiment": len(right),
        "minimum_attainable_p": minimum_mann_whitney_p(len(left), len(right)),
    }


# 中文备注：统计分析：PSI组间检验（参数：control、experiment）
def psi_group_test(
    control: Iterable[Any], experiment: Iterable[Any]
) -> dict[str, Any] | None:
    """对两组重复样本的 PSI 同时做参数与非参数检验。

    返回两组各自的均值、ΔPSI、Welch p 与 Mann-Whitney p，外加一条 ``note``
    说明该用哪个结果——不能只给一个 p 值，因为 n=3 时两者给出的结论差异很大：
    Welch 能到 0.01 量级，精确 Mann-Whitney 的下界却是 0.1。
    """
    left, right = _psi_values(control), _psi_values(experiment)
    welch = welch_t_test(left, right)
    mann = mann_whitney_u(left, right)
    if welch is None and mann is None:
        return None
    result: dict[str, Any] = {
        "n_control": len(left),
        "n_experiment": len(right),
        "mean_control": round(sum(left) / len(left), 6) if left else None,
        "mean_experiment": round(sum(right) / len(right), 6) if right else None,
        "delta_psi": (
            round(sum(right) / len(right) - sum(left) / len(left), 6)
            if left and right else None
        ),
        "welch_t": welch,
        "mann_whitney_u": mann,
    }
    notes = []
    if welch is None:
        notes.append("至少一组重复数不足 2，未做 Welch t 检验")
    if mann is not None:
        floor = mann["minimum_attainable_p"]
        if floor >= 0.05:
            notes.append(
                f"样本量 {len(left)} vs {len(right)} 太小：精确 Mann-Whitney 的"
                f"最小可能 p 为 {floor:g}，达不到 0.05，非显著不代表无差异"
            )
    result["note"] = "；".join(notes)
    return result


# 中文备注：统计分析：按样本分组取PSI（参数：event、control_ids、experiment_ids）
def event_psi_groups(
    event: StandardEvent, control_ids: Sequence[str], experiment_ids: Sequence[str]
) -> tuple[list[float], list[float]] | None:
    """按给定的样本分组从事件里取出两组 PSI；任一组为空时返回 None。"""
    psi = getattr(event, "psi_by_sample", None) or {}
    control = _psi_values(psi.get(sample) for sample in control_ids)
    experiment = _psi_values(psi.get(sample) for sample in experiment_ids)
    if not control or not experiment:
        return None
    return control, experiment


# 中文备注：统计分析：事件级PSI检验（参数：event、control_ids、experiment_ids）
def psi_group_test_for_event(
    event: StandardEvent, control_ids: Sequence[str], experiment_ids: Sequence[str]
) -> dict[str, Any] | None:
    """对单个事件做组间 PSI 检验；没有重复样本数据时返回 None。"""
    groups = event_psi_groups(event, control_ids, experiment_ids)
    if groups is None:
        return None
    return psi_group_test(*groups)


# 中文备注：统计分析：显著事件的重复样本支持度（参数：events、control_ids、experiment_ids）
def psi_group_test_summary(
    events: Sequence[StandardEvent],
    control_ids: Sequence[str],
    experiment_ids: Sequence[str],
    *,
    alpha: float = 0.05,
    fdr_max: float = 0.05,
    max_events: int = 2000,
) -> dict[str, Any]:
    """统计「rMATS 判显著的事件里,有多少在重复样本层面也站得住」。

    这是一个质控口径,不是新的显著性检验:``unsupported`` 列出 rMATS 认为显著、
    但组间 PSI 检验未达 ``alpha`` 的事件,通常意味着 ΔPSI 在重复样本间不稳定。
    ``max_events`` 用来限制逐事件检验的开销,超出部分记为 ``truncated``。
    """
    tested = 0
    mats_significant = 0
    psi_supported = 0
    unsupported: list[dict[str, Any]] = []
    skipped = 0
    capped = 0
    for index, event in enumerate(events):
        if index >= max_events:
            capped = len(events) - index
            break
        test = psi_group_test_for_event(event, control_ids, experiment_ids)
        if test is None:
            skipped += 1
            continue
        tested += 1
        is_mats_significant = event.fdr is not None and event.fdr <= fdr_max
        if is_mats_significant:
            mats_significant += 1
        p_values = [
            item["p_value"] for item in (test.get("welch_t"), test.get("mann_whitney_u"))
            if item is not None and item.get("p_value") is not None
        ]
        supported = any(value <= alpha for value in p_values)
        if supported:
            psi_supported += 1
        elif is_mats_significant:
            unsupported.append({
                "event_id": event.event_id,
                "gene_symbol": event.gene_symbol,
                "fdr": event.fdr,
                "delta_psi": event.delta_psi,
                "psi_p_value": min(p_values) if p_values else None,
            })
    unsupported.sort(key=lambda row: abs(row.get("delta_psi") or 0), reverse=True)
    return {
        "tested": tested,
        "skipped_no_replicates": skipped,
        "mats_significant": mats_significant,
        "psi_supported": psi_supported,
        "unsupported": unsupported,
        "truncated": capped,
        "alpha": alpha,
        "fdr_max": fdr_max,
        "note": (
            "psi_supported 统计的是组间 PSI 检验达到 alpha 的事件数；"
            "unsupported 是 rMATS 判显著但重复样本层面不稳的事件，供人工复核。"
        ),
    }
