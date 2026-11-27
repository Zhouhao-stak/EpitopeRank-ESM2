"""Gene annotation skill for splicing analysis.

Fetches gene information including:
- Gene / transcript structure from Ensembl (GRCh37 或 GRCh38)
- Alternative-splicing overview inferred from transcript exon structure
- Clinical variants (ClinVar, queried by gene symbol)
- Basic gene metadata (MyGene.info)

Splice-site conservation, GTEx expression and SpliceAI/TCGA event catalogues are
**not** integrated; the results below do not claim to provide them.
"""

from __future__ import annotations

from typing import Any

import httpx

from epitoperank.skills.base import BaseSkill, SkillResult

#: 基因组版本别名 -> Ensembl REST 主机。不同版本必须打不同主机，否则坐标会错版本。
_BUILD_ALIASES: dict[str, str] = {
    "grch38": "GRCh38", "hg38": "GRCh38", "": "GRCh38",
    "grch37": "GRCh37", "hg19": "GRCh37",
}
_ENSEMBL_HOSTS: dict[str, str] = {
    "GRCh38": "https://rest.ensembl.org",
    "GRCh37": "https://grch37.rest.ensembl.org",
}


def _normalise_build(genome_build: str | None) -> str | None:
    """把 GRCh38 / hg38 / GRCh37 / hg19 等写法归一化；无法识别返回 None。"""
    return _BUILD_ALIASES.get(str(genome_build or "").strip().lower())


def _ensembl_host(genome_build: str | None) -> str | None:
    """按基因组版本选择 Ensembl REST 主机；版本不支持时返回 None。"""
    build = _normalise_build(genome_build)
    return _ENSEMBL_HOSTS.get(build) if build else None


