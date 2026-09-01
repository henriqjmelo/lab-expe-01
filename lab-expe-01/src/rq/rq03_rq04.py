"""
RQ03 — Sistemas populares lançam releases com frequência?
        Métrica: total de releases publicadas

RQ04 — Sistemas populares são atualizados com frequência?
        Métrica: data do último push (pushedAt) — o tempo até a última
        atualização é calculado a partir desse dado bruto na fase de análise.
"""

from src.github_client import run_query

SAMPLE_QUERY = """
query($searchQuery: String!, $first: Int!) {
  search(query: $searchQuery, type: REPOSITORY, first: $first) {
    nodes {
      ... on Repository {
        nameWithOwner
        stargazerCount
        pushedAt
        releases {
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
    for repo in fetch_sample():
        print(
            f"{repo['nameWithOwner']:<40} "
            f"stars={repo['stargazerCount']:<8} "
            f"releases={repo['releases']['totalCount']:<5} "
            f"pushedAt={repo['pushedAt']}"
        )
