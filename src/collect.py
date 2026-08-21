"""
Coletor unificado (issue #6) — combina os campos de todas as RQs (01 a
06) numa única query GraphQL e pagina via cursor até atingir o número
de repositórios desejado.
"""

import time

import requests

from src.github_client import run_query

REPO_QUERY = """
query($searchQuery: String!, $first: Int!, $after: String) {
  search(query: $searchQuery, type: REPOSITORY, first: $first, after: $after) {
    pageInfo {
      hasNextPage
      endCursor
    }
    nodes {
      ... on Repository {
        nameWithOwner
        stargazerCount

        createdAt
        pullRequests(states: MERGED) {
          totalCount
        }

        releases {
          totalCount
        }
        pushedAt

        primaryLanguage {
          name
        }
        closedIssues: issues(states: CLOSED) {
          totalCount
        }
        totalIssues: issues {
          totalCount
        }
      }
    }
  }
}
"""

PAGE_SIZE = 20  # conservador: páginas maiores aumentam o risco de 502
MIN_PAGE_SIZE = 5  # piso ao encolher uma página que continua falhando


def _fetch_page(search_query: str, first: int, after: str | None) -> dict:
    """Busca uma página, encolhendo o tamanho se continuar levando 502
    mesmo após os retries automáticos do github_client (algum repositório
    específico naquela faixa deixa a query mais cara de processar)."""
    size = first
    while True:
        try:
            variables = {"searchQuery": search_query, "first": size, "after": after}
            return run_query(variables=variables, query=REPO_QUERY)["search"]
        except requests.exceptions.HTTPError:
            if size <= MIN_PAGE_SIZE:
                raise
            size = max(size // 2, MIN_PAGE_SIZE)
            time.sleep(2)


def collect_repositories(total: int = 100, delay: float = 2.0) -> list[dict]:
    """Coleta os `total` repositórios com mais estrelas, com os campos de RQ disponíveis."""
    repos: list[dict] = []
    cursor = None
    search_query = "stars:>1 sort:stars-desc"

    while len(repos) < total:
        page_size = min(PAGE_SIZE, total - len(repos))
        search = _fetch_page(search_query, page_size, cursor)

        repos.extend(search["nodes"])

        if not search["pageInfo"]["hasNextPage"]:
            break
        cursor = search["pageInfo"]["endCursor"]

        if len(repos) < total:
            time.sleep(delay)  # respeita rate limit da Search API (30 req/min)

    return repos


if __name__ == "__main__":
    import sys

    from src.export_csv import export_to_csv

    n = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    result = collect_repositories(total=n)
    export_to_csv(result, "data/repositorios.csv")
    print(f"Coletados {len(result)} repositorios -> data/repositorios.csv")
