"""连接肽的 MHC 类别与长度支持。

早先 ``junction_peptides`` 硬限 8–11，CD4 候选只能拿 MHC-I 选出的 9mer 再向外
截一个固定窗口，等于把 I 类的 anchor 假设带进了 II 类。这里锁住新的口径：
8–11 属 I 类、12–25 属 II 类，且每条候选都带上自己的 ``mhc_class``。
"""
from __future__ import annotations

import pytest

from epitoperank.neoantigen import (
    MHC_I_LENGTHS, MHC_II_LENGTHS, junction_peptides, mhc_class_for_length,
)
from epitoperank.peptide.pipeline import PeptideOptions

# 改变后蛋白：M + 10A + 10W + 10K；参考蛋白：M + 10A + 10K（相当于跳掉 W 段）
ALTERED = "ATG" + "GCT" * 10 + "TGG" * 10 + "AAG" * 10
REFERENCE = "ATG" + "GCT" * 10 + "AAG" * 10
JUNCTION_NT = 33  # 3 + 30：第 10 与第 11 个残基之间


# ---------------------------------------------------------------------------
# 长度 -> 类别
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(("length", "expected"), [
    (8, 1), (9, 1), (10, 1), (11, 1),
    (12, 2), (15, 2), (25, 2),
])
def test_mhc_class_boundaries(length: int, expected: str) -> None:
    assert mhc_class_for_length(length) == expected


@pytest.mark.parametrize("length", [7, 26, 0, 40])
def test_mhc_class_rejects_lengths_outside_both_ranges(length: int) -> None:
    with pytest.raises(ValueError, match="8|12"):
        mhc_class_for_length(length)


# ---------------------------------------------------------------------------
# 默认行为不变
# ---------------------------------------------------------------------------
def test_default_is_still_mhc_i() -> None:
    peptides = junction_peptides(REFERENCE, ALTERED, JUNCTION_NT)
    assert peptides, "默认应至少产出一条 8-11mer"
    assert {item["length"] for item in peptides} == {8, 9, 10, 11}
    assert {item["mhc_class"] for item in peptides} == {1}


def test_default_lengths_constant_matches_previous_behaviour() -> None:
    assert MHC_I_LENGTHS == (8, 9, 10, 11)


# ---------------------------------------------------------------------------
# CD4 长度
# ---------------------------------------------------------------------------
def test_mhc_class_ii_generates_longer_junction_peptides() -> None:
    peptides = junction_peptides(REFERENCE, ALTERED, JUNCTION_NT, mhc_class="II")
    assert MHC_II_LENGTHS == (15,)
    assert peptides, "II 类应产出连接肽"
    assert {item["length"] for item in peptides} == {15}
    assert {item["mhc_class"] for item in peptides} == {2}


def test_cd4_peptide_really_spans_the_junction() -> None:
    """15mer 必须真的横跨连接点，而不是从某一侧单独截出来的。"""
    proteins = "M" + "A" * 10 + "W" * 10 + "K" * 10
    right_aa = JUNCTION_NT // 3
    for item in junction_peptides(REFERENCE, ALTERED, JUNCTION_NT, mhc_class="II"):
        start = item["start_aa"] - 1
        window = proteins[start:start + item["length"]]
        assert window == item["peptide"]
        assert start < right_aa < start + item["length"], "肽段必须包含连接点两侧的残基"
        assert "W" in item["peptide"], "改变后特有的 W 段应在肽段中出现"


def test_mixed_lengths_label_each_peptide_class() -> None:
    peptides = junction_peptides(
        REFERENCE, ALTERED, JUNCTION_NT, lengths=(8, 9, 10, 11, 15),
    )
    by_class = {}
    for item in peptides:
        by_class.setdefault(item["mhc_class"], set()).add(item["length"])
        expected = 1 if item["length"] <= 11 else 2
        assert item["mhc_class"] == expected
    assert by_class[1] == {8, 9, 10, 11}
    assert by_class[2] == {15}


@pytest.mark.parametrize("lengths", [(7,), (26,), (8, 30)])
def test_out_of_range_lengths_still_raise(lengths: tuple[int, ...]) -> None:
    with pytest.raises(ValueError):
        junction_peptides(REFERENCE, ALTERED, JUNCTION_NT, lengths=lengths)


# ---------------------------------------------------------------------------
# 肽选项校验：CLI 与 API 共用这条路径
# ---------------------------------------------------------------------------
def test_peptide_options_accept_cd4_lengths() -> None:
    PeptideOptions(alleles=["HLA-A*02:01"], mhc_class="both",
                   lengths=(8, 9, 10, 11, 15)).validate()


@pytest.mark.parametrize("lengths", [(30,), (7,), ()])
def test_peptide_options_reject_invalid_lengths(lengths: tuple[int, ...]) -> None:
    with pytest.raises(ValueError, match="lengths"):
        PeptideOptions(alleles=["HLA-A*02:01"], lengths=lengths).validate()
