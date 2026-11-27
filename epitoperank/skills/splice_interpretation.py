"""Splice event interpretation skill.

Provides clinical and functional interpretation of alternative splicing events:
- Protein domain impact analysis (UniProt)
- Clinical database lookups (ClinVar / OMIM via NCBI E-utilities)
- Therapeutic targeting opportunities (ClinicalTrials.gov)
- Disease mechanism hypotheses based on event type

Two capabilities that were previously advertised are **not** implemented here and
must not be faked: splice-site strength (MaxEntScan / SpliceSiteFinder) and
SpliceAI delta scores.  Both now report themselves as ``unavailable`` in
``interpretation["data_sources"]`` instead of returning a placeholder that an
LLM or a reader could mistake for a real prediction.
"""

from __future__ import annotations

from typing import Any

import httpx

from epitoperank.skills.base import BaseSkill, SkillResult

#: 未取得的数据源在结果里的统一标记。
UNAVAILABLE = "unavailable"
#: 已取得的数据源在结果里的统一标记。
AVAILABLE = "available"


def _source(status: str, reason: str) -> dict[str, str]:
    """构造一条数据源状态记录，供上层区分「拿到了」与「没拿到」。"""
    return {"status": status, "reason": reason}


class SpliceInterpretationSkill(BaseSkill):
    """Interpret the biological and clinical significance of splicing events."""

    @property
    def name(self) -> str:
        """技能标识符 splice_interpretation，供工具注册与调用时使用。"""
        return "splice_interpretation"

    @property
    def description(self) -> str:
        """供模型选择工具时阅读的技能说明（中文）。"""
        return "解读可变剪接事件的生物学和临床意义，包括剪接位点强度预测、致病性评估、蛋白结构域影响和治疗靶点分析"

    @property
    def input_schema(self) -> dict[str, Any]:
        """技能的入参 JSON Schema：gene_symbol 与 event_type 必填，坐标与 ΔPSI 可选。"""
        return {
            "type": "object",
            "properties": {
                "gene_symbol": {
                    "type": "string",
                    "description": "Gene symbol (e.g., BRCA1)",
                },
                "event_type": {
                    "type": "string",
                    "enum": ["SE", "MXE", "A5SS", "A3SS", "RI"],
                    "description": "Alternative splicing event type",
                },
                "chromosome": {
                    "type": "string",
                    "description": "Chromosome (e.g., chr17)",
                },
                "start": {
                    "type": "integer",
                    "description": "Genomic start position (GRCh38)",
                },
                "end": {
                    "type": "integer",
                    "description": "Genomic end position (GRCh38)",
                },
                "strand": {
                    "type": "string",
                    "enum": ["+", "-"],
                    "description": "DNA strand orientation",
                },
                "delta_psi": {
                    "type": "number",
                    "description": "Change in percent spliced in (PSI)",
                },
                "fdr": {
                    "type": "number",
                    "description": "False discovery rate",
                },
                "include_therapeutics": {
                    "type": "boolean",
                    "default": True,
                    "description": "Include therapeutic targeting information",
                },
            },
            "required": ["gene_symbol", "event_type"],
        }

    async def execute(self, **kwargs: Any) -> SkillResult:
        """汇总剪接位点、致病性、蛋白影响、临床与治疗信息并生成中文小结。"""
        gene_symbol = kwargs.get("gene_symbol")
        event_type = kwargs.get("event_type")
        chromosome = kwargs.get("chromosome")
        start = kwargs.get("start")
        end = kwargs.get("end")
        strand = kwargs.get("strand")
        delta_psi = kwargs.get("delta_psi")
        fdr = kwargs.get("fdr")
        include_therapeutics = kwargs.get("include_therapeutics", True)

        if not gene_symbol or not event_type:
            return SkillResult(
                skill_name=self.name,
                success=False,
                error="必须提供基因符号和事件类型",
            )

        try:
            interpretation: dict[str, Any] = {}
            sources: dict[str, dict[str, str]] = {}

            # 1. 剪接位点强度：本仓库未集成 MaxEntScan，明确记为不可用，
            #    不再返回「method: MaxEntScan (placeholder)」这种半成品字段。
            if chromosome and start and end:
                splice_strength = await self._predict_splice_strength(
                    chromosome, start, end, strand, sources
                )
                if splice_strength:
                    interpretation["splice_site_prediction"] = splice_strength
            else:
                sources["maxentscan"] = _source(
                    UNAVAILABLE, "缺少染色体坐标，未尝试剪接位点强度预测"
                )

            # 2. SpliceAI 致病性评分：无稳定公开 REST 接口，同样如实报告
            spliceai_scores = await self._get_spliceai_scores(
                gene_symbol, chromosome, start, end, sources
            )
            if spliceai_scores:
                interpretation["pathogenicity"] = spliceai_scores

            # 3. Analyze protein domain impact
            if delta_psi is not None:
                protein_impact = await self._analyze_protein_impact(
                    gene_symbol, event_type, delta_psi, sources
                )
                if protein_impact:
                    interpretation["protein_impact"] = protein_impact

            # 4. Check clinical databases
            clinical_info = await self._query_clinical_databases(
                gene_symbol, event_type, sources
            )
            if clinical_info:
                interpretation["clinical_significance"] = clinical_info

            # 5. Therapeutic opportunities
            if include_therapeutics:
                therapeutics = await self._find_therapeutic_opportunities(
                    gene_symbol, event_type
                )
                if therapeutics:
                    interpretation["therapeutic_opportunities"] = therapeutics

            # 6. Generate summary interpretation
            interpretation["data_sources"] = sources
            summary = self._generate_summary(
                gene_symbol, event_type, delta_psi, fdr, interpretation
            )
            interpretation["summary"] = summary

            # 除了 summary / data_sources 之外没有任何实质内容时才算失败，
            # 避免把所有外部源都不可用的情形报成「已解读成功」。
            substantive = set(interpretation) - {"summary", "data_sources"}
            if not substantive:
                return SkillResult(
                    skill_name=self.name,
                    success=False,
                    error=f"无法解读 {gene_symbol} 的 {event_type} 事件：外部数据源均未返回内容",
                    metadata={"data_sources": sources},
                )

            return SkillResult(
                skill_name=self.name,
                success=True,
                data={
                    "gene": gene_symbol,
                    "event_type": event_type,
                    "interpretation": interpretation,
                },
                metadata={
                    "delta_psi": delta_psi,
                    "fdr": fdr,
                    "data_sources": sources,
                    "unavailable_sources": [
                        name for name, info in sources.items()
                        if info.get("status") == UNAVAILABLE
                    ],
                    "genomic_location": (
                        f"{chromosome}:{start}-{end}" if chromosome and start else None
                    ),
                },
            )

        except Exception as exc:  # noqa: BLE001
            return SkillResult(
                skill_name=self.name,
                success=False,
                error=f"剪接事件解读失败: {str(exc)}",
            )

    # 中文备注：外部技能：预测splicestrength（参数：chromosome、start、end、strand、sources）
    async def _predict_splice_strength(
        self,
        chromosome: str,
        start: int,
        end: int,
        strand: str | None,
        sources: dict[str, dict[str, str]],
    ) -> dict[str, Any] | None:
        """剪接位点强度预测。

        本仓库没有集成 MaxEntScan / SpliceSiteFinder，因此这里**不产出任何分数**，
        只把数据源标记为不可用。早先的实现返回 ``method: "MaxEntScan (placeholder)"``，
        会让模型和报告把一次从未发生的计算当成已完成的证据。
        """
        sources["maxentscan"] = _source(
            UNAVAILABLE,
            "未集成 MaxEntScan / SpliceSiteFinder，不输出剪接位点强度分数",
        )
        return None

    # 中文备注：外部技能：获取spliceai分数（参数：gene_symbol、chromosome、start、end、sources）
    async def _get_spliceai_scores(
        self,
        gene_symbol: str,
        chromosome: str | None,
        start: int | None,
        end: int | None,
        sources: dict[str, dict[str, str]],
    ) -> dict[str, Any] | None:
        """SpliceAI delta 评分。

        SpliceAI 官方只提供本地权重与 UCSC 的网页版查询，没有稳定的公开 REST 接口，
        本仓库也不打包权重，因此不返回任何分数。早先的实现会返回一个全为 ``None``
        的假结果，等于每份解读都带着一条「致病性待查询」的噪声。
        """
        if not (chromosome and start and end):
            sources["spliceai"] = _source(
                UNAVAILABLE, "缺少染色体坐标，未尝试 SpliceAI 查询"
            )
            return None
        sources["spliceai"] = _source(
            UNAVAILABLE,
            "未集成 SpliceAI 本地权重或 UCSC 查询，不输出 ds_max 等致病性分数",
        )
        return None

    # 中文备注：外部技能：辅助处理analyzeproteinimpact（参数：gene_symbol、event_type、delta_psi、sources）
    async def _analyze_protein_impact(
        self,
        gene_symbol: str,
        event_type: str,
        delta_psi: float,
        sources: dict[str, dict[str, str]],
    ) -> dict[str, Any] | None:
        """从 UniProt 取结构域注释，给出剪接事件可能影响的结构域。

        早先的实现用 ``fields=domains`` 查询并读 ``results[0]["domains"]``——这两处
        都不是 UniProt REST 的字段（结构域在 ``features`` 里，类型的值是 ``Domain``），
        因此永远取不到结构域，却仍然返回一个带通用结论的对象，看上去像做过分析。
        现在结构域要么真的解析出来，要么把 ``uniprot`` 标为不可用并说明原因，
        结论的 ``basis`` 会标明它是「结构域注释」还是「按事件类型的通用推断」。
        """
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    "https://rest.uniprot.org/uniprotkb/search",
                    params={
                        "query": (f"gene_exact:{gene_symbol} AND "
                                  "organism_id:9606 AND reviewed:true"),
                        "format": "json",
                        "size": 1,
                    },
                )
                if response.status_code != 200:
                    sources["uniprot"] = _source(
                        UNAVAILABLE, f"UniProt 返回 HTTP {response.status_code}"
                    )
                    return self._impact_heuristic(event_type, delta_psi)

                results = response.json().get("results") or []
                if not results:
                    sources["uniprot"] = _source(
                        UNAVAILABLE, "UniProt 未匹配到该基因的已审阅条目"
                    )
                    return self._impact_heuristic(event_type, delta_psi)

                domains = self._uniprot_domains(results[0])
                if not domains:
                    sources["uniprot"] = _source(
                        UNAVAILABLE, "UniProt 条目没有结构域类注释"
                    )
                    return self._impact_heuristic(event_type, delta_psi)

                sources["uniprot"] = _source(
                    AVAILABLE, f"取到 {len(domains)} 条结构域类注释"
                )
                return {
                    "event_type": event_type,
                    "delta_psi": delta_psi,
                    "uniprot_accession": results[0].get("primaryAccession"),
                    "affected_domains": domains[:5],
                    "functional_consequence": self._event_type_consequence(
                        event_type, delta_psi
                    ),
                    "basis": "uniprot_domains",
                }
        except Exception as exc:  # noqa: BLE001
            sources["uniprot"] = _source(UNAVAILABLE, f"UniProt 查询失败: {exc}"[:200])
            return self._impact_heuristic(event_type, delta_psi)

    @staticmethod
    # 中文备注：外部技能：解析uniprot结构域（参数：entry）
    def _uniprot_domains(entry: dict[str, Any]) -> list[dict[str, Any]]:
        """从 UniProt 条目里取结构域类 feature（Domain / Region / Zinc finger）。"""
        wanted = ("Domain", "Region", "Zinc finger", "Motif")
        domains = []
        for feature in entry.get("features") or []:
            feature_type = str(feature.get("type") or "")
            if not any(key in feature_type for key in wanted):
                continue
            location = feature.get("location") or {}
            domains.append({
                "name": feature.get("description") or feature_type,
                "type": feature_type,
                "start": (location.get("start") or {}).get("value"),
                "end": (location.get("end") or {}).get("value"),
            })
        return domains

    @staticmethod
    # 中文备注：外部技能：按事件类型给通用推断（参数：event_type、delta_psi）
    def _event_type_consequence(event_type: str, delta_psi: float) -> str | None:
        """按事件类型给出的通用生物学推断，不含任何具体结构域信息。"""
        if event_type == "SE":
            return ("外显子跳跃可能导致蛋白结构域缺失或移码突变"
                    if abs(delta_psi) > 0.2
                    else "外显子跳跃程度较轻，可能影响有限")
        if event_type == "RI":
            return "内含子保留通常引入提前终止密码子，导致无义介导的mRNA降解"
        if event_type in ("A5SS", "A3SS"):
            return "剪接位点改变可能导致蛋白C端或N端截短"
        if event_type == "MXE":
            return "互斥外显子替换可能改变蛋白结构域组成"
        return None

    @classmethod
    # 中文备注：外部技能：无结构域注释时的降级结论（参数：event_type、delta_psi）
    def _impact_heuristic(cls, event_type: str, delta_psi: float) -> dict[str, Any]:
        """取不到结构域注释时的降级返回：只给通用推断，并标明依据。"""
        return {
            "event_type": event_type,
            "delta_psi": delta_psi,
            "affected_domains": [],
            "functional_consequence": cls._event_type_consequence(event_type, delta_psi),
            "basis": "event_type_heuristic",
            "note": "未取得该基因的结构域注释，无法判断具体结构域是否受影响",
        }

    # 中文备注：外部技能：辅助处理查询clinicaldatabases（参数：gene_symbol、event_type、sources）
    async def _query_clinical_databases(
        self, gene_symbol: str, event_type: str,
        sources: dict[str, dict[str, str]],
    ) -> dict[str, Any] | None:
        """查询 ClinVar / OMIM 里与该基因剪接相关的记录。"""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                clinical_data = {"clinvar": [], "omim": [], "cosmic": []}

                # Query ClinVar
                clinvar_response = await client.get(
                    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
                    params={
                        "db": "clinvar",
                        "term": f"{gene_symbol}[gene] AND splicing",
                        "retmode": "json",
                        "retmax": 5,
                    },
                )

                if clinvar_response.status_code == 200:
                    clinvar_data_raw = clinvar_response.json()
                    ids = clinvar_data_raw.get("esearchresult", {}).get("idlist", [])
                    clinical_data["clinvar"] = [
                        {"clinvar_id": cid, "gene": gene_symbol} for cid in ids[:3]
                    ]

                # Query OMIM
                omim_response = await client.get(
                    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
                    params={
                        "db": "omim",
                        "term": gene_symbol,
                        "retmode": "json",
                        "retmax": 3,
                    },
                )

                if omim_response.status_code == 200:
                    omim_data_raw = omim_response.json()
                    ids = omim_data_raw.get("esearchresult", {}).get("idlist", [])
                    clinical_data["omim"] = [
                        {"omim_id": oid, "gene": gene_symbol} for oid in ids[:3]
                    ]

                # Filter out empty results
                return {k: v for k, v in clinical_data.items() if v}

        except Exception:  # noqa: BLE001
            return None

    # 中文备注：外部技能：辅助处理findtherapeuticopportunities（参数：gene_symbol、event_type）
    async def _find_therapeutic_opportunities(
        self, gene_symbol: str, event_type: str
    ) -> dict[str, Any] | None:
        """Find therapeutic targeting opportunities."""
        # This would integrate with drug databases and ASO design tools
        therapeutic_info = {
            "targeting_strategies": [],
            "existing_drugs": [],
            "clinical_trials": [],
        }

        # General strategies based on event type
        if event_type == "SE":
            therapeutic_info["targeting_strategies"].append(
                {
                    "strategy": "反义寡核苷酸 (ASO)",
                    "mechanism": "阻断剪接沉默子或增强剪接增强子结合",
                    "example": "Nusinersen (Spinraza) for SMN2 exon 7 inclusion",
                }
            )
        elif event_type == "RI":
            therapeutic_info["targeting_strategies"].append(
                {
                    "strategy": "小分子剪接调节剂",
                    "mechanism": "调节剪接因子活性以促进内含子去除",
                    "example": "Risdiplam for SMN2 splicing modulation",
                }
            )

        # Check ClinicalTrials.gov for ongoing trials
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                trials_response = await client.get(
                    "https://clinicaltrials.gov/api/v2/studies",
                    params={
                        "query.term": f"{gene_symbol} AND splicing",
                        "pageSize": 3,
                    },
                )

                if trials_response.status_code == 200:
                    trials_data = trials_response.json()
                    studies = trials_data.get("studies", [])
                    therapeutic_info["clinical_trials"] = [
                        {
                            "nct_id": study.get("protocolSection", {}).get(
                                "identificationModule", {}
                            ).get("nctId"),
                            "title": study.get("protocolSection", {})
                            .get("identificationModule", {})
                            .get("briefTitle"),
                            "status": study.get("protocolSection", {})
                            .get("statusModule", {})
                            .get("overallStatus"),
                        }
                        for study in studies[:3]
                    ]
        except Exception:  # noqa: BLE001
            pass

        return therapeutic_info if any(therapeutic_info.values()) else None

    # 中文备注：外部技能：生成摘要（参数：gene_symbol、event_type、delta_psi、fdr、interpretation）
    def _generate_summary(
        self,
        gene_symbol: str,
        event_type: str,
        delta_psi: float | None,
        fdr: float | None,
        interpretation: dict[str, Any],
    ) -> str:
        """生成中文小结。

        只陈述**真的拿到**的东西：早先的实现会因为 pathogenicity 键恒存在而
        每次都输出「SpliceAI 致病性评分待查询」，等于把一次未发生的查询写进结论。
        """
        parts = [f"基因 {gene_symbol} 发生 {event_type} 型可变剪接事件。"]

        if delta_psi is not None:
            direction = "增加" if delta_psi > 0 else "减少"
            parts.append(f"剪接变化幅度为 {abs(delta_psi):.1%}（PSI {direction}）。")

        if fdr is not None and fdr < 0.05:
            parts.append(f"该变化具有统计学显著性（FDR = {fdr:.2e}）。")

        impact = interpretation.get("protein_impact") or {}
        consequence = impact.get("functional_consequence")
        if consequence:
            if impact.get("basis") == "uniprot_domains":
                parts.append(f"功能影响：{consequence}")
            else:
                parts.append(f"功能影响（按事件类型的通用推断，未经结构域注释核对）：{consequence}")

        clinical = interpretation.get("clinical_significance") or {}
        if clinical.get("clinvar"):
            parts.append(f"ClinVar 命中 {len(clinical['clinvar'])} 条相关记录。")

        strategies = (interpretation.get("therapeutic_opportunities") or {}).get(
            "targeting_strategies", []
        )
        if strategies:
            parts.append(f"潜在治疗策略：{strategies[0].get('strategy', '未知')}")

        missing = [
            name for name, info in (interpretation.get("data_sources") or {}).items()
            if info.get("status") == UNAVAILABLE
        ]
        if missing:
            parts.append(f"未获取到：{'、'.join(missing)}。")

        return "".join(parts)
