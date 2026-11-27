"""组间 PSI 检验测试。

重点不是复算 scipy 的数字，而是锁住三个容易出错的口径：
1. 组内变异必须真的进入检验（同样的 ΔPSI，样本发散时不能算显著）；
2. 小样本非参数检验存在不可达的 p 值下界，必须显式告知；
3. 汇总口径要能把「rMATS 显著但重复样本不稳」的事件挑出来。
"""
from __future__ import annotations

import math
from types import SimpleNamespace

import pytest

from epitoperank.analysis.statistics import (
    event_psi_groups,
    mann_whitney_u,
    minimum_mann_whitney_p,
    psi_group_test,
    psi_group_test_for_event,
    psi_group_test_summary,
    welch_t_test,
)
from epitoperank.splicing.schema import StandardEvent


def _event(event_id: str, psi: dict[str, float], *, fdr: float | None = 0.01,
           delta_psi: float | None = None) -> StandardEvent:
    return StandardEvent(
        event_id=event_id, gene_id="ENSG_T", gene_symbol="GENE",
        event_type="SE", chromosome="1", strand="+", genomic_coordinates="1-2",
        coordinate_system="1-based", source_tool="rmats",
        mean_psi_group1=None, mean_psi_group2=None,
        delta_psi=delta_psi, p_value=None, fdr=fdr, psi_by_sample=psi,
    )


# ---------------------------------------------------------------------------
# 基本检验
# ---------------------------------------------------------------------------
def test_welch_detects_clean_separation() -> None:
    result = welch_t_test([0.90, 0.92, 0.88], [0.10, 0.12, 0.08])
    assert result is not None
    assert result["p_value"] < 0.001
    assert result["n_control"] == 3 and result["n_experiment"] == 3


def test_welch_needs_two_replicates_per_group() -> None:
    assert welch_t_test([0.9], [0.1, 0.2]) is None


def test_welch_survives_zero_variance_groups() -> None:
    """两组都零方差时 scipy 返回 NaN，不能把 NaN 当成 p 值传下去。"""
    same = welch_t_test([0.5, 0.5, 0.5], [0.5, 0.5, 0.5])
    assert same is not None and same["p_value"] == 1.0
    different = welch_t_test([0.5, 0.5, 0.5], [0.9, 0.9, 0.9])
    assert different is not None and different["p_value"] == 0.0
    assert different["statistic"] is None, "无穷大的统计量不能写进 JSON"


def test_mann_whitney_uses_exact_for_small_samples() -> None:
    result = mann_whitney_u([0.9, 0.92, 0.88], [0.1, 0.12, 0.08])
    assert result is not None
    assert result["method"] == "exact"
    # 3 vs 3 完全分离时精确双侧 p 恰为 0.1
    assert result["p_value"] == pytest.approx(0.1)


def test_mann_whitney_switches_to_asymptotic_for_large_samples() -> None:
    result = mann_whitney_u(list(range(10)), list(range(20, 32)))
    assert result is not None and result["method"] == "asymptotic"


@pytest.mark.parametrize(("n1", "n2", "floor"), [
    (2, 2, 1 / 3),
    (3, 3, 0.1),
    (4, 4, 2 / 70),
    (3, 4, 2 / 35),
])
def test_minimum_attainable_p_matches_exact_enumeration(n1: int, n2: int, floor: float) -> None:
    assert minimum_mann_whitney_p(n1, n2) == pytest.approx(floor)


def test_minimum_attainable_p_is_zero_for_large_samples() -> None:
    assert minimum_mann_whitney_p(10, 10) == 0.0


# ---------------------------------------------------------------------------
# 组内变异必须真的影响结论
# ---------------------------------------------------------------------------
def test_welch_accounts_for_within_group_variance() -> None:
    """ΔPSI 相同、只有组内离散度不同时，p 值必须明显不同。

    这正是 2×2 卡方做不到的事：它只看到计数聚合后的 ΔPSI，看不到重复样本的离散度。
    """
    tight = psi_group_test([0.80, 0.81, 0.79], [0.20, 0.21, 0.19])
    noisy = psi_group_test([1.00, 0.80, 0.60], [0.40, 0.20, 0.00])
    assert tight is not None and noisy is not None
    # 两组均值完全相同，ΔPSI 一致
    assert tight["delta_psi"] == pytest.approx(noisy["delta_psi"], abs=1e-9)
    assert tight["welch_t"]["p_value"] < 0.001
    assert noisy["welch_t"]["p_value"] > tight["welch_t"]["p_value"] * 50


def test_welch_not_significant_when_groups_overlap() -> None:
    """真正重叠的两组不应被判为显著。"""
    overlapped = psi_group_test([0.80, 0.20, 0.50], [0.70, 0.30, 0.60])
    assert overlapped is not None
    assert overlapped["welch_t"]["p_value"] > 0.05


def test_psi_group_test_reports_the_floor_for_small_samples() -> None:
    result = psi_group_test([0.9, 0.92, 0.88], [0.1, 0.12, 0.08])
    assert result is not None
    assert result["mann_whitney_u"]["minimum_attainable_p"] == pytest.approx(0.1)
    assert "达不到 0.05" in result["note"]


def test_psi_group_test_without_replicates_returns_none() -> None:
    assert psi_group_test([0.9], [0.1]) is None


def test_psi_group_test_ignores_missing_values() -> None:
    result = psi_group_test([0.9, None, 0.88, float("nan")], [0.1, 0.12])
    assert result is not None
    assert result["n_control"] == 2 and result["n_experiment"] == 2


