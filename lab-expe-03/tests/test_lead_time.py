from __future__ import annotations

from metricas.lead_time import ReleaseComCommits, lead_time_por_commit, lead_time_por_release


def test_exemplo_do_enunciado():
    release = ReleaseComCommits(
        tag_name="v1.1",
        published_at="2024-03-15T00:00:00Z",
        commits_datas=[
            "2024-03-02T00:00:00Z",
            "2024-03-10T00:00:00Z",
            "2024-03-14T00:00:00Z",
        ],
    )

    por_release = lead_time_por_release([release])
    assert por_release["n_releases"] == 1
    assert por_release["mediana_dias"] == 13

    por_commit = lead_time_por_commit([release])
    assert por_commit["n_commits"] == 3
    assert por_commit["mediana_dias"] == 5


def test_primeira_release_da_historia_e_ignorada():
    primeira = ReleaseComCommits("v1.0", "2024-01-10T00:00:00Z", ignorada=True)

    assert lead_time_por_release([primeira])["n_releases"] == 0
    assert lead_time_por_release([primeira])["releases_ignoradas"] == 1
    assert lead_time_por_commit([primeira])["n_commits"] == 0


def test_release_sem_commits_novos_fica_fora_da_mediana_mas_e_contada():
    sem_commits = ReleaseComCommits("v1.2", "2024-04-01T00:00:00Z", commits_datas=[])
    com_commits = ReleaseComCommits(
        "v1.3", "2024-04-10T00:00:00Z", commits_datas=["2024-04-05T00:00:00Z"]
    )

    resultado = lead_time_por_release([sem_commits, com_commits])
    assert resultado["n_releases"] == 1
    assert resultado["releases_sem_commits_novos"] == 1
    assert resultado["mediana_dias"] == 5


def test_comparacao_404_marca_ignorada_e_nao_entra_na_mediana():
    ignorada = ReleaseComCommits("v2.0", "2024-05-01T00:00:00Z", ignorada=True)

    resultado = lead_time_por_release([ignorada])
    assert resultado["n_releases"] == 0
    assert resultado["releases_ignoradas"] == 1
    assert lead_time_por_commit([ignorada])["n_commits"] == 0


def test_mediana_do_repositorio_entre_varias_releases():
    releases = [
        ReleaseComCommits("v1", "2024-01-20T00:00:00Z", ["2024-01-10T00:00:00Z"]),
        ReleaseComCommits("v2", "2024-02-20T00:00:00Z", ["2024-02-05T00:00:00Z"]),
        ReleaseComCommits("v3", "2024-03-20T00:00:00Z", ["2024-03-19T00:00:00Z"]),
    ]

    assert lead_time_por_release(releases)["mediana_dias"] == 10


def test_sem_releases_validas_mediana_e_none():
    resultado = lead_time_por_release([])
    assert resultado["n_releases"] == 0
    assert resultado["mediana_dias"] is None
