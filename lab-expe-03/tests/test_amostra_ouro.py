import pandas as pd
from pathlib import Path

from analise.amostra_ouro import gerar, sortear_releases, sortear_repositorios


def test_sorteio_repositorios_e_reprodutivel():
    repos = pd.DataFrame({
        "owner": ["o"] * 70, "repo": [f"r{i}" for i in range(70)],
        "linguagem": ["Python"] * 70, "estrelas": range(70),
    })

    primeiro = sortear_repositorios(repos)
    segundo = sortear_repositorios(repos)

    pd.testing.assert_frame_equal(primeiro, segundo)
    assert len(primeiro) == 60


def test_sorteio_releases_respeita_janela_e_limite_por_repo():
    repos = pd.DataFrame({"owner": ["o", "o"], "repo": ["a", "b"]})
    releases = pd.DataFrame({
        "owner": ["o"] * 12, "repo": ["a"] * 6 + ["b"] * 6,
        "tag_name": [f"v{i}" for i in range(12)], "published_at": pd.date_range("2026-01-01", periods=12),
        "prerelease": [False] * 11 + [True], "na_janela": [True] * 11 + [False],
    })
    commits = pd.DataFrame({
        "owner": ["o"] * 12, "repo": ["a"] * 6 + ["b"] * 6,
        "tag_name": [f"v{i}" for i in range(12)], "mensagem": ["feat: exemplo"] * 12,
        "reverte_sha": [""] * 11 + ["abc"],
    })

    primeiro = sortear_releases(repos, releases, commits)
    segundo = sortear_releases(repos, releases, commits)

    pd.testing.assert_frame_equal(primeiro, segundo)
    assert primeiro.groupby("full_name").size().max() <= 5
    assert not primeiro["tag_name"].isin(["v11"]).any()


def test_geracao_cria_modelos_sem_substituir_arquivos_existentes(tmp_path: Path):
    dataset = pd.DataFrame({
        "owner": ["o"] * 60, "repo": [f"r{i}" for i in range(60)],
        "linguagem": ["Python"] * 60, "estrelas": range(60),
    })
    releases = pd.DataFrame({
        "owner": ["o"] * 60, "repo": [f"r{i}" for i in range(60)], "tag_name": ["v1"] * 60,
        "published_at": pd.date_range("2026-01-01", periods=60), "prerelease": [False] * 60,
        "na_janela": [True] * 60,
    })
    commits = pd.DataFrame({
        "owner": ["o"] * 60, "repo": [f"r{i}" for i in range(60)], "tag_name": ["v1"] * 60,
        "mensagem": ["feat: exemplo"] * 60, "reverte_sha": [""] * 60,
    })
    dataset_path, releases_path, commits_path = (tmp_path / nome for nome in ("dataset.csv", "releases.csv", "commits.csv.gz"))
    dataset.to_csv(dataset_path, index=False)
    releases.to_csv(releases_path, index=False)
    commits.to_csv(commits_path, index=False, compression="gzip")
    saida = tmp_path / "validacao"
    rotulos = saida / "rotulos_henrique_repos.csv"
    rotulos.parent.mkdir()
    rotulos.write_text("rotulos_humanos_preservados", encoding="utf-8")

    gerar(dataset_path, releases_path, commits_path, saida)

    assert rotulos.read_text(encoding="utf-8") == "rotulos_humanos_preservados"
    assert len(pd.read_csv(saida / "amostra_ouro_repos.csv")) == 60
    assert len(pd.read_csv(saida / "modelo_rotulos_releases.csv")) == 60