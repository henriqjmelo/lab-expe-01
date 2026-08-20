"""
Exporta a lista de repositórios coletados para um arquivo .csv.

Achata campos aninhados do GraphQL (ex.: {"totalCount": 5} ou
{"name": "Python"}) em valores simples de coluna, para funcionar com
qualquer combinação de campos das RQs — não depende de saber de
antemão quais RQs já foram implementadas.
"""

import csv


def _flatten_value(value):
    if isinstance(value, dict):
        if "totalCount" in value:
            return value["totalCount"]
        if "name" in value:
            return value["name"]
        return value
    if value is None:
        return ""
    return value


def _flatten_repo(repo: dict) -> dict:
    return {key: _flatten_value(value) for key, value in repo.items()}


def export_to_csv(repos: list[dict], path: str) -> None:
    if not repos:
        raise ValueError("Lista de repositórios vazia — nada para exportar.")

    rows = [_flatten_repo(repo) for repo in repos]
    fieldnames = list(rows[0].keys())

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    from src.rq.rq03_rq04 import fetch_sample

    sample = fetch_sample(size=10)
    export_to_csv(sample, "data/sample_export.csv")
    print(f"Exportados {len(sample)} repositorios para data/sample_export.csv")
