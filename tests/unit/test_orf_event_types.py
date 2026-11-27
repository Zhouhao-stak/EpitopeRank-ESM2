"""A3SS / A5SS / MXE 的 CDS 重建测试。

全部使用合成基因组：不再依赖网络或真实基因组，且可以精确断言
「异常 CDS 应当等于哪条序列」，而不是只检查是否产出。

合成基因组的构造方式是「先定义转录本方向的序列块，再按链方向落到基因组」，
因此正链与负链用的是同一套生物学预期，可以直接对比。
"""
from __future__ import annotations

import csv
from pathlib import Path

from epitoperank.neoantigen import junction_peptides
from epitoperank.splicing.orf_builder import (
    ReferenceProvider, _build_one, _revcomp, build_orf_table,
)

# 5' 端侧翼：ATG + 19 个 GCT → M + 19A（60 nt，前 20 个密码子）
FLANK5 = "ATG" + "GCT" * 19
# 3' 端侧翼：20 个 AAG → 20K（60 nt）
FLANK3 = "AAG" * 20
# 可变的中间外显子：10 个互不相同的密码子，删除任一段都会改变连接处氨基酸
EXON_A_CODONS = ["TGG", "GAA", "TTC", "CAG", "CAT", "AAG", "CTG", "GAT", "CCG", "TAC"]
# 另一个互斥外显子，起始残基与 EXON_A 不同，保证连接肽在参考蛋白里查不到
EXON_B_CODONS = ["CGT", "GAC", "TTA", "AGC", "GGT", "CCA", "ATG", "TCT", "GCC", "ATT"]
EXON_A = "".join(EXON_A_CODONS)
EXON_B = "".join(EXON_B_CODONS)
INTRON = "C" * 10


def _genome(*blocks: str) -> str:
    """按顺序拼接基因组块（1-based 坐标即块边界）。"""
    return "".join(blocks)


class SyntheticProvider(ReferenceProvider):
    """单转录本的合成参考源；区段按转录本顺序给出。"""

    def __init__(self, genome: str, segments: list[tuple[int, int]], strand: int = 1) -> None:
        self.genome = genome
        self.segments = segments
        self.strand = strand

    def transcripts(self, chrom, start, end, strand, gene_id):
        return [{
            "id": "TX1",
            "start": min(s for s, _ in self.segments),
            "end": max(e for _, e in self.segments),
            "strand": strand, "gene_id": gene_id, "chrom": chrom, "coding": True,
        }]

    def cds_segments(self, transcript):
        return [{"start": s, "end": e, "phase": 0, "strand": self.strand}
                for s, e in self.segments]

    def sequence(self, chrom, start, end):
        return self.genome[start - 1:end]

    def assembly(self):
        return "synthetic-v1"


# ---------------------------------------------------------------------------
# 正链：5'侧翼(1..60) + 内含子 + 可变外显子(71..100) + 内含子 + 3'侧翼(111..170)
# ---------------------------------------------------------------------------
SHIFT_PLUS = _genome(FLANK5, INTRON, EXON_A, INTRON, FLANK3)
SHIFT_PLUS_SEGMENTS = [(1, 60), (71, 100), (111, 170)]

# 负链：把同样的转录本块反向互补落到基因组上，转录顺序为 111..170 → 71..100 → 1..60
SHIFT_MINUS = _genome(_revcomp(FLANK3), INTRON, _revcomp(EXON_A), INTRON, _revcomp(FLANK5))
SHIFT_MINUS_SEGMENTS = [(111, 170), (71, 100), (1, 60)]

LONG_CDS = FLANK5 + EXON_A + FLANK3


def _row(**fields: str) -> dict[str, str]:
    """把事件坐标写成 _build_one 期望的小写 rMATS 行。"""
    return {key.lower(): str(value) for key, value in fields.items()}


def _event(event_type: str, row: dict[str, str], strand: str) -> dict:
    return {
        "event_id": f"{event_type}:1", "event_type": event_type,
        "gene_id": "ENSG_SYN", "gene_symbol": "SYNGENE", "chrom": "1",
        "strand": strand, "fdr": 0.001, "delta_psi": 0.8, "row": row, "support": 10.0,
    }


def _a3ss_row(long_start: int, long_end: int, short_start: int, short_end: int) -> dict[str, str]:
    """A3SS/A5SS 行；短型用的是 rMATS 的 shortES / shortEE 两列。"""
    return _row(LongExonStart_0base=long_start - 1, LongExonEnd=long_end,
                ShortES=short_start - 1, ShortEE=short_end)


