"""端到端冒烟：走真实 CLI，检查落盘产物。

这里刻意只做"用户真的会做的两件事"，并且完全离线（``--predictor none``）：

1. CDS 表模式：``--cds splice_orfs.tsv``
2. 裸肽模式：``--peptides peptides.tsv``

单测覆盖的是函数级行为，这一层覆盖的是"命令跑得通、表里有该有的列、manifest 记下了
输入指纹"——也就是 README 里承诺的"丢进去一批数据、出来能用的表"。

用 subprocess 调真实 CLI 而不是直接 import 函数，是为了同时守住 argparse 与
``run.py`` 里的参数校验（例如 ``--lengths`` 的 8–25 边界）。
"""
from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
DEMO = REPO_ROOT / "examples" / "peptide_demo"


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    """调用 run.py peptide，返回完整结果；失败时把输出带进断言信息。"""
    return subprocess.run(
        [sys.executable, "run.py", "peptide", *args],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=300,
    )


def _read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def test_cds_mode_produces_ranked_table(tmp_path: Path) -> None:
    out = tmp_path / "cds_mode"
    result = _run_cli("--input", str(DEMO), "--cds", str(DEMO / "splice_orfs.tsv"),
                      "--mhc-class", "class1", "--predictor", "none", "--out", str(out))
    assert result.returncode == 0, result.stdout + result.stderr

    peptides = _read_tsv(out / "splice_peptides.tsv")
    assert peptides, "CDS 模式应产出连接肽"
    header = set(peptides[0])
    # 这些列是下游（候选表、报告、报告附加证据）依赖的契约
    assert {"event_id", "peptide", "length", "mhc_class", "junction_aa"} <= header
    # 默认 I 类：全部 8-11 aa 且标为类别 1
    assert {p["mhc_class"] for p in peptides} == {"1"}
    assert all(8 <= int(p["length"]) <= 11 for p in peptides)

    ranked = _read_tsv(out / "ranked_candidates.tsv")
    assert len(ranked) == len(peptides)

    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["inputs"]["mode"] == "cds_table"
    assert len(manifest["inputs"]["cds_table_sha256"]) == 64, "输入表应带 SHA-256 指纹"


def test_cds_mode_with_cd4_lengths_marks_class_two(tmp_path: Path) -> None:
    """12-25 aa 的 CD4 连接肽必须标为类别 2，不能被当成 I 类。"""
    out = tmp_path / "cds_cd4"
    result = _run_cli("--input", str(DEMO), "--cds", str(DEMO / "splice_orfs.tsv"),
                      "--mhc-class", "both", "--predictor", "none",
                      "--lengths", "8,9,10,11,15", "--out", str(out))
    assert result.returncode == 0, result.stdout + result.stderr

    peptides = _read_tsv(out / "splice_peptides.tsv")
    by_length: dict[int, set[str]] = {}
    for row in peptides:
        by_length.setdefault(int(row["length"]), set()).add(row["mhc_class"])
    assert by_length[9] == {"1"}
    assert by_length[15] == {"2"}
    # II 类用 p1 anchor，I 类的 p2/p_omega 对它没有意义
    fifteen = next(row for row in peptides if row["length"] == "15")
    assert fifteen.get("p2", "") == "" and fifteen.get("p_omega", "") == ""


def test_cd4_lengths_require_class_two(tmp_path: Path) -> None:
    """只请求 class1 却给 12-25 长度时应报错，而不是静默丢弃。"""
    result = _run_cli("--input", str(DEMO), "--cds", str(DEMO / "splice_orfs.tsv"),
                      "--mhc-class", "class1", "--predictor", "none",
                      "--lengths", "8,15", "--out", str(tmp_path / "bad"))
    assert result.returncode != 0
    assert "MHC-II" in result.stdout


def test_peptide_table_mode_accepts_plain_peptides(tmp_path: Path) -> None:
    out = tmp_path / "peptide_mode"
    result = _run_cli("--input", str(DEMO), "--peptides", str(DEMO / "peptides.tsv"),
                      "--mhc-class", "class1", "--predictor", "none", "--out", str(out))
    assert result.returncode == 0, result.stdout + result.stderr
    peptides = _read_tsv(out / "splice_peptides.tsv")
    assert peptides
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["inputs"]["mode"] in {"peptide_table", "peptide_list"}


@pytest.mark.parametrize("lengths", ["8,30", "7"])
def test_out_of_range_lengths_fail_fast(tmp_path: Path, lengths: str) -> None:
    result = _run_cli("--input", str(DEMO), "--cds", str(DEMO / "splice_orfs.tsv"),
                      "--mhc-class", "both", "--predictor", "none",
                      "--lengths", lengths, "--out", str(tmp_path / "bad"))
    assert result.returncode != 0
    assert "8-25" in result.stdout
