from __future__ import annotations

import pandas as pd
import pytest

from analise.alternativas import calcular_graphql


def test_calcular_graphql_a_partir_dos_arquivos(tmp_path):
    (tmp_path / "graphql").mkdir()
    pd.DataFrame({"owner": ["o", "o"], "repo": ["r", "vazio"]}).to_csv(tmp_path / "repositorios.csv", index=False)
    pd.DataFrame([
        {"owner": "o", "repo": "r", "number": 1, "estado": "merged", "created_at": "2025-03-01T00:00:00Z",
         "merged_at": "2025-03-01T04:00:00Z", "closed_at": "", "primeira_resposta_at": "2025-03-01T01:00:00Z"},
        {"owner": "o", "repo": "r", "number": 2, "estado": "closed", "created_at": "2025-03-02T00:00:00Z",
         "merged_at": "", "closed_at": "2025-03-03T00:00:00Z", "primeira_resposta_at": ""},
    ]).to_csv(tmp_path / "graphql" / "prs.csv.gz", index=False)
    pd.DataFrame([
        {"owner": "o", "repo": "r", "number": 5, "created_at": "2025-03-01T00:00:00Z",
         "closed_at": "2025-03-02T00:00:00Z", "labels": "bug", "eh_bug": True},
    ]).to_csv(tmp_path / "graphql" / "issues.csv.gz", index=False)
    pd.DataFrame([
        {"owner": "o", "repo": "r", "created_at": f"2025-03-0{d}T00:00:00Z", "environment": "production",
         "state": "ACTIVE", "status": "SUCCESS", "status_at": ""} for d in range(1, 7)
    ]).to_csv(tmp_path / "graphql" / "deployments.csv.gz", index=False)
    pd.DataFrame([
        {"owner": "o", "repo": "r", "truncado_prs": False, "truncado_issues": True, "truncado_deployments": False},
    ]).to_csv(tmp_path / "graphql" / "resumo.csv", index=False)

    t = calcular_graphql(tmp_path).set_index("repo")
    assert t.loc["r", "lt_pr_mediana_horas"] == pytest.approx(4)
    assert t.loc["r", "taxa_aceitacao_pr"] == pytest.approx(0.5)
    assert t.loc["r", "resolucao_bug_mediana_horas"] == pytest.approx(24)
    assert bool(t.loc["r", "usa_deployments"]) is True
    assert t.loc["r", "cfr_d_deploy"] == 0
    assert bool(t.loc["r", "truncado_issues"]) is True
    assert t.loc["vazio", "n_prs_mergeados"] == 0
    assert pd.isna(t.loc["vazio", "truncado_prs"])
