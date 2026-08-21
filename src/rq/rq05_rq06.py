"""
RQ05 — Sistemas populares são escritos nas linguagens mais populares?
        Métrica: linguagem primária do repositório.

RQ06 — Sistemas populares possuem um alto percentual de issues fechadas?
        Métricas: total de issues fechadas e total de issues.

Os campos retornados também permitem calcular o percentual de issues fechadas
e agrupar os resultados por linguagem na etapa de análise.
"""

from src.github_client import run_query


SAMPLE_QUERY = """
query($searchQuery: String!, $first: Int!) {
  search(query: $searchQuery, type: REPOSITORY, first: $first) {
    nodes {
      ... on Repository {
        nameWithOwner
        stargazerCount
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


def fetch_sample(size: int = 10) -> list[dict]:
    variables = {"searchQuery": "stars:>1 sort:stars-desc", "first": size}
    data = run_query(SAMPLE_QUERY, variables)
    return data["search"]["nodes"]


if __name__ == "__main__":
    from src.export_csv import export_to_csv

    sample = fetch_sample()
    export_to_csv(sample, "data/rq05_rq06_export.csv")
    print(f"Exportados {len(sample)} repositorios para data/rq05_rq06_export.csv")