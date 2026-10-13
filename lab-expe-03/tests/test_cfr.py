from __future__ import annotations

import pytest

from metricas.cfr import (
    FALHA,
    IGNORADO,
    SUCESSO,
    Deploy,
    cfr_ci,
    cfr_entrega,
    classificar_conclusao,
    corretiva_semver_patch,
    marcar_corretivas,
    versao_semver,
)

INICIO = "2025-01-01T00:00:00Z"
FIM = "2026-01-01T00:00:00Z"


@pytest.mark.parametrize(
    "conclusion, classe",
    [
        ("success", SUCESSO),
        ("failure", FALHA),
        ("timed_out", FALHA),
        ("startup_failure", FALHA),
        ("cancelled", IGNORADO),
        ("skipped", IGNORADO),
        ("neutral", IGNORADO),
        ("action_required", IGNORADO),
        ("stale", IGNORADO),
        (None, IGNORADO),
        ("", IGNORADO),
    ],
)
def test_classificacao_por_conclusion(conclusion, classe):
    assert classificar_conclusao(conclusion) == classe


def test_cfr_ci_ignora_cancelados_e_soma_todos_os_tipos_de_falha():
    r = cfr_ci(["success", "success", "failure", "timed_out", "cancelled", "skipped", None])
    assert r == {"n_validos": 4, "n_sucessos": 2, "n_falhas": 2, "n_ignorados": 3, "cfr": 0.5}


def test_cfr_ci_sem_runs_validos_e_none():
    assert cfr_ci(["cancelled", "skipped"])["cfr"] is None
    assert cfr_ci([])["cfr"] is None


@pytest.mark.parametrize(
    "tag, versao",
    [("v1.2.3", (1, 2, 3)), ("1.2", (1, 2, 0)), ("release-2.0.1", (2, 0, 1)), ("nightly", None)],
)
def test_versao_semver(tag, versao):
    assert versao_semver(tag) == versao


def test_corretiva_v0_so_quando_sobe_apenas_o_patch():
    v120 = Deploy("v1.2.0", "2025-03-01T00:00:00Z")
    assert corretiva_semver_patch(Deploy("v1.2.1", "x"), v120)
    assert not corretiva_semver_patch(Deploy("v1.3.0", "x"), v120)
    assert not corretiva_semver_patch(Deploy("v2.0.0", "x"), v120)
    assert not corretiva_semver_patch(Deploy("v1.2.1", "x"), None)
    assert not corretiva_semver_patch(Deploy("nightly", "x"), v120)


def test_marcar_corretivas_compara_com_o_deploy_anterior():
    deploys = [Deploy("v1.0.0", "a"), Deploy("v1.0.1", "b"), Deploy("v1.1.0", "c"), Deploy("v1.1.1", "d")]
    assert marcar_corretivas(deploys) == [False, True, False, True]


def test_cfr_entrega_release_seguida_de_corretiva_em_ate_7_dias_falhou():
    deploys = [
        Deploy("v1.0.0", "2025-03-01T00:00:00Z"),
        Deploy("v1.0.1", "2025-03-05T00:00:00Z"),
        Deploy("v1.1.0", "2025-04-01T00:00:00Z"),
        Deploy("v1.1.1", "2025-04-20T00:00:00Z"),
    ]
    r = cfr_entrega(deploys, INICIO, FIM)
    assert r["n_avaliadas"] == 4
    assert r["n_falharam"] == 1
    assert r["cfr"] == 0.25
    assert r["n_corretivas"] == 2


def test_cfr_entrega_censura_os_ultimos_7_dias_da_janela():
    deploys = [
        Deploy("v1.0.0", "2025-06-01T00:00:00Z"),
        Deploy("v1.1.0", "2025-12-28T00:00:00Z"),
    ]
    r = cfr_entrega(deploys, INICIO, FIM)
    assert r["n_avaliadas"] == 1
    assert r["n_censuradas"] == 1


def test_cfr_entrega_ignora_deploys_fora_da_janela_mas_usa_como_anterior():
    deploys = [
        Deploy("v1.0.0", "2024-12-30T00:00:00Z"),
        Deploy("v1.0.1", "2025-01-02T00:00:00Z"),
    ]
    r = cfr_entrega(deploys, INICIO, FIM)
    assert r["n_avaliadas"] == 1
    assert r["n_falharam"] == 0
    assert r["n_corretivas"] == 1


def test_cfr_entrega_sem_releases_avaliaveis_e_none():
    assert cfr_entrega([], INICIO, FIM)["cfr"] is None


def test_cfr_entrega_aceita_outra_heuristica():
    deploys = [Deploy("a", "2025-03-01T00:00:00Z"), Deploy("hotfix-b", "2025-03-02T00:00:00Z")]
    r = cfr_entrega(deploys, INICIO, FIM, heuristica=lambda d, _: "hotfix" in d.tag_name)
    assert r["n_falharam"] == 1
