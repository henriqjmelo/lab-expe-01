from __future__ import annotations

import pandas as pd

from validacao.avaliacao_heuristica import avaliar_todas_as_versoes, avaliar_versao, escolher_melhor_versao
from validacao.comparar_versoes import marcacoes_por_release


def releases_df(linhas):
    return pd.DataFrame(linhas, columns=["owner", "repo", "tag_name", "published_at", "prerelease"])


def commits_df(linhas):
    return pd.DataFrame(linhas, columns=["owner", "repo", "tag_name", "mensagem"])


def consenso_df(linhas):
    return pd.DataFrame(linhas, columns=["owner", "repo", "tag_name", "corretiva"])


def test_avaliar_versao_com_gabarito_perfeito_da_f1_um():
    marcacoes = pd.DataFrame([
        {"owner": "d", "repo": "r", "tag_name": "v1.0.1", "marcada": True},
        {"owner": "d", "repo": "r", "tag_name": "v1.1.0", "marcada": False},
    ])
    consenso = consenso_df([
        ("d", "r", "v1.0.1", "sim"),
        ("d", "r", "v1.1.0", "nao"),
    ])

    r = avaliar_versao(marcacoes, consenso)

    assert r["precisao"] == 1.0
    assert r["recall"] == 1.0
    assert r["f1"] == 1.0
    assert r["n"] == 2


def test_avaliar_versao_so_falso_positivo_derruba_precisao():
    marcacoes = pd.DataFrame([
        {"owner": "d", "repo": "r", "tag_name": "v1.0.1", "marcada": True},
        {"owner": "d", "repo": "r", "tag_name": "v1.1.0", "marcada": True},
    ])
    consenso = consenso_df([
        ("d", "r", "v1.0.1", "sim"),
        ("d", "r", "v1.1.0", "nao"),
    ])

    r = avaliar_versao(marcacoes, consenso)

    assert r["precisao"] == 0.5
    assert r["recall"] == 1.0


def test_avaliar_versao_releases_fora_do_consenso_nao_entram():
    marcacoes = pd.DataFrame([
        {"owner": "d", "repo": "r", "tag_name": "v1.0.1", "marcada": True},
        {"owner": "d", "repo": "r", "tag_name": "v9.9.9", "marcada": True},  # nao sorteada na amostra-ouro
    ])
    consenso = consenso_df([("d", "r", "v1.0.1", "sim")])

    r = avaliar_versao(marcacoes, consenso)

    assert r["n"] == 1


def test_avaliar_versao_sem_intersecao_devolve_none():
    marcacoes = pd.DataFrame([{"owner": "d", "repo": "r", "tag_name": "v1.0.1", "marcada": True}])
    consenso = consenso_df([("outro", "r2", "v1.0.1", "sim")])

    r = avaliar_versao(marcacoes, consenso)

    assert r["n"] == 0
    assert r["f1"] is None


def test_avaliar_todas_as_versoes_devolve_uma_linha_por_versao_com_flag_de_f1_minimo():
    releases = releases_df([
        ("d", "r", "v1.0.0", "2025-11-01T00:00:00Z", False),
        ("d", "r", "v1.0.1", "2025-11-05T00:00:00Z", False),
    ])
    commits = commits_df([("d", "r", "v1.0.1", "fix: corrige bug")])
    consenso = consenso_df([("d", "r", "v1.0.1", "sim")])

    tabela = avaliar_todas_as_versoes(releases, commits, consenso)

    assert len(tabela) == 4
    assert "atinge_f1_minimo" in tabela.columns
    assert tabela["atinge_f1_minimo"].dtype == bool


def test_escolher_melhor_versao_pega_o_maior_f1():
    tabela = pd.DataFrame([
        {"versao": "v0", "f1": 0.5},
        {"versao": "v1", "f1": 0.9},
        {"versao": "v2", "f1": 0.3},
    ])

    assert escolher_melhor_versao(tabela) == "v1"


def test_marcacoes_por_release_usa_a_release_anterior_correta():
    # garante que a integracao marcacoes_por_release -> avaliar_versao funciona de ponta a ponta
    releases = releases_df([
        ("d", "r", "v1.0.0", "2025-11-01T00:00:00Z", False),
        ("d", "r", "v1.0.1", "2025-11-05T00:00:00Z", False),
        ("d", "r", "v1.1.0", "2025-12-01T00:00:00Z", False),
    ])
    from metricas.corretiva import VERSOES

    marcacoes = marcacoes_por_release(releases, commits_df([]), VERSOES["v0_semver_patch"])

    por_tag = marcacoes.set_index("tag_name")["marcada"]
    assert bool(por_tag["v1.0.0"]) is False  # primeira release, sem anterior
    assert bool(por_tag["v1.0.1"]) is True  # patch sobre v1.0.0
    assert bool(por_tag["v1.1.0"]) is False  # minor, nao e patch
