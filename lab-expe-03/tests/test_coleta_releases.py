"""Testes de pipeline/coleta_releases.py (issue #135).

Usa um cliente falso no lugar do GitHubClient real: os testes nao fazem
chamada de rede, so verificam como o modulo monta as releases a partir das
respostas da API (paginacao do compare, 404, release sem anterior).
"""

from __future__ import annotations

import pytest

from pipeline.coleta_releases import (
    comparar_commits,
    listar_releases,
    listar_tags_com_data,
    montar_releases_com_commits,
)
from pipeline.github_client import GitHubAPIError


class ClienteFalso:
    """paginar() devolve o que foi programado por caminho; get() segue a mesma
    logica, mas pode levantar GitHubAPIError pra simular um 404 do compare."""

    def __init__(self, paginas: dict[str, list] | None = None, gets: dict | None = None):
        self.paginas = paginas or {}
        self.gets = gets or {}
        self.chamadas_get: list[tuple[str, dict | None]] = []

    def paginar(self, caminho: str, params=None, *, chave=None):
        yield from self.paginas.get(caminho, [])

    def get(self, caminho: str, params: dict | None = None):
        self.chamadas_get.append((caminho, params))
        resposta = self.gets.get(caminho)
        if isinstance(resposta, Exception):
            raise resposta
        if callable(resposta):
            return resposta(params)
        return resposta


def test_listar_releases_ordena_por_data_de_publicacao():
    cliente = ClienteFalso(
        paginas={
            "repos/o/r/releases": [
                {"tag_name": "v2", "published_at": "2024-02-01T00:00:00Z", "draft": False},
                {"tag_name": "v1", "published_at": "2024-01-01T00:00:00Z", "draft": False},
            ]
        }
    )

    releases = listar_releases(cliente, "o", "r")
    assert [r["tag_name"] for r in releases] == ["v1", "v2"]


def test_listar_tags_busca_a_data_do_commit_apontado():
    cliente = ClienteFalso(
        paginas={"repos/o/r/tags": [{"name": "v1", "commit": {"sha": "abc123"}}]},
        gets={
            "repos/o/r/commits/abc123": {
                "commit": {"author": {"date": "2024-01-05T00:00:00Z"}}
            }
        },
    )

    tags = listar_tags_com_data(cliente, "o", "r")
    assert tags == [{"name": "v1", "sha": "abc123", "data": "2024-01-05T00:00:00Z"}]


def test_comparar_commits_segue_paginacao_ate_a_pagina_incompleta():
    # Sem paginar, o compare para em 250 commits (ver issue #135): o modulo
    # precisa continuar pedindo pagina enquanto a pagina voltar cheia.
    pagina_1 = {"commits": [{"commit": {"author": {"date": f"2024-01-{d:02d}T00:00:00Z"}}} for d in range(1, 101)]}
    pagina_2 = {"commits": [{"commit": {"author": {"date": "2024-02-01T00:00:00Z"}}}]}

    def get(params):
        return pagina_1 if params["page"] == 1 else pagina_2

    cliente = ClienteFalso(gets={"repos/o/r/compare/v1...v2": get})

    datas = comparar_commits(cliente, "o", "r", "v1", "v2")
    assert len(datas) == 101
    assert datas[-1] == "2024-02-01T00:00:00Z"


def test_comparar_commits_404_devolve_none():
    cliente = ClienteFalso(
        gets={"repos/o/r/compare/apagada...v2": GitHubAPIError(404, "x", "Not Found")}
    )

    assert comparar_commits(cliente, "o", "r", "apagada", "v2") is None


def test_comparar_commits_propaga_outros_erros():
    cliente = ClienteFalso(gets={"repos/o/r/compare/v1...v2": GitHubAPIError(500, "x", "boom")})

    with pytest.raises(GitHubAPIError):
        comparar_commits(cliente, "o", "r", "v1", "v2")


def test_montar_releases_marca_a_primeira_como_ignorada():
    releases = [
        {"tag_name": "v1", "published_at": "2024-01-01T00:00:00Z", "draft": False},
        {"tag_name": "v2", "published_at": "2024-02-01T00:00:00Z", "draft": False},
    ]
    cliente = ClienteFalso(
        gets={
            "repos/o/r/compare/v1...v2": {
                "commits": [{"commit": {"author": {"date": "2024-01-15T00:00:00Z"}}}]
            }
        }
    )

    montadas = montar_releases_com_commits(cliente, "o", "r", releases)

    assert montadas[0].tag_name == "v1" and montadas[0].ignorada
    assert montadas[1].tag_name == "v2" and not montadas[1].ignorada
    assert montadas[1].commits_datas == ["2024-01-15T00:00:00Z"]


def test_montar_releases_com_uma_unica_release_so_tem_a_ignorada():
    releases = [{"tag_name": "v1", "published_at": "2024-01-01T00:00:00Z", "draft": False}]

    montadas = montar_releases_com_commits(ClienteFalso(), "o", "r", releases)

    assert len(montadas) == 1
    assert montadas[0].ignorada


def test_montar_releases_ignora_rascunhos():
    releases = [
        {"tag_name": "v1", "published_at": "2024-01-01T00:00:00Z", "draft": False},
        {"tag_name": "v2-rc", "published_at": "2024-01-15T00:00:00Z", "draft": True},
        {"tag_name": "v2", "published_at": "2024-02-01T00:00:00Z", "draft": False},
    ]
    cliente = ClienteFalso(gets={"repos/o/r/compare/v1...v2": {"commits": []}})

    montadas = montar_releases_com_commits(ClienteFalso(gets=cliente.gets), "o", "r", releases)

    assert [m.tag_name for m in montadas] == ["v1", "v2"]


def test_montar_releases_404_marca_ignorada_sem_propagar():
    releases = [
        {"tag_name": "v1", "published_at": "2024-01-01T00:00:00Z", "draft": False},
        {"tag_name": "v2", "published_at": "2024-02-01T00:00:00Z", "draft": False},
    ]
    cliente = ClienteFalso(
        gets={"repos/o/r/compare/v1...v2": GitHubAPIError(404, "x", "Not Found")}
    )

    montadas = montar_releases_com_commits(cliente, "o", "r", releases)

    assert montadas[1].ignorada
    assert montadas[1].commits_datas == []
