"""Valida nulos, outliers e consistencia das metricas de RQ05 e RQ06."""

import csv
import statistics
from collections import Counter


DATA_PATH = "data/repositorios.csv"


def load_rows(path: str = DATA_PATH) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def _report_count_metric(rows: list[dict], field: str, label: str) -> None:
    values = [int(row[field]) for row in rows if row[field] not in ("", None)]
    nulls = len(rows) - len(values)
    quartiles = statistics.quantiles(values, n=4)
    q1, q3 = quartiles[0], quartiles[2]
    upper_bound = q3 + 1.5 * (q3 - q1)
    outliers = [value for value in values if value > upper_bound]

    print(f"--- {label} ({field}) ---")
    print(f"nulos: {nulls}/{len(rows)}")
    print(f"min={min(values)} max={max(values)} mediana={statistics.median(values)}")
    print(f"outliers (> {upper_bound:.1f}, limite IQR): {len(outliers)} repositorios")


def validate_primary_language(rows: list[dict]) -> None:
    values = [row["primaryLanguage"] for row in rows if row["primaryLanguage"] not in ("", None)]
    nulls = len(rows) - len(values)

    print("--- RQ05 (primaryLanguage) ---")
    print(f"nulos: {nulls}/{len(rows)}")
    print(f"linguagens distintas: {len(set(values))}")
    print(f"mais frequentes: {Counter(values).most_common(10)}")


def validate_issues(rows: list[dict]) -> None:
    pairs = [
        (int(row["closedIssues"]), int(row["totalIssues"]))
        for row in rows
        if row["closedIssues"] not in ("", None) and row["totalIssues"] not in ("", None)
    ]
    null_closed = sum(1 for row in rows if row["closedIssues"] in ("", None))
    null_total = sum(1 for row in rows if row["totalIssues"] in ("", None))
    invalid_order = sum(1 for closed_value, total_value in pairs if closed_value > total_value)
    zero_total = sum(1 for _, total_value in pairs if total_value == 0)
    ratios = [closed_value / total_value for closed_value, total_value in pairs if total_value > 0]

    print("--- RQ06 (issues fechadas/total) ---")
    print(f"nulos closedIssues: {null_closed}/{len(rows)}")
    print(f"nulos totalIssues: {null_total}/{len(rows)}")
    print(f"closedIssues > totalIssues: {invalid_order}")
    print(f"totalIssues igual a zero: {zero_total}")
    if ratios:
        print(f"razao mediana: {statistics.median(ratios):.4f}")
    else:
        print("razao mediana: sem dados (todos os repositórios têm totalIssues igual a zero)")

    _report_count_metric(rows, "closedIssues", "RQ06 issues fechadas")
    _report_count_metric(rows, "totalIssues", "RQ06 issues totais")


if __name__ == "__main__":
    rows = load_rows()
    print(f"Total de repositorios: {len(rows)}\n")
    validate_primary_language(rows)
    print()
    validate_issues(rows)