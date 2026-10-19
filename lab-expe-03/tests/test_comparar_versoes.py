from __future__ import annotations

import pandas as pd

from metricas.cfr import Deploy, cfr_entrega
from metricas.corretiva import VERSOES
from validacao.comparar_versoes import INICIO, FIM, cfr_b_por_repositorio, resumo_por_versao


def releases_df(linhas: list[tuple[str, str, str, str, bool]]) -> pd.DataFrame:
    return pd.DataFrame(linhas, columns=["owner", "repo", "tag_name", "published_at", "prerelease"])


def commits_df(linhas: list[tuple[str, str, str, str]]) -> pd.DataFrame:
    return pd.DataFrame(linhas, columns=["owner", "repo", "tag_name", "mensagem"])


def test_cfr_b_por_repositorio_com_v0_bate_com_cfr_entrega_direto():
    # duas releases de dois repositorios: o resultado por repositorio tem que ser
    # identico a chamar cfr_entrega direto com os mesmos deploys e a v0
    releases = releases_df([
        ("dono1", "repo1", "v1.0.0", "2025-11-01T00:00:00Z", False),
        ("dono1", "repo1", "v1.0.1", "2025-11-05T00:00:00Z", False),
        ("dono1", "repo1", "v1.1.0", "2025-12-01T00:00:00Z", False),
        ("dono2", "repo2", "v2.0.0", "2025-10-10T00:00:00Z", False),
        ("dono2", "repo2", "v2.0.1", "2025-10-12T00:00:00Z", False),
    ])
    commits = commits_df([])

    tabela = cfr_b_por_repositorio(releases, commits, VERSOES["v0_semver_patch"], INICIO, FIM)

    esperado_repo1 = cfr_entrega(
        [Deploy("v1.0.0", "2025-11-01T00:00:00Z"), Deploy("v1.0.1", "2025-11-05T00:00:00Z"),
         Deploy("v1.1.0", "2025-12-01T00:00:00Z")],
        INICIO, FIM,
    )
    linha1 = tabela[(tabela.owner == "dono1") & (tabela.repo == "repo1")].iloc[0]
    assert linha1["cfr_b"] == esperado_repo1["cfr"]
    assert linha1["n_corretivas"] == esperado_repo1["n_corretivas"]


def test_cfr_b_por_repositorio_ignora_prerelease():
    releases = releases_df([
        ("dono1", "repo1", "v1.0.0", "2025-11-01T00:00:00Z", False),
        ("dono1", "repo1", "v1.0.1-rc1", "2025-11-03T00:00:00Z", True),
        ("dono1", "repo1", "v1.0.1", "2025-11-05T00:00:00Z", False),
    ])
    commits = commits_df([])

    tabela = cfr_b_por_repositorio(releases, commits, VERSOES["v0_semver_patch"], INICIO, FIM)

    linha = tabela[(tabela.owner == "dono1") & (tabela.repo == "repo1")].iloc[0]
    # so as 2 releases publicadas contam; a pre-release fica de fora e nao aparece
    # nem como avaliada nem como anterior de ninguem
    assert linha["n_avaliadas"] + linha["n_censuradas"] == 2


def test_cfr_b_por_repositorio_usa_mensagens_do_repositorio_certo():
    # dois repositorios com a mesma tag_name: as mensagens de um nao podem vazar pro outro
    releases = releases_df([
        ("dono1", "repo1", "v1.0.0", "2025-11-01T00:00:00Z", False),
        ("dono1", "repo1", "v1.0.1", "2025-11-05T00:00:00Z", False),
        ("dono2", "repo2", "v1.0.0", "2025-11-01T00:00:00Z", False),
        ("dono2", "repo2", "v1.0.1", "2025-11-05T00:00:00Z", False),
    ])
    commits = commits_df([
        ("dono1", "repo1", "v1.0.1", "fix: corrige bug"),
        ("dono2", "repo2", "v1.0.1", "feat: nova funcionalidade"),
    ])

    tabela = cfr_b_por_repositorio(releases, commits, VERSOES["v1_mensagens"], INICIO, FIM)

    r1 = tabela[(tabela.owner == "dono1") & (tabela.repo == "repo1")].iloc[0]
    r2 = tabela[(tabela.owner == "dono2") & (tabela.repo == "repo2")].iloc[0]
    assert r1["n_corretivas"] == 1
    assert r2["n_corretivas"] == 0


def test_resumo_por_versao_tem_uma_linha_por_versao():
    releases = releases_df([
        ("dono1", "repo1", "v1.0.0", "2025-11-01T00:00:00Z", False),
        ("dono1", "repo1", "v1.0.1", "2025-11-05T00:00:00Z", False),
    ])
    commits = commits_df([("dono1", "repo1", "v1.0.1", "fix: corrige bug")])

    resumo = resumo_por_versao(releases, commits)

    assert list(resumo["versao"]) == list(VERSOES)