# ---------------------------------------------------------------------------
# A3SS：外显子 5' 边界在两个位点之间移动
# ---------------------------------------------------------------------------
def test_a3ss_long_form_deletes_the_shifted_region() -> None:
    """转录本含长型时，异常 CDS 应删掉只属于长型的那 6 nt。"""
    provider = SyntheticProvider(SHIFT_PLUS, SHIFT_PLUS_SEGMENTS)
    event = _event("A3SS", _a3ss_row(71, 100, 77, 100), "+")
    result = _build_one(event, provider)
    assert "reason" not in result, result
    assert result["reference_cds"] == LONG_CDS
    assert result["altered_cds"] == FLANK5 + EXON_A[6:] + FLANK3
    assert result["frame_status"] == "exon_shortened"
    assert result["junction_nt"] == 60
    # 连接点两侧确实能产出参考 cDNA 里没有的肽
    assert junction_peptides(result["reference_cds"], result["altered_cds"], 60)


def test_a3ss_short_form_inserts_the_shifted_region() -> None:
    """转录本含短型时，异常 CDS 应把长型多出的 6 nt 插回去。"""
    provider = SyntheticProvider(SHIFT_PLUS, [(1, 60), (77, 100), (111, 170)])
    event = _event("A3SS", _a3ss_row(71, 100, 77, 100), "+")
    result = _build_one(event, provider)
    assert "reason" not in result, result
    # 补回后应与长型 CDS 完全一致
    assert result["altered_cds"] == LONG_CDS
    assert result["frame_status"] == "exon_lengthened"


def test_a3ss_negative_strand_matches_forward_expectation() -> None:
    """负链上同一操作应得到同样的 mRNA 结果（方向只在坐标层翻转）。"""
    provider = SyntheticProvider(SHIFT_MINUS, SHIFT_MINUS_SEGMENTS, strand=-1)
    event = _event("A3SS", _a3ss_row(71, 100, 71, 94), "-")
    result = _build_one(event, provider)
    assert "reason" not in result, result
    assert result["reference_cds"] == LONG_CDS
    assert result["altered_cds"] == FLANK5 + EXON_A[6:] + FLANK3


# ---------------------------------------------------------------------------
# A5SS：外显子 3' 边界移动（差异段落在另一侧）
# ---------------------------------------------------------------------------
def test_a5ss_long_form_deletes_the_shifted_region_at_exon_end() -> None:
    provider = SyntheticProvider(SHIFT_PLUS, SHIFT_PLUS_SEGMENTS)
    event = _event("A5SS", _a3ss_row(71, 100, 71, 94), "+")
    result = _build_one(event, provider)
    assert "reason" not in result, result
    assert result["altered_cds"] == FLANK5 + EXON_A[:24] + FLANK3
    assert result["junction_nt"] == 84
    assert junction_peptides(result["reference_cds"], result["altered_cds"], 84)


def test_a5ss_short_form_inserts_the_shifted_region_at_exon_end() -> None:
    provider = SyntheticProvider(SHIFT_PLUS, [(1, 60), (71, 94), (111, 170)])
    event = _event("A5SS", _a3ss_row(71, 100, 71, 94), "+")
    result = _build_one(event, provider)
    assert "reason" not in result, result
    assert result["altered_cds"] == LONG_CDS


def test_shift_landing_in_utr_is_skipped() -> None:
    """位点移动若不在 CDS 内（转录本的外显子边界对不上任何一个位点），应跳过。"""
    provider = SyntheticProvider(SHIFT_PLUS, [(1, 60), (75, 100), (111, 170)])
    event = _event("A3SS", _a3ss_row(71, 100, 77, 100), "+")
    result = _build_one(event, provider)
    assert result.get("reason") == "no_reconstructable_orf"


# ---------------------------------------------------------------------------
# MXE：两个互斥外显子互换
# ---------------------------------------------------------------------------
MXE_PLUS = _genome(FLANK5, INTRON, EXON_A, INTRON, EXON_B, INTRON, FLANK3)
MXE_MINUS = _genome(_revcomp(FLANK3), INTRON, _revcomp(EXON_B), INTRON,
                    _revcomp(EXON_A), INTRON, _revcomp(FLANK5))


def _mxe_row(first: tuple[int, int], second: tuple[int, int]) -> dict[str, str]:
    """MXE 的列名以数字开头，无法写成关键字参数，这里直接建字典。"""
    return {
        "1stexonstart_0base": str(first[0] - 1), "1stexonend": str(first[1]),
        "2ndexonstart_0base": str(second[0] - 1), "2ndexonend": str(second[1]),
    }


def test_mxe_swaps_in_the_other_exclusive_exon() -> None:
    provider = SyntheticProvider(MXE_PLUS, [(1, 60), (71, 100), (151, 210)])
    event = _event("MXE", _mxe_row((71, 100), (111, 140)), "+")
    result = _build_one(event, provider)
    assert "reason" not in result, result
    assert result["reference_cds"] == FLANK5 + EXON_A + FLANK3
    assert result["altered_cds"] == FLANK5 + EXON_B + FLANK3
    # 左右两个连接点都应能取到，实际使用的是第一个能产出新肽的
    assert result["junction_nt"] in (60, 90)
    assert junction_peptides(result["reference_cds"], result["altered_cds"],
                             result["junction_nt"])


