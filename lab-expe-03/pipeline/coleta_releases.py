from __future__ import annotations

from metricas.lead_time import ReleaseComCommits
from pipeline.github_client import GitHubAPIError, GitHubClient

COMMITS_POR_PAGINA = 100


def listar_releases(cliente: GitHubClient, owner: str, repo: str) -> list[dict]:
    brutas = list(cliente.paginar(f"repos/{owner}/{repo}/releases"))
    return sorted(brutas, key=lambda r: r["published_at"] or "")


def listar_tags_com_data(cliente: GitHubClient, owner: str, repo: str) -> list[dict]:
    tags = list(cliente.paginar(f"repos/{owner}/{repo}/tags"))
    resultado = []
    for tag in tags:
        sha = tag["commit"]["sha"]
        commit = cliente.get(f"repos/{owner}/{repo}/commits/{sha}")
        resultado.append(
            {"name": tag["name"], "sha": sha, "data": commit["commit"]["author"]["date"]}
        )
    return resultado


def comparar_commits(
    cliente: GitHubClient, owner: str, repo: str, base: str, head: str
) -> list[str] | None:
    datas: list[str] = []
    pagina = 1
    while True:
        try:
            resultado = cliente.get(
                f"repos/{owner}/{repo}/compare/{base}...{head}",
                {"per_page": COMMITS_POR_PAGINA, "page": pagina},
            )
        except GitHubAPIError as erro:
            if erro.status == 404:
                return None
            raise
        commits = resultado.get("commits") or []
        datas.extend(commit["commit"]["author"]["date"] for commit in commits)
        if len(commits) < COMMITS_POR_PAGINA:
            return datas
        pagina += 1


def montar_releases_com_commits(
    cliente: GitHubClient, owner: str, repo: str, releases: list[dict] | None = None
) -> list[ReleaseComCommits]:
    publicadas = [r for r in (releases or listar_releases(cliente, owner, repo)) if not r["draft"]]

    montadas = []
    for indice, release in enumerate(publicadas):
        if indice == 0:
            montadas.append(ReleaseComCommits(release["tag_name"], release["published_at"], ignorada=True))
            continue
        anterior = publicadas[indice - 1]
        datas = comparar_commits(cliente, owner, repo, anterior["tag_name"], release["tag_name"])
        if datas is None:
            montadas.append(ReleaseComCommits(release["tag_name"], release["published_at"], ignorada=True))
        else:
            montadas.append(ReleaseComCommits(release["tag_name"], release["published_at"], datas))
    return montadas
