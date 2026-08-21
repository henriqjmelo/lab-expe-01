"""
RQ01 — Sistemas populares são maduros/antigos?
        Métrica: idade do repositório (calculado a partir de createdAt)

RQ02 — Sistemas populares recebem muita contribuição externa?
        Métrica: total de pull requests aceitas (MERGED)
"""

from src.github_client import run_query

SAMPLE_QUERY = """
query($searchQuery: String!, $first: Int!) {
  search(query: $searchQuery, type: REPOSITORY, first: $first) {
    nodes {
      ... on Repository {
        nameWithOwner
        stargazerCount
        createdAt
        pullRequests(states: MERGED) {
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
            f"createdAt={repo['createdAt']:<22} "
            f"mergedPRs={repo['pullRequests']['totalCount']}"
        )
