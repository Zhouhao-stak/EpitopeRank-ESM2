"""外部数据源的「诚实性」测试。

这一组用例保护的是一个容易退化的性质：**没取到的数据必须表现为「没取到」**，
不能变成一条看起来像结论的占位字段。历史上这里出过三种问题——
MaxEntScan 返回 ``method: "MaxEntScan (placeholder)"``、
SpliceAI 返回全 None 的假分数但摘要里照样写「致病性评分待查询」、
PubMed 请求了摘要 XML 却直接丢弃。

全部不联网：只测纯解析函数与「不联网也应正确标记为不可用」的分支。
"""
from __future__ import annotations

import pytest

from epitoperank.skills.gene_annotation import (
    GeneAnnotationSkill, _ensembl_host, _normalise_build,
)
from epitoperank.skills.literature_search import _parse_pubmed_abstracts
from epitoperank.skills.splice_interpretation import (
    AVAILABLE, UNAVAILABLE, SpliceInterpretationSkill,
)


# ---------------------------------------------------------------------------
# 不联网也必须如实标记为不可用
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_splice_strength_reports_unavailable_without_scores() -> None:
    skill = SpliceInterpretationSkill()
    sources: dict[str, dict[str, str]] = {}
    result = await skill._predict_splice_strength("chr17", 7676154, 7676254, "+", sources)

    assert result is None, "未集成 MaxEntScan 时不应产出任何分数"
    assert sources["maxentscan"]["status"] == UNAVAILABLE
    assert "MaxEntScan" in sources["maxentscan"]["reason"]


@pytest.mark.asyncio
async def test_spliceai_reports_unavailable_without_scores() -> None:
    skill = SpliceInterpretationSkill()
    sources: dict[str, dict[str, str]] = {}
    result = await skill._get_spliceai_scores("TP53", "chr17", 7676154, 7676254, sources)

    assert result is None, "SpliceAI 全 None 的假结果必须去掉"
    assert sources["spliceai"]["status"] == UNAVAILABLE


@pytest.mark.asyncio
async def test_spliceai_missing_coordinates_is_still_reported() -> None:
    skill = SpliceInterpretationSkill()
    sources: dict[str, dict[str, str]] = {}
    assert await skill._get_spliceai_scores("TP53", None, None, None, sources) is None
    assert sources["spliceai"]["status"] == UNAVAILABLE
    assert "坐标" in sources["spliceai"]["reason"]


def test_summary_does_not_claim_a_query_that_never_happened() -> None:
    skill = SpliceInterpretationSkill()
    summary = skill._generate_summary(
        "TP53", "SE", 0.6, 0.001,
        {"data_sources": {"spliceai": {"status": UNAVAILABLE, "reason": "未集成"}}},
    )
    assert "待查询" not in summary
    assert "SpliceAI" not in summary
    assert "未获取到" in summary and "spliceai" in summary


def test_summary_marks_heuristic_impact_as_heuristic() -> None:
    skill = SpliceInterpretationSkill()
    summary = skill._generate_summary(
        "TP53", "SE", 0.6, 0.001,
        {"protein_impact": {"functional_consequence": "外显子跳跃可能导致结构域缺失",
                            "basis": "event_type_heuristic"}},
    )
    assert "通用推断" in summary


# ---------------------------------------------------------------------------
# UniProt 结构域解析：真实结构在 features 里，不是 domains
# ---------------------------------------------------------------------------
def test_uniprot_domains_reads_features_not_domains() -> None:
    entry = {
        "primaryAccession": "P04637",
        "features": [
            {"type": "Domain", "description": "Transactivation",
             "location": {"start": {"value": 1}, "end": {"value": 42}}},
            {"type": "Zinc finger", "description": "p53-like tetramerisation",
             "location": {"start": {"value": 100}, "end": {"value": 120}}},
            {"type": "Cross-link", "description": "not a domain",
             "location": {"start": {"value": 200}, "end": {"value": 200}}},
        ],
    }
    domains = SpliceInterpretationSkill._uniprot_domains(entry)
    names = [d["name"] for d in domains]
    assert names == ["Transactivation", "p53-like tetramerisation"]
    assert domains[0]["start"] == 1 and domains[0]["end"] == 42


def test_uniprot_domains_empty_when_no_domain_features() -> None:
    assert SpliceInterpretationSkill._uniprot_domains({"features": []}) == []


def test_impact_heuristic_marks_basis_and_keeps_domains_empty() -> None:
    impact = SpliceInterpretationSkill._impact_heuristic("RI", 0.5)
    assert impact["basis"] == "event_type_heuristic"
    assert impact["affected_domains"] == []
    assert impact["functional_consequence"]


def test_event_type_consequence_covers_all_five_events() -> None:
    for event_type in ("SE", "RI", "A5SS", "A3SS", "MXE"):
        assert SpliceInterpretationSkill._event_type_consequence(event_type, 0.5)


# ---------------------------------------------------------------------------
# 基因组版本必须真的影响请求主机
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(("build", "expected"), [
    ("GRCh38", "https://rest.ensembl.org"),
    ("hg38", "https://rest.ensembl.org"),
    ("GRCh37", "https://grch37.rest.ensembl.org"),
    ("hg19", "https://grch37.rest.ensembl.org"),
])
def test_ensembl_host_follows_genome_build(build: str, expected: str) -> None:
    assert _ensembl_host(build) == expected


def test_unsupported_genome_build_is_not_silently_answered_with_grch38() -> None:
    assert _normalise_build("mm10") is None
    assert _ensembl_host("mm10") is None


def test_gene_annotation_structure_returns_none_for_unknown_build() -> None:
    """版本无法识别时应返回 None（记为未取得），而不是拿默认版本顶上。"""
    skill = GeneAnnotationSkill()
    import asyncio
    assert asyncio.run(skill._fetch_ensembl_structure("ENSG00000141510", "mm10")) is None


# ---------------------------------------------------------------------------
# PubMed 摘要：真的解析出来，而不是丢弃
# ---------------------------------------------------------------------------
_PUBMED_XML = """<?xml version="1.0"?>
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>12345678</PMID>
      <Article>
        <Abstract>
          <AbstractText Label="BACKGROUND">Splicing is frequent in tumours.</AbstractText>
          <AbstractText Label="RESULTS">We found 42 novel junctions.</AbstractText>
        </Abstract>
      </Article>
    </MedlineCitation>
  </PubmedArticle>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>87654321</PMID>
      <Article><Abstract /></Article>
    </MedlineCitation>
  </PubmedArticle>
</PubmedArticleSet>
"""


def test_parse_pubmed_abstracts_joins_labelled_sections() -> None:
    abstracts = _parse_pubmed_abstracts(_PUBMED_XML)
    assert set(abstracts) == {"12345678"}, "没有摘要的条目不应产生空串条目"
    assert "BACKGROUND: Splicing is frequent in tumours." in abstracts["12345678"]
    assert "RESULTS: We found 42 novel junctions." in abstracts["12345678"]


def test_parse_pubmed_abstracts_tolerates_broken_xml() -> None:
    assert _parse_pubmed_abstracts("<PubmedArticleSet><oops>") == {}