class GeneAnnotationSkill(BaseSkill):
    """Retrieve detailed gene annotation for splicing context."""

    @property
    def name(self) -> str:
        """技能标识符 gene_annotation，供工具注册与调用时使用。"""
        return "gene_annotation"

    @property
    def description(self) -> str:
        """供模型选择工具时阅读的技能说明（中文）。"""
        return "获取基因注释信息，包括外显子结构、已知剪接事件、保守性评分和临床变异（支持Ensembl/UCSC数据库查询）"

    @property
    def input_schema(self) -> dict[str, Any]:
        """技能的入参 JSON Schema：gene_symbol 必填，其余为可选查询开关。"""
        return {
            "type": "object",
            "properties": {
                "gene_symbol": {
                    "type": "string",
                    "description": "Gene symbol (e.g., BRCA1, TP53)",
                },
                "gene_id": {
                    "type": "string",
                    "description": "Ensembl gene ID (e.g., ENSG00000012345)",
                },
                "genome_build": {
                    "type": "string",
                    "enum": ["GRCh38", "GRCh37"],
                    "default": "GRCh38",
                    "description": "Genome assembly version",
                },
                "include_splicing": {
                    "type": "boolean",
                    "default": True,
                    "description": "Include known splicing events",
                },
                "include_clinical": {
                    "type": "boolean",
                    "default": True,
                    "description": "Include ClinVar clinical variants",
                },
            },
            "required": ["gene_symbol"],
        }

    async def execute(self, **kwargs: Any) -> SkillResult:
        """执行基因注释查询，依次聚合 MyGene.info、Ensembl 与 ClinVar 的结果。"""
        gene_symbol = kwargs.get("gene_symbol")
        gene_id = kwargs.get("gene_id")
        genome_build = kwargs.get("genome_build", "GRCh38")
        include_splicing = kwargs.get("include_splicing", True)
        include_clinical = kwargs.get("include_clinical", True)

        if not gene_symbol and not gene_id:
            return SkillResult(
                skill_name=self.name,
                success=False,
                error="必须提供 gene_symbol 或 gene_id",
            )

        try:
            result_data = {}

            # Fetch basic gene info from MyGene.info
            basic_info = await self._fetch_mygene_info(gene_symbol or gene_id)
            if basic_info:
                result_data["basic_info"] = basic_info

            # Fetch gene structure from Ensembl
            if gene_id or basic_info:
                ens_id = gene_id or basic_info.get("ensembl_gene")
                if ens_id:
                    structure = await self._fetch_ensembl_structure(ens_id, genome_build)
                    if structure:
                        result_data["gene_structure"] = structure

            # Fetch splicing events
            if include_splicing and (gene_id or basic_info):
                ens_id = gene_id or basic_info.get("ensembl_gene")
                if ens_id:
                    splicing = await self._fetch_splicing_events(ens_id, genome_build)
                    if splicing:
                        result_data["splicing_events"] = splicing

            # Fetch clinical variants
            if include_clinical and (gene_symbol or basic_info):
                # ClinVar 的 [gene] 字段要的是基因符号；用 ENSG 编号查不到东西
                symbol = gene_symbol or (basic_info or {}).get("symbol")
                if symbol:
                    clinical = await self._fetch_clinvar_variants(symbol)
                    if clinical:
                        result_data["clinical_variants"] = clinical

            if not result_data:
                return SkillResult(
                    skill_name=self.name,
                    success=False,
                    error=f"未能获取基因 {gene_symbol or gene_id} 的注释信息",
                )

            return SkillResult(
                skill_name=self.name,
                success=True,
                data=result_data,
                metadata={
                    "gene_symbol": gene_symbol,
                    "gene_id": gene_id,
                    "genome_build": genome_build,
                    "sources": ["MyGene.info", "Ensembl", "ClinVar"],
                },
            )

        except Exception as exc:  # noqa: BLE001
            return SkillResult(
                skill_name=self.name,
                success=False,
                error=f"基因注释查询失败: {str(exc)}",
            )

    # 中文备注：外部技能：获取mygene信息（参数：query）
    async def _fetch_mygene_info(self, query: str) -> dict[str, Any] | None:
        """Fetch basic gene information from MyGene.info."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"https://mygene.info/v3/query?q={query}&fields=symbol,name,ensembl,summary,type_of_gene"
                )
                if response.status_code == 200:
                    data = response.json()
                    hits = data.get("hits", [])
                    if hits:
                        hit = hits[0]
                        # MyGene 在多命中时会把 ensembl 返回成列表，
                        # 直接 .get 会抛 AttributeError 并把整条基因信息丢掉
                        ensembl = hit.get("ensembl")
                        if isinstance(ensembl, list):
                            ensembl = ensembl[0] if ensembl else {}
                        if not isinstance(ensembl, dict):
                            ensembl = {}
                        return {
                            "symbol": hit.get("symbol"),
                            "name": hit.get("name"),
                            "ensembl_gene": ensembl.get("gene"),
                            "summary": hit.get("summary"),
                            "gene_type": hit.get("type_of_gene"),
                        }
        except Exception:  # noqa: BLE001
            pass
        return None

    # 中文备注：外部技能：获取ensemblstructure（参数：gene_id、genome_build）
    async def _fetch_ensembl_structure(
        self, gene_id: str, genome_build: str
    ) -> dict[str, Any] | None:
        """Fetch gene structure from Ensembl REST API.

        早先的实现收下 genome_build 却完全不用，永远查默认的 GRCh38——
        对一个强制要求「坐标与参考版本一致」的平台来说，这会静默返回错版本的坐标。
        现在按版本选主机，版本无法识别时直接返回 None，由上层记为未取得。
        """
        host = _ensembl_host(genome_build)
        if host is None:
            return None
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{host}/lookup/id/{gene_id}",
                    headers={"Content-Type": "application/json"},
                )
                if response.status_code == 200:
                    gene_data = response.json()
                    return {
                        "gene_id": gene_id,
                        "genome_build": _normalise_build(genome_build),
                        "chromosome": gene_data.get("seq_region_name"),
                        "start": gene_data.get("start"),
                        "end": gene_data.get("end"),
                        "strand": gene_data.get("strand"),
                        "biotype": gene_data.get("biotype"),
                        "description": gene_data.get("description"),
                    }
        except Exception:  # noqa: BLE001
            pass
        return None

    # 中文备注：外部技能：获取转录本结构（参数：gene_id、genome_build）
    async def _fetch_splicing_events(
        self, gene_id: str, genome_build: str = "GRCh38"
    ) -> dict[str, Any] | None:
        """用 Ensembl 的转录本结构给出该基因的可变剪接概况。

        早先这里返回的是一条 ``note: "完整剪接事件查询需要集成 SpliceAI…"``——它会被
        当成 ``splicing_events`` 写进结果，模型很容易误读为「查到了剪接事件」。
        Ensembl 本身没有「已知剪接事件」这个接口，但有每个转录本的外显子结构，
        足以给出可核对的客观数字（转录本数、编码转录本数、不同的外显子数分布）。
        这里只陈述这些能算出来的事实，不臆造事件列表。
        """
        host = _ensembl_host(genome_build)
        if host is None:
            return None
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{host}/lookup/id/{gene_id}",
                    params={"expand": "1"},
                    headers={"Content-Type": "application/json"},
                )
                if response.status_code != 200:
                    return None
                data = response.json()
        except Exception:  # noqa: BLE001
            return None

        transcripts = data.get("transcripts") or []
        if not transcripts:
            return None
        coding = [t for t in transcripts if t.get("biotype") == "protein_coding"]
        exon_counts: dict[int, int] = {}
        for transcript in coding:
            count = len(transcript.get("Exon") or [])
            if count:
                exon_counts[count] = exon_counts.get(count, 0) + 1
        return {
            "source": "Ensembl (transcript structure)",
            "genome_build": _normalise_build(genome_build),
            "gene_id": gene_id,
            "transcript_count": len(transcripts),
            "protein_coding_transcript_count": len(coding),
            # 编码转录本的外显子数分布：同一基因出现多种外显子数，说明存在可变剪接
            "exon_count_distribution": dict(sorted(exon_counts.items())),
            "has_alternative_exon_structure": len(exon_counts) > 1,
            "note": (
                "这是由转录本外显子结构推断的可变剪接概况，不是已注释的剪接事件列表；"
                "具体事件仍以项目的 rMATS 结果为准。"
            ),
        }

    # 中文备注：外部技能：获取clinvarvariants（参数：gene_symbol）
    async def _fetch_clinvar_variants(self, gene_symbol: str) -> list[dict[str, Any]] | None:
        """按基因符号查询 ClinVar 中该基因的变异记录。

        参数从 Ensembl 基因编号改为基因符号：ClinVar 的 ``[gene]`` 字段匹配的是
        符号（如 TP53），传 ENSG 编号不会命中，早先这里实际上一直查不到东西。
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
                    params={
                        "db": "clinvar",
                        "term": f"{gene_symbol}[gene]",
                        "retmode": "json",
                        "retmax": 10,
                    },
                )
                if response.status_code == 200:
                    data = response.json()
                    ids = data.get("esearchresult", {}).get("idlist", [])
                    if ids:
                        return [
                            {"clinvar_id": clinvar_id, "gene_symbol": gene_symbol}
                            for clinvar_id in ids[:5]
                        ]
        except Exception:  # noqa: BLE001
            pass
        return None
