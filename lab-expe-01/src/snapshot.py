"""
Exporta um snapshot dos cards do GitHub Projects v2.

Cada execução gera um arquivo com data (não sobrescreve o anterior),
já que os snapshots precisam se acumular sprint a sprint — é a única
forma de preservar histórico de mudança de coluna, já que a API do
Projects v2 não expõe isso diretamente.
"""

from datetime import date

from src.export_csv import export_to_csv
from src.github_client import run_query


PROJECT_QUERY = """
query($after: String) {
  user(login: "henriqjmelo") {
    projectV2(number: 1) {
      items(first: 20, after: $after) {
        pageInfo {
          hasNextPage
          endCursor
        }
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
    snapshot = []
    cursor = None

    while True:
        data = run_query(PROJECT_QUERY, {"after": cursor})
        project = data["user"]["projectV2"]
        if project is None:
            raise RuntimeError("Projeto v2 #1 não encontrado para o usuário henriqjmelo.")

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

        page_info = project["items"]["pageInfo"]
        if not page_info["hasNextPage"]:
            break
        cursor = page_info["endCursor"]

    return snapshot


if __name__ == "__main__":
    path = f"data/snapshot_{date.today().isoformat()}.csv"
    rows = fetch_snapshot()
    export_to_csv(rows, path)
    print(f"Exportados {len(rows)} cards para {path}")