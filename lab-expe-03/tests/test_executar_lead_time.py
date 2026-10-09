"""Testes de pipeline/executar_lead_time.py (issue #135).

Usa o mesmo ClienteFalso de test_coleta_releases.py. Nao precisa de
GITHUB_TOKEN nem de rede: e so a orquestracao (ler repos -> calcular -> csv).
"""

from __future__ import annotations

import csv

from pipeline.executar_lead_time import (
    CAMPOS_SAIDA,
    coletar_lead_time,
    gravar_csv,
    ler_repositorios,
    lead_time_do_repositorio,
)
from tests.test_coleta_releases import ClienteFalso


def cliente_de_dois_repos() -> ClienteFalso:
    releases_o1 = [
        {"tag_name": "v1", "published_at": "2024-01-01T00:00:00Z", "draft": False},
        {"tag_name": "v2", "published_at": "2024-01-20T00:00:00Z", "draft": False},
    ]
    releases_o2 = [{"tag_name": "v1", "published_at": "2024-03-01T00:00:00Z", "draft": False}]
    return ClienteFalso(
        paginas={
            "repos/dono1/repo1/releases": releases_o1,
            "repos/dono2/repo2/releases": releases_o2,
        },
        gets={
            "repos/dono1/repo1/compare/v1...v2": {
                "commits": [{"commit": {"author": {"date": "2024-01-10T00:00:00Z"}}}]
            }
        },
    )


def test_ler_repositorios(tmp_path):
    caminho = tmp_path / "repos.csv"
    caminho.write_text("owner,repo\ndono1,repo1\ndono2,repo2\n", encoding="utf-8")

    assert ler_repositorios(caminho) == [("dono1", "repo1"), ("dono2", "repo2")]


def test_lead_time_do_repositorio_com_release_valida():
    resultado = lead_time_do_repositorio(cliente_de_dois_repos(), "dono1", "repo1")

    assert resultado["owner"] == "dono1"
    assert resultado["a_n_releases"] == 1
    assert resultado["a_mediana_dias"] == 10
    assert resultado["a_releases_ignoradas"] == 1  # v1 e a primeira da historia


def test_lead_time_do_repositorio_com_uma_unica_release():
    # dono2/repo2 so tem uma release: nao ha anterior pra comparar, fica tudo ignorado.
    resultado = lead_time_do_repositorio(cliente_de_dois_repos(), "dono2", "repo2")

    assert resultado["a_n_releases"] == 0
    assert resultado["a_mediana_dias"] is None
    assert resultado["b_n_commits"] == 0


def test_coletar_lead_time_processa_todos_os_repositorios():
    linhas = coletar_lead_time(cliente_de_dois_repos(), [("dono1", "repo1"), ("dono2", "repo2")])

    assert [l["repo"] for l in linhas] == ["repo1", "repo2"]


def test_gravar_csv_usa_os_campos_esperados(tmp_path):
    linhas = coletar_lead_time(cliente_de_dois_repos(), [("dono1", "repo1")])
    caminho = tmp_path / "saida" / "lead_time.csv"

    gravar_csv(caminho, linhas)

    with caminho.open(newline="", encoding="utf-8") as f:
        gravadas = list(csv.DictReader(f))
    assert gravadas[0].keys() == set(CAMPOS_SAIDA)
    assert gravadas[0]["owner"] == "dono1"
    assert float(gravadas[0]["a_mediana_dias"]) == 10