# ---------------------------------------------------------------------------
# 事件级与汇总
# ---------------------------------------------------------------------------
def test_event_psi_groups_uses_sample_lists() -> None:
    event = _event("SE:1", {"c1": 0.9, "c2": 0.88, "e1": 0.1, "e2": 0.12})
    groups = event_psi_groups(event, ["c1", "c2"], ["e1", "e2"])
    assert groups == ([0.9, 0.88], [0.1, 0.12])


def test_event_psi_groups_returns_none_when_a_group_is_empty() -> None:
    event = _event("SE:1", {"c1": 0.9})
    assert event_psi_groups(event, ["c1"], ["e1"]) is None


def test_psi_group_test_summary_flags_unstable_significant_events() -> None:
    stable = _event("SE:1", {"c1": 0.92, "c2": 0.90, "c3": 0.91,
                             "e1": 0.10, "e2": 0.11, "e3": 0.09}, delta_psi=-0.81)
    unstable = _event("SE:2", {"c1": 0.95, "c2": 0.55, "c3": 0.75,
                               "e1": 0.55, "e2": 0.20, "e3": 0.50}, delta_psi=-0.33)
    no_replicates = _event("SE:3", {"c1": 0.9, "e1": 0.1}, delta_psi=-0.8)

    summary = psi_group_test_summary(
        [stable, unstable, no_replicates],
        ["c1", "c2", "c3"], ["e1", "e2", "e3"],
    )
    assert summary["tested"] == 2, "单重复事件两组各 1 个样本，无法做组间检验"
    assert summary["skipped_no_replicates"] == 1
    flagged = {row["event_id"] for row in summary["unsupported"]}
    assert "SE:2" in flagged
    assert "SE:1" not in flagged
    assert "SE:3" not in flagged, "没做过检验的事件不能出现在「不稳」名单里"


def test_psi_group_test_summary_counts_skipped_without_psi() -> None:
    empty = _event("SE:9", {}, delta_psi=-0.8)
    summary = psi_group_test_summary([empty], ["c1", "c2"], ["e1", "e2"])
    assert summary["tested"] == 0
    assert summary["skipped_no_replicates"] == 1
    assert summary["unsupported"] == []


def test_result_is_json_serialisable() -> None:
    """结果会进 API 与 agent_state.json，不能带 inf / NaN。"""
    import json

    result = psi_group_test([0.9, 0.92, 0.88], [0.1, 0.12, 0.08])
    payload = json.dumps(result, allow_nan=False)
    assert "Infinity" not in payload and "NaN" not in payload


def test_chi_square_still_available_for_count_based_check() -> None:
    """原有的 2×2 卡方保留，作为计数层面的交叉验证。"""
    from epitoperank.analysis.statistics import chi_square_p_value

    p_value = chi_square_p_value(10, 1, 1, 10)
    assert p_value is not None and p_value < 0.01
    assert not math.isnan(p_value)


# ---------------------------------------------------------------------------
# 接入分析流程：没有重复样本时必须明确「没做」，而不是给出一个通过的结果
# ---------------------------------------------------------------------------
def _dataset(samples: list[tuple[str, str]]) -> SimpleNamespace:
    from epitoperank.splicing.schema import SampleMetadata

    meta = [SampleMetadata(sample_id=sid, group=group) for sid, group in samples]
    groups: dict[str, list[str]] = {}
    for item in meta:
        groups.setdefault(item.group, []).append(item.sample_id)
    labels = sorted(groups)
    return SimpleNamespace(
        groups=groups,
        group_labels=(labels[0], labels[-1]) if len(labels) >= 2 else None,
    )


def test_replicate_support_is_skipped_for_single_sample_groups() -> None:
    from epitoperank.splicing.filtering import FilterSettings
    from epitoperank.tools.analysis_tools import _replicate_support

    context = SimpleNamespace(
        dataset=_dataset([("c1", "ctrl"), ("e1", "treat")]),
        significant_events=[_event("SE:1", {"c1": 0.9, "e1": 0.1})],
    )
    assert _replicate_support(context, FilterSettings()) is None, (
        "两组各一个样本时无从估计组内方差，不能报成复核通过"
    )


def test_replicate_support_runs_with_replicates() -> None:
    from epitoperank.splicing.filtering import FilterSettings
    from epitoperank.tools.analysis_tools import _replicate_support

    samples = [("c1", "ctrl"), ("c2", "ctrl"), ("e1", "treat"), ("e2", "treat")]
    context = SimpleNamespace(
        dataset=_dataset(samples),
        significant_events=[
            _event("SE:1", {"c1": 0.92, "c2": 0.90, "e1": 0.10, "e2": 0.11}),
        ],
    )
    support = _replicate_support(context, FilterSettings())
    assert support is not None
    assert support["tested"] == 1
    assert support["psi_supported"] == 1
    assert support["groups"] == {"control": "ctrl", "experiment": "treat"}


def test_replicate_support_returns_none_without_two_groups() -> None:
    from epitoperank.splicing.filtering import FilterSettings
    from epitoperank.tools.analysis_tools import _replicate_support

    context = SimpleNamespace(
        dataset=_dataset([("c1", "ctrl"), ("c2", "ctrl")]),
        significant_events=[_event("SE:1", {"c1": 0.9, "c2": 0.88})],
    )
    assert _replicate_support(context, FilterSettings()) is None