def test_mxe_negative_strand_swaps_in_the_other_exclusive_exon() -> None:
    provider = SyntheticProvider(MXE_MINUS, [(151, 210), (111, 140), (1, 60)], strand=-1)
    event = _event("MXE", _mxe_row((111, 140), (71, 100)), "-")
    result = _build_one(event, provider)
    assert "reason" not in result, result
    assert result["altered_cds"] == FLANK5 + EXON_B + FLANK3


def test_mxe_partially_coded_exon_is_skipped() -> None:
    """互斥外显子只有一部分落在 CDS 内时不做猜测，直接跳过。"""
    provider = SyntheticProvider(MXE_PLUS, [(1, 60), (75, 100), (151, 210)])
    event = _event("MXE", _mxe_row((71, 100), (111, 140)), "+")
    result = _build_one(event, provider)
    assert result.get("reason") == "no_reconstructable_orf"


# ---------------------------------------------------------------------------
# 端到端：五类事件都能进表
# ---------------------------------------------------------------------------
_RMATS_TAIL = ["10", "1", "1", "10", "100", "100", "0.0001", "0.001",
               "0.1,0.1", "0.9,0.9", "0.8"]
_BASE_HEAD = ["ID", "GeneID", "geneSymbol", "chr", "strand"]


def _write_tables(directory: Path) -> None:
    """写五张最小的 rMATS 表，全部指向同一套合成基因组。"""
    def write(name: str, header: list[str], row: list[str]) -> None:
        with (directory / name).open("w", encoding="utf-8", newline="") as fh:
            writer = csv.writer(fh, delimiter="\t", lineterminator="\n")
            writer.writerow(_BASE_HEAD + header + [
                "IJC_SAMPLE_1", "SJC_SAMPLE_1", "IJC_SAMPLE_2", "SJC_SAMPLE_2",
                "IncFormLen", "SkipFormLen", "PValue", "FDR",
                "IncLevel1", "IncLevel2", "IncLevelDifference"])
            writer.writerow(["1", "ENSG_SYN", "SYNGENE", "1", "+"] + row + _RMATS_TAIL)

    write("SE.MATS.JC.txt",
          ["exonStart_0base", "exonEnd", "upstreamES", "upstreamEE",
           "downstreamES", "downstreamEE"],
          ["70", "100", "1", "60", "111", "170"])
    write("RI.MATS.JC.txt",
          ["riExonStart_0base", "riExonEnd", "upstreamES", "upstreamEE",
           "downstreamES", "downstreamEE"],
          ["70", "100", "1", "60", "111", "170"])
    write("A3SS.MATS.JC.txt",
          ["longExonStart_0base", "longExonEnd", "shortES", "shortEE",
           "flankingES", "flankingEE"],
          ["70", "100", "76", "100", "1", "60"])
    write("A5SS.MATS.JC.txt",
          ["longExonStart_0base", "longExonEnd", "shortES", "shortEE",
           "flankingES", "flankingEE"],
          ["70", "100", "70", "94", "1", "60"])
    write("MXE.MATS.JC.txt",
          ["1stExonStart_0base", "1stExonEnd", "2ndExonStart_0base", "2ndExonEnd",
           "upstreamES", "upstreamEE", "downstreamES", "downstreamEE"],
          ["70", "100", "110", "140", "1", "60", "151", "210"])


def test_build_orf_table_covers_all_five_event_types(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    _write_tables(source)
    genome = _genome(FLANK5, INTRON, EXON_A, INTRON, EXON_B, INTRON, FLANK3)
    provider = SyntheticProvider(genome, [(1, 60), (71, 100), (151, 210)])

    output = source / "splice_orfs.tsv"
    manifest = build_orf_table(source, output, provider=provider, max_events=10)

    assert manifest["supported_event_types"] == ["SE", "RI", "A3SS", "A5SS", "MXE"]
    written = {row["event_id"] for row in _read(output)}
    # SE / A3SS / A5SS / MXE 在 + 链上都能重建；RI 的保留内含子与中间外显子重叠，
    # 找不到「左右相邻且夹住内含子」的区段对，应被明确跳过而不是静默消失。
    assert written == {"SE:1", "A3SS:1", "A5SS:1", "MXE:1"}
    assert [item["event_id"] for item in manifest["skipped"]] == ["RI:1"]
    assert manifest["skipped"][0]["reason"] == "no_reconstructable_orf"


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))
