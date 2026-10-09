"""Coleta de releases, tags e commits entre releases (issue #135).

Usa o GitHubClient de pipeline/github_client.py (issue #136) para paginacao,
rate limit e backoff. Este modulo so monta os dados; quem calcula o lead time
e metricas/lead_time.py, que nao depende de rede e e testado isoladamente.

A execucao real sobre os 100 repositorios da amostra depende do cache e da
retomada da issue #136 (ainda nao prontos): sem eles, repetir a coleta depois
de uma queda refaz chamadas que ja tinham sido gastas na cota de rate limit.
"""

from __future__ import annotations

from metricas.lead_time import ReleaseComCommits
from pipeline.github_client import GitHubAPIError, GitHubClient

# Sem paginar o compare, o endpoint para em 250 commits (ver issue #135).
COMMITS_POR_PAGINA = 100


def listar_releases(cliente: GitHubClient, owner: str, repo: str) -> list[dict]:
    """GET /repos/{owner}/{repo}/releases, ordenadas da mais antiga pra mais nova."""
    brutas = list(cliente.paginar(f"repos/{owner}/{repo}/releases"))
    return sorted(brutas, key=lambda r: r["published_at"] or "")


def listar_tags_com_data(cliente: GitHubClient, owner: str, repo: str) -> list[dict]:
    """GET /repos/{owner}/{repo}/tags. Tags nao tem data propria (RQ 07): usa a
    data do commit apontado, via GET /repos/{owner}/{repo}/commits/{sha}."""
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
    """GET /repos/{owner}/{repo}/compare/{base}...{head}, paginado por page/per_page.

    Devolve as datas de commit.author.date de cada commit entre base e head, ou
    None se a comparacao der 404 (tag apagada ou reescrita - issue #135 pede pra
    registrar e contar, nao propagar o erro)."""
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
    """Monta a lista que metricas/lead_time.py consome: uma entrada por release
    publicada, com os commits desde a release anterior.

    A primeira release da historia e marcada como ignorada (nao ha release
    anterior pra comparar), igual uma comparacao que devolveu 404.
    """
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
