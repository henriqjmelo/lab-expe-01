"""Junta coleta_releases.py e metricas/lead_time.py numa linha de comando (issue #135).

Le uma lista de repositorios (owner,repo) de um CSV, calcula o lead time (a) e
(b) de cada um e grava o resultado em outro CSV. E o pedaco que falta pra ir
da funcao isolada ao "roda sobre os 100 repositorios da S01" do DoD da issue.

A execucao real sobre a amostra depende de:
    - lab-expe-03/data/repositorios.csv, gerado pela selecao da issue #134;
    - cache/retomada no GitHubClient da issue #136 (ainda nao existem) -
      sem eles, repetir a coleta apos uma queda refaz chamadas ja gastas.

Uso:
    python -m pipeline.executar_lead_time --repos data/repositorios.csv \
        --saida data/lead_time.csv
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from metricas.lead_time import lead_time_por_commit, lead_time_por_release
from pipeline.coleta_releases import montar_releases_com_commits
from pipeline.github_client import GitHubClient

CAMPOS_SAIDA = (
    "owner",
    "repo",
    "a_n_releases",
    "a_mediana_dias",
    "a_releases_sem_commits_novos",
    "a_releases_ignoradas",
    "b_n_commits",
    "b_mediana_dias",
)


def ler_repositorios(caminho: Path) -> list[tuple[str, str]]:
    """CSV com colunas owner,repo (uma linha por repositorio da amostra)."""
    with caminho.open(newline="", encoding="utf-8") as f:
        return [(linha["owner"], linha["repo"]) for linha in csv.DictReader(f)]


def lead_time_do_repositorio(cliente: GitHubClient, owner: str, repo: str) -> dict:
    releases = montar_releases_com_commits(cliente, owner, repo)
    a = lead_time_por_release(releases)
    b = lead_time_por_commit(releases)
    return {
        "owner": owner,
        "repo": repo,
        "a_n_releases": a["n_releases"],
        "a_mediana_dias": a["mediana_dias"],
        "a_releases_sem_commits_novos": a["releases_sem_commits_novos"],
        "a_releases_ignoradas": a["releases_ignoradas"],
        "b_n_commits": b["n_commits"],
        "b_mediana_dias": b["mediana_dias"],
    }


def coletar_lead_time(cliente: GitHubClient, repositorios: list[tuple[str, str]]) -> list[dict]:
    return [lead_time_do_repositorio(cliente, owner, repo) for owner, repo in repositorios]


def gravar_csv(caminho: Path, linhas: list[dict]) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS_SAIDA)
        w.writeheader()
        w.writerows(linhas)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--repos", type=Path, required=True, help="CSV com colunas owner,repo")
    ap.add_argument("--saida", type=Path, required=True, help="CSV de saida com o lead time")
    args = ap.parse_args()

    cliente = GitHubClient()
    repositorios = ler_repositorios(args.repos)
    linhas = coletar_lead_time(cliente, repositorios)
    gravar_csv(args.saida, linhas)
    print(f"{len(linhas)} repositorios processados -> {args.saida}")


if __name__ == "__main__":
    main()
