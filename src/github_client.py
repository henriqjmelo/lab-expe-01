import requests

from src.config import GITHUB_TOKEN

GRAPHQL_URL = "https://api.github.com/graphql"


def run_query(query: str, variables: dict | None = None) -> dict:
    response = requests.post(
        GRAPHQL_URL,
        json={"query": query, "variables": variables or {}},
        headers={"Authorization": f"Bearer {GITHUB_TOKEN}"},
    )
    response.raise_for_status()
    payload = response.json()

    if "errors" in payload:
        raise RuntimeError(payload["errors"])

    return payload["data"]
