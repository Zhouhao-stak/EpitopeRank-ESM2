"""Unit & integration tests for ESM-2-650M LoRA (v4 + v5-beta) integration."""

from __future__ import annotations

from typing import Any

import pytest
import requests
from fastapi.testclient import TestClient

from epitoperank.api.app import create_app
from epitoperank.peptide import capabilities, esm2_client
from epitoperank.peptide.pipeline import _attach_esm2_scores
from epitoperank.peptide.scoring import DEFAULT_WEIGHTS, SPLICING_WEIGHTS, WEIGHT_PRESETS, component_scores, composite, rank


def test_esm2_unconfigured_graceful_degradation(monkeypatch) -> None:
    monkeypatch.delenv("EPITOPERANK_ESM2_URL", raising=False)
    monkeypatch.delenv("EPITOPERANK_ESM2_API_KEY", raising=False)

    st = esm2_client.status()
    assert st["available"] is False
    assert st["configured"] is False
    assert esm2_client.score_candidates([{"peptide": "VVVGADGVGK", "allele": "HLA-A*11:01"}]) == {}

    # 5-dim fallback when esm2_immunogenicity is absent
    res = composite({
        "peptide": "VVVGADGVGK",
        "percentile_rank": 0.2,
        "processing_total_score": 1.0,
        "expression": 20.0,
        "delta_psi": 0.4,
        "self_hit": False,
    })
    assert "immunogenicity" not in res["components_used"]
    assert "immunogenicity" in res["components_missing"]
    assert res["evidence_tier"] == "A"
    assert 0.0 < float(res["composite_score"]) <= 1.0


def test_esm2_timeout_graceful_degradation(monkeypatch) -> None:
    monkeypatch.setenv("EPITOPERANK_ESM2_URL", "http://127.0.0.1:19999")
    monkeypatch.setenv("EPITOPERANK_ESM2_TIMEOUT", "1")

    def _fail_post(*args: Any, **kwargs: Any) -> Any:
        raise requests.Timeout("simulated timeout")

    monkeypatch.setattr(requests, "post", _fail_post)
    rows = [{"peptide": "VVVGADGVGK", "best_allele": "HLA-A*11:01"}]
    assert _attach_esm2_scores(rows) == 0
    assert "esm2_immunogenicity" not in rows[0]


def test_esm2_kras_g12d_online_scoring_and_6dim_ranking(monkeypatch) -> None:
    monkeypatch.setenv("EPITOPERANK_ESM2_URL", "http://127.0.0.1:8090")
    monkeypatch.setenv("EPITOPERANK_ESM2_API_KEY", "test-secret")

    captured: dict[str, Any] = {}

    class _FakeResp:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, Any]:
            return {
                "results": [
                    {
                        "peptide": "VVVGADGVGK",
                        "allele": "HLA-A*11:01",
                        "esm2_v4_score": 0.8074,
                        "v5beta_score": 0.8321,
                        "immunogenicity_score": 0.8074,
                        "residue_weights": [0.05, 0.06, 0.08, 0.12, 0.16, 0.21, 0.14, 0.08, 0.05, 0.05],
                        "mut_wt_detail": {"mut_pos": 6, "d_kd": -3.1, "d_chg": -1.0, "is_tcr": True},
                        "clinical_fusion": {"fusion_score": 0.912, "fusion_tier": "Tier-1"},
                    }
                ]
            }

    def _fake_post(url: str, *, headers: dict[str, str], json: dict[str, Any], timeout: float) -> _FakeResp:
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        captured["timeout"] = timeout
        return _FakeResp()

    monkeypatch.setattr(requests, "post", _fake_post)

    rows: list[dict[str, object]] = [
        {
            "peptide": "VVVGADGVGK",
            "wt_peptide": "VVVGAGGVGK",
            "best_allele": "HLA-A*11:01",
            "percentile_rank": 0.15,
            "ic50_nm": 18.5,
            "expression": 45.0,
            "processing_total_score": 1.2,
            "delta_psi": 0.35,
            "self_hit": False,
        },
        {
            "peptide": "AAAAAAAAA",
            "best_allele": "HLA-A*11:01",
            "percentile_rank": 0.15,
            "processing_total_score": 1.2,
            "expression": 45.0,
            "delta_psi": 0.35,
            "self_hit": False,
            "esm2_immunogenicity": 0.05,
        },
    ]
    matched = _attach_esm2_scores(rows)
    assert matched == 1
    assert captured["url"] == "http://127.0.0.1:8090/api/v1/score_clinical"
    assert captured["headers"]["X-API-Key"] == "test-secret"
    assert captured["json"]["candidates"][0]["wt_peptide"] == "VVVGAGGVGK"
    assert captured["json"]["candidates"][0]["affinity_nm"] == pytest.approx(18.5)
    assert captured["json"]["candidates"][0]["rna_tpm"] == pytest.approx(45.0)

    ranked = rank(rows, weights=DEFAULT_WEIGHTS)
    top = ranked[0]
    assert top["peptide"] == "VVVGADGVGK"
    assert top["esm2_immunogenicity"] == pytest.approx(0.8321)
    assert top["esm2_fusion_tier"] == "Tier-1"
    assert len(top["esm2_residue_weights"]) == 10
    assert "immunogenicity" in top["components_used"]
    assert component_scores(top)["immunogenicity"] == pytest.approx(0.8321)
    assert top["composite_score"] > ranked[1]["composite_score"]


def test_capabilities_api_exposes_esm2_lora(monkeypatch) -> None:
    monkeypatch.delenv("EPITOPERANK_ESM2_URL", raising=False)
    caps = capabilities()
    assert "esm2_lora" in caps["predictors"]
    assert caps["predictors"]["esm2_lora"]["available"] is False

    client = TestClient(create_app())
    resp = client.get("/api/peptide/capabilities")
    assert resp.status_code == 200
    data = resp.json()
    assert "esm2_lora" in data["predictors"]
    assert data["ranking"]["weights"]["immunogenicity"] == pytest.approx(0.25)
    assert data["ranking"]["presets"]["splicing"]["immunogenicity"] == pytest.approx(0.40)
    assert sum(SPLICING_WEIGHTS.values()) == pytest.approx(1.0)
    assert set(WEIGHT_PRESETS.keys()) >= {"default", "splicing"}


def test_esm2_bigmhc_cooperative_scoring_passthrough(monkeypatch) -> None:
    monkeypatch.setenv("EPITOPERANK_ESM2_URL", "http://127.0.0.1:8091")

    class _CoopResp:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, Any]:
            return {
                "bigmhc_im_enabled": True,
                "results": [
                    {
                        "peptide": "VVVGADGVGK",
                        "allele": "HLA-A*11:01",
                        "esm2_v4_score": 0.8074,
                        "v5beta_score": 0.8321,
                        "bigmhc_im_score": 0.7100,
                        "coop_immunogenicity_score": 0.7772,
                        "immunogenicity_score": 0.8074,
                    }
                ],
            }

    monkeypatch.setattr(requests, "post", lambda *a, **kw: _CoopResp())
    rows: list[dict[str, object]] = [{"peptide": "VVVGADGVGK", "best_allele": "HLA-A*11:01"}]
    assert _attach_esm2_scores(rows) == 1
    assert rows[0]["bigmhc_im_score"] == pytest.approx(0.7100)
    assert rows[0]["coop_immunogenicity"] == pytest.approx(0.7772)
    assert rows[0]["esm2_immunogenicity"] == pytest.approx(0.7772)
