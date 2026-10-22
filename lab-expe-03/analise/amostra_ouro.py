from __future__ import annotations

import argparse
import random
from pathlib import Path

import pandas as pd


def sortear_repositorios(repositorios: pd.DataFrame, n: int = 60, semente: int = 42) -> pd.DataFrame:
    if len(repositorios) < n:
        raise ValueError(f"A amostra contém {len(repositorios)} repositórios; são necessários {n}.")
    resultado = repositorios.sample(n=n, random_state=semente).copy()
    resultado["full_name"] = resultado["owner"].astype(str) + "/" + resultado["repo"].astype(str)
    resultado["url"] = "https://github.com/" + resultado["full_name"]
    colunas = [coluna for coluna in ("full_name", "url", "linguagem", "estrelas") if coluna in resultado]
    return resultado[colunas].reset_index(drop=True)


def sortear_releases(
    repositorios: pd.DataFrame,
    releases: pd.DataFrame,
    commits: pd.DataFrame,
    limite: int = 5,
    semente: int = 42,
) -> pd.DataFrame:
    elegiveis = releases[releases["na_janela"].astype(bool) & ~releases["prerelease"].astype(bool)].copy()
    elegiveis = elegiveis.sort_values(["published_at", "owner", "repo", "tag_name"])
    selecionadas = []
    for _, repositorio in repositorios.iterrows():
        if "owner" in repositorio and "repo" in repositorio:
            owner, repo = repositorio["owner"], repositorio["repo"]
        else:
            owner, repo = repositorio["full_name"].split("/", maxsplit=1)
        disponiveis = elegiveis[(elegiveis["owner"] == owner) & (elegiveis["repo"] == repo)]
        tags = disponiveis["tag_name"].tolist()
        escolhidas = tags if len(tags) <= limite else random.Random(semente).sample(tags, limite)
        por_tag = disponiveis.drop_duplicates("tag_name").set_index("tag_name")
        selecionadas.extend(por_tag.loc[escolhidas].reset_index().to_dict("records"))
    resultado = pd.DataFrame(selecionadas)
    if resultado.empty:
        return pd.DataFrame(columns=["full_name", "tag_name", "url", "published_at", "n_commits", "n_reverts", "commits"])
    commits_escolhidos = commits.merge(resultado[["owner", "repo", "tag_name"]], on=["owner", "repo", "tag_name"])
    agrupados = []
    for chave, grupo in commits_escolhidos.groupby(["owner", "repo", "tag_name"], sort=False):
        mensagens = grupo["mensagem"].fillna("").astype(str).tolist()
        trecho = " · ".join(mensagens[:20])
        if len(mensagens) > 20:
            trecho += f" · [+{len(mensagens) - 20} commits]"
        agrupados.append({
            "owner": chave[0], "repo": chave[1], "tag_name": chave[2],
            "n_commits": len(grupo), "n_reverts": int(grupo["reverte_sha"].fillna("").astype(str).str.strip().ne("").sum()),
            "commits": trecho,
        })
    resumo_commits = pd.DataFrame(
        agrupados, columns=["owner", "repo", "tag_name", "n_commits", "n_reverts", "commits"]
    )
    resultado = resultado.merge(resumo_commits, on=["owner", "repo", "tag_name"], how="left")
    resultado["full_name"] = resultado["owner"].astype(str) + "/" + resultado["repo"].astype(str)
    resultado["url"] = "https://github.com/" + resultado["full_name"] + "/releases/tag/" + resultado["tag_name"].astype(str)
    resultado["n_commits"] = resultado["n_commits"].fillna(0).astype(int)
    resultado["n_reverts"] = resultado["n_reverts"].fillna(0).astype(int)
    return resultado[["full_name", "tag_name", "url", "published_at", "n_commits", "n_reverts", "commits"]]


def _criar_se_nao_existe(caminho: Path, df: pd.DataFrame, sobrescrever: bool) -> None:
    if caminho.exists() and not sobrescrever:
        return
    caminho.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(caminho, index=False)


def gerar(
    dataset_path: Path = Path("data/dataset_dora.csv"),
    releases_path: Path = Path("data/eventos/releases.csv"),
    commits_path: Path = Path("data/eventos/commits_releases.csv.gz"),
    saida: Path = Path("validacao"),
    sobrescrever: bool = False,
) -> list[Path]:
    dataset = pd.read_csv(dataset_path)
    repositorios = sortear_repositorios(dataset)
    releases = sortear_releases(repositorios, pd.read_csv(releases_path), pd.read_csv(commits_path))
    modelo_repos = repositorios.copy()
    modelo_repos.insert(1, "tipo_projeto", "")
    modelo_repos.insert(2, "releases_reais", "")
    modelo_releases = releases.copy()
    modelo_releases.insert(2, "corretiva", "")
    arquivos = {
        "amostra_ouro_repos.csv": repositorios,
        "amostra_ouro_releases.csv": releases,
        "modelo_rotulos_repos.csv": modelo_repos,
        "modelo_rotulos_releases.csv": modelo_releases,
    }
    destinos = []
    for nome, dados in arquivos.items():
        destino = saida / nome
        _criar_se_nao_existe(destino, dados, sobrescrever)
        destinos.append(destino)
    for nome in ("henrique", "gabriel", "guilherme"):
        for dimensao, modelo in (("repos", modelo_repos), ("releases", modelo_releases)):
            destino = saida / f"rotulos_{nome}_{dimensao}.csv"
            _criar_se_nao_existe(destino, modelo, sobrescrever)
            destinos.append(destino)
    return destinos


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m analise.amostra_ouro")
    parser.add_argument("--dataset", type=Path, default=Path("data/dataset_dora.csv"))
    parser.add_argument("--releases", type=Path, default=Path("data/eventos/releases.csv"))
    parser.add_argument("--commits", type=Path, default=Path("data/eventos/commits_releases.csv.gz"))
    parser.add_argument("--saida", type=Path, default=Path("validacao"))
    parser.add_argument("--sobrescrever", action="store_true")
    args = parser.parse_args(argv)
    for caminho in gerar(args.dataset, args.releases, args.commits, args.saida, args.sobrescrever):
        print(caminho)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())