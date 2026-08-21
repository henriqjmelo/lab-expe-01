"""Exporta um snapshot dos cards do GitHub Projects v2."""

from src.export_csv import export_to_csv
from src.github_client import run_query


PROJECT_QUERY = """
query {
  user(login: "henriqjmelo") {
    projectV2(number: 1) {
      items(first: 20) {
        nodes {
          content {
            ... on Issue {
              number
              title
            }
          }
          fieldValueByName(name: "Status") {
            ... on ProjectV2ItemFieldSingleSelectValue {
              name
            }
          }
        }
      }
    }
  }
}
"""


def fetch_snapshot() -> list[dict]:
    data = run_query(PROJECT_QUERY)
    project = data["user"]["projectV2"]
    if project is None:
        raise RuntimeError("Projeto v2 #1 não encontrado para o usuário henriqjmelo.")

    snapshot = []
    for item in project["items"]["nodes"]:
        content = item.get("content") or {}
        if "number" not in content:
            continue
        status = item.get("fieldValueByName") or {}
        snapshot.append(
            {
                "number": content["number"],
                "title": content["title"],
                "status": status.get("name", ""),
            }
        )
    return snapshot


if __name__ == "__main__":
    rows = fetch_snapshot()
    export_to_csv(rows, "data/snapshot.csv")
    print(f"Exportados {len(rows)} cards para data/snapshot.csv")