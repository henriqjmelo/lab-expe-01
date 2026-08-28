from __future__ import annotations

import time

import requests

from src.config import GITHUB_TOKEN

GRAPHQL_URL = "https://api.github.com/graphql"
RETRYABLE_STATUS_CODES = {502, 503, 504}
MAX_RETRIES = 5


def run_query(query: str, variables: dict | None = None) -> dict:
    attempt = 0
    while True:
        response = requests.post(
            GRAPHQL_URL,
            json={"query": query, "variables": variables or {}},
            headers={"Authorization": f"Bearer {GITHUB_TOKEN}"},
        )

        if response.status_code in RETRYABLE_STATUS_CODES and attempt < MAX_RETRIES:
            attempt += 1
            time.sleep(2**attempt)  # 2s, 4s, 8s, 16s, 32s
            continue

        response.raise_for_status()
        break

    payload = response.json()

    if "errors" in payload:
        if not payload.get("data"):
            raise RuntimeError(payload["errors"])
        print(f"Aviso: resposta GraphQL com erros parciais: {payload['errors']}")

    return payload["data"]
