"""Recover missing standard figures for projects saved by an earlier run."""

import json
from pathlib import Path
from types import SimpleNamespace

from epitoperank.analysis import visualization as viz
from epitoperank.analysis.enrichment import EnrichmentResult
from epitoperank.data.loader import load_dataset
from epitoperank.splicing.schema import SampleMetadata


def build_figure(name, memory, project, target: Path, analysis):
    """按图表名称从项目数据库或原始输入目录重建缺失的标准图表（火山图、富集图、热图等）。"""
    project_id = project["project_id"]
    source = project.get("source_dir")
    if name == "candidate_ranking":
        candidates = [SimpleNamespace(**row) for row in memory.load_candidates(project_id)]
        return viz.plot_candidate_ranking(candidates, target)
    if name == "enrichment":
        terms = [
            EnrichmentResult(
                row["ontology"], row["term"], row["gene_count"], row["background_count"],
                row["fold_enrichment"], row["p_value"], row["fdr"], tuple(json.loads(row["genes_json"])),
            )
            for row in memory.load_enrichment(project_id)
        ]
        return viz.plot_enrichment(terms, target)

    rows = memory.load_figure_events(project_id, name)
    if not rows and memory.count_events(project_id) == 0:
        if not source or not Path(source).exists():
            return None
        dataset = load_dataset(source)
        events, samples = dataset.events, dataset.samples
    else:
        for row in rows:
            if "psi_json" in row:
                row["psi_by_sample"] = json.loads(row.pop("psi_json") or "{}")
        events = [SimpleNamespace(**row) for row in rows]
        samples = [
            SampleMetadata(row["sample_id"], row["group_name"])
            for row in memory.load_samples(project_id)
        ]

    if name == "volcano":
        fdr, dpsi = analysis.fdr_threshold, analysis.delta_psi_threshold
        try:
            saved = json.loads((target.parent / "agent_state.json").read_text(encoding="utf-8"))
            gates = saved.get("facts", {}).get("filtered_with") or saved.get("params", {})
            fdr, dpsi = float(gates.get("fdr", fdr)), float(gates.get("delta_psi", dpsi))
        except (OSError, ValueError, TypeError):
            pass
        return viz.plot_volcano(events, target, fdr, dpsi)
    if name == "event_type_counts":
        return viz.plot_event_type_counts(events, target)
    if name == "psi_heatmap":
        return viz.plot_psi_heatmap(events, samples, target)
    return viz.plot_psi_distribution(events, samples, target)
