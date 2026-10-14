from __future__ import annotations

import pytest

from metricas.colaboracao import (
    Deployment,
    PullRequest,
    eh_producao,
    metricas_bugs,
    metricas_deploys,
    metricas_prs,
    resultado_deploy,
)


def test_metricas_prs():
    prs = [
        PullRequest("merged", "2025-03-01T00:00:00Z", merged_at="2025-03-01T10:00:00Z",
                    primeira_resposta_at="2025-03-01T02:00:00Z"),
        PullRequest("merged", "2025-03-02T00:00:00Z", merged_at="2025-03-03T06:00:00Z"),
        PullRequest("closed", "2025-03-04T00:00:00Z", closed_at="2025-03-05T00:00:00Z",
                    primeira_resposta_at="2025-03-04T04:00:00Z"),
    ]
    r = metricas_prs(prs, semanas=2)
    assert r["n_prs_mergeados"] == 2
    assert r["prs_mergeados_semana"] == pytest.approx(1)
    assert r["lt_pr_mediana_horas"] == pytest.approx((10 + 30) / 2)
    assert r["primeira_resposta_mediana_horas"] == pytest.approx(3)
    assert r["prop_prs_sem_resposta"] == pytest.approx(1 / 3)
    assert r["taxa_aceitacao_pr"] == pytest.approx(2 / 3)


def test_metricas_prs_sem_dados():
    r = metricas_prs([], semanas=0)
    assert r["prs_mergeados_semana"] is None and r["lt_pr_mediana_horas"] is None
    assert r["taxa_aceitacao_pr"] is None and r["prop_prs_sem_resposta"] is None


def test_resposta_antes_da_abertura_conta_como_zero():
    pr = PullRequest("merged", "2025-03-01T10:00:00Z", merged_at="2025-03-01T12:00:00Z",
                     primeira_resposta_at="2025-03-01T09:00:00Z")
    assert metricas_prs([pr], 1)["primeira_resposta_mediana_horas"] == 0


def test_metricas_bugs():
    issues = [
        ("2025-03-01T00:00:00Z", "2025-03-02T00:00:00Z", True),
        ("2025-03-01T00:00:00Z", "2025-03-01T06:00:00Z", True),
        ("2025-03-01T00:00:00Z", "2025-03-10T00:00:00Z", False),
    ]
    assert metricas_bugs(issues) == {"n_bugs_fechados": 2, "resolucao_bug_mediana_horas": pytest.approx(15)}
    assert metricas_bugs([])["resolucao_bug_mediana_horas"] is None


@pytest.mark.parametrize("ambiente, esperado", [
    ("production", True), ("Production – web", True), ("github-pages", True), ("release", True),
    ("staging", False), ("preview", False), ("pr-123", False), ("dev", False), ("", False),
])
def test_eh_producao(ambiente, esperado):
    assert eh_producao(ambiente) is esperado


@pytest.mark.parametrize("state, status, esperado", [
    ("ACTIVE", "SUCCESS", "sucesso"), ("INACTIVE", "", "sucesso"), ("FAILURE", "", "falha"),
    ("ACTIVE", "ERROR", "falha"), ("PENDING", "QUEUED", None), ("ABANDONED", "", None),
])
def test_resultado_deploy(state, status, esperado):
    assert resultado_deploy(Deployment("2025-01-01T00:00:00Z", "production", state, status)) == esperado


def test_metricas_deploys_com_recuperacao_por_ambiente():
    d = lambda dia, estado, amb="production": Deployment(f"2025-03-{dia:02d}T00:00:00Z", amb, estado)  # noqa: E731
    deploys = [d(1, "ACTIVE"), d(2, "FAILURE"), d(3, "FAILURE"), d(4, "ACTIVE"), d(5, "ACTIVE"),
               d(6, "ACTIVE", "staging"), d(7, "PENDING")]
    r = metricas_deploys(deploys, semanas=1)
    assert r["n_deploys_producao"] == 6
    assert r["usa_deployments"] is True
    assert r["df_deploy_semana"] == pytest.approx(6)
    assert r["cfr_d_deploy"] == pytest.approx(2 / 5)
    assert r["recuperacao_deploy_mediana_horas"] == pytest.approx(48)


def test_poucos_deploys_nao_tem_cobertura():
    r = metricas_deploys([Deployment("2025-03-01T00:00:00Z", "production", "ACTIVE")], semanas=1)
    assert r["usa_deployments"] is False
    assert r["df_deploy_semana"] is None and r["cfr_d_deploy"] is None
