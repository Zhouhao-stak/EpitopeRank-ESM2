"""Append saved candidate evidence to the original splicing report."""

from __future__ import annotations

import csv
import html
import json
import logging
import re
from dataclasses import dataclass
from io import BytesIO
from itertools import islice
from pathlib import Path

logger = logging.getLogger(__name__)
ROW_LIMIT = 25
HEADERS = ("Peptide", "Gene / source event", "MHC-I HLA / % rank",
           "MHC-II HLA / % rank", "Binding tier / evidence level")
LIMITATION = (
    "These are research candidates. HLA predictions and percentile ranks are computational evidence. "
    "Antigen presentation, tumor specificity and T-cell recognition require independent evidence."
)


@dataclass
class CandidateSection:
    title: str
    summary: str
    rows: list[tuple[str, ...]]


def _table(path: Path) -> list[dict[str, str]]:
    """读取制表符分隔的候选结果表（最多返回 ROW_LIMIT 行），文件不存在时返回空列表。"""
    if not path.is_file():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(islice(csv.DictReader(handle, delimiter="\t"), ROW_LIMIT))


def load_sections(project_dir: Path, input_dir: Path | None) -> list[CandidateSection]:
    """读取新抗原与多肽工作台的最新保存结果（兼容历史输出路径），组装为报告章节列表。"""
    sections = []
    roots = [project_dir]
    if input_dir is not None:
        roots.append(input_dir)
    for folder, filename, title in (
        ("neoantigen_results", "neoantigen_manifest.json", "Splice-derived candidates"),
        ("peptide_results", "manifest.json", "Peptide workbench candidates"),
    ):
        manifest = next((root / folder / filename for root in roots
                         if (root / folder / filename).is_file()), None)
        if manifest is None:
            continue
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
            predictions = data.get("prediction_summary") or {}
            count = data.get("candidate_count", "unknown")
            predicted = predictions.get("prediction_count", data.get("prediction_count", 0))
            errors = predictions.get("error_count", len(data.get("prediction_errors") or []))
            methods = predictions.get("method_labels") or [data.get("prediction_method") or ""]
            method_label = ", ".join(filter(None, methods))
            summary = f"Candidate rows: {count}. Prediction records: {predicted}. Prediction errors: {errors}."
            if method_label:
                summary += f" Methods: {method_label}."
            tiers = data.get("binding_tiers") or predictions.get("tiers") or {}
            if folder == "neoantigen_results":
                tiers = {label: tiers[key] for label, key in (
                    ("strong", "strong_count"), ("weak", "weak_count"),
                    ("non-binding", "not_binding_count"), ("unknown", "unknown_count"),
                ) if key in tiers}
            if isinstance(tiers, dict) and tiers:
                counts = ", ".join(f"{label}={total}" for label, total in sorted(tiers.items()))
                summary += f" Saved tiers: {counts}."
            if data.get("prediction_truncated"):
                summary += f" Combinations beyond the prediction limit: {data['prediction_truncated']}."
            if not predicted:
                requested = data.get("alleles") or predictions.get("alleles")
                if (data.get("options") or {}).get("predictor") == "none":
                    requested = False
                summary += (" No prediction results were returned." if requested
                            else " HLA binding was not evaluated.")
            if folder == "neoantigen_results":
                summary += " Sequence novelty was checked against the supplied reference CDS."
            else:
                summary += " Inspect the manifest for reference coverage and scoring inputs."
            records = _table(manifest.parent / "ranked_candidates.tsv")
            if not records:
                records = _table(manifest.parent / "splice_peptides.tsv")
            if any(row.get("mhc_class2_percentile") for row in records):
                summary += " MHC-II ranks refer to the predicted core in the submitted window or peptide."
            rows = []
            for row in records:
                gene = row.get("gene_symbol") or row.get("gene_id")
                source = " / ".join(filter(None, (gene, row.get("event_id"), row.get("event_type"))))
                allele = row.get("allele") or row.get("best_allele")
                rank = row.get("percentile_rank")
                # Older workbench tables put the best class II result in both
                # sets of columns when no class I rank was available.
                class2_only = (allele, rank) == (row.get("mhc_class2_allele"), row.get("mhc_class2_percentile"))
                mhc_i = "" if class2_only else " / ".join(filter(None, (allele, rank)))
                mhc_ii = " / ".join(filter(None, (row.get("mhc_class2_allele"),
                                                  row.get("mhc_class2_percentile"))))
                tier_parts = [row.get("binding_tier") or row.get("evidence_tier") or "-"]
                if row.get("esm2_immunogenicity"):
                    tier_parts.append(f"ESM2={row['esm2_immunogenicity']}")
                if row.get("esm2_fusion_tier"):
                    tier_parts.append(str(row["esm2_fusion_tier"]))
                rows.append((row.get("peptide") or "-", source or "-", mhc_i or "-",
                             mhc_ii or "-", " / ".join(tier_parts)))
            sections.append(CandidateSection(title, summary, rows))
        except (OSError, ValueError, TypeError, AttributeError, csv.Error):
            logger.warning("Could not read candidate results at %s", manifest, exc_info=True)
            sections.append(CandidateSection(title, "Saved result files could not be read.", []))
    return sections


def _blocks(sections: list[CandidateSection]) -> list[CandidateSection]:
    """返回待渲染的候选章节列表；若暂无候选结果，则返回一条提示占位章节。"""
    return sections or [CandidateSection(
        "Candidate evidence status",
        "No candidate run is saved for this project. Run Splice Neoantigens or the project Peptide Workbench and export again.",
        [],
    )]


def append_html(original: str, sections: list[CandidateSection]) -> str:
    """将候选多肽与新抗原证据章节追加插入到 HTML 报告的 </body> 之前。"""
    parts = ['<section id="candidate-neoantigens"><h2>Candidate peptides and neoantigens</h2>']
    parts.append(f"<p>{LIMITATION}</p>")
    for section in _blocks(sections):
        parts.append(f"<h3>{html.escape(section.title)}</h3><p>{html.escape(section.summary)}</p>")
        if section.rows:
            parts.append(f"<p>Showing up to {ROW_LIMIT} saved rows. Full results are in the candidate tables.</p>")
            parts.append("<table><thead><tr>" + "".join(f"<th>{h}</th>" for h in HEADERS) + "</tr></thead><tbody>")
            for row in section.rows:
                parts.append("<tr>" + "".join(f"<td>{html.escape(cell)}</td>" for cell in row) + "</tr>")
            parts.append("</tbody></table>")
    parts.append("</section>")
    block = "\n".join(parts)
    end = re.search(r"</body\s*>", original, re.IGNORECASE)
    return original[:end.start()] + block + original[end.start():] if end else original + block


def append_pdf(original: Path, sections: list[CandidateSection]) -> bytes:
    """将候选多肽与新抗原证据页面渲染为 PDF 并追加合并到原始 PDF 报告末尾，返回字节流。"""
    from pypdf import PdfWriter
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table

    styles = getSampleStyleSheet()
    cell_style = ParagraphStyle("AntigenCell", parent=styles["BodyText"], fontSize=8, leading=10)
    story = [Paragraph("Candidate peptides and neoantigens", styles["Heading1"]),
             Paragraph(LIMITATION, styles["BodyText"])]
    for section in _blocks(sections):
        story.append(Paragraph(html.escape(section.title), styles["Heading2"]))
        story.append(Paragraph(html.escape(section.summary), styles["BodyText"]))
        if section.rows:
            story.append(Paragraph(f"Showing up to {ROW_LIMIT} saved rows. Full results are in the candidate tables.",
                                   styles["BodyText"]))
            story.append(Spacer(1, 8))
            cells = [[Paragraph(html.escape(cell), cell_style) for cell in row]
                     for row in (HEADERS, *section.rows)]
            story.append(Table(cells, colWidths=[116, 133, 74, 74, 65], repeatRows=1, style=[
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEF5FA")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LINEBELOW", (0, 0), (-1, 0), 0.4, colors.lightgrey),
            ]))
    supplement = BytesIO()
    SimpleDocTemplate(supplement, pagesize=A4, leftMargin=54, rightMargin=54).build(story)
    output = BytesIO()
    with PdfWriter() as writer:
        with original.open("rb") as source:
            writer.append(source)
            writer.append(supplement)
            writer.write(output)
    return output.getvalue()
