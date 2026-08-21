"""
Validação de consistência dos dados de RQ03 (releases) e RQ04 (pushedAt)
no dataset completo (data/repositorios.csv) — checa nulos e outliers
antes da análise final (S03).
"""

import csv
import statistics
from datetime import datetime, timezone

DATA_PATH = "data/repositorios.csv"


def load_rows(path: str = DATA_PATH) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def validate_releases(rows: list[dict]) -> None:
    values = [int(r["releases"]) for r in rows if r["releases"] not in ("", None)]
    nulls = len(rows) - len(values)

    q1, q3 = statistics.quantiles(values, n=4)[0], statistics.quantiles(values, n=4)[2]
    iqr = q3 - q1
    upper_bound = q3 + 1.5 * iqr
    outliers = [v for v in values if v > upper_bound]

    print("--- RQ03 (releases) ---")
    print(f"nulos: {nulls}/{len(rows)}")
    print(f"min={min(values)} max={max(values)} mediana={statistics.median(values)}")
    print(f"outliers (> {upper_bound:.1f}, limite IQR): {len(outliers)} repositorios")
    print(f"repositorios sem nenhuma release: {sum(1 for v in values if v == 0)}")


def validate_pushed_at(rows: list[dict]) -> None:
    values = [r["pushedAt"] for r in rows if r["pushedAt"] not in ("", None)]
    nulls = len(rows) - len(values)

    now = datetime.now(timezone.utc)
    parsed = [datetime.fromisoformat(v.replace("Z", "+00:00")) for v in values]
    future_dates = [d for d in parsed if d > now]
    oldest = min(parsed)
    newest = max(parsed)

    print("--- RQ04 (pushedAt) ---")
    print(f"nulos: {nulls}/{len(rows)}")
    print(f"data mais antiga: {oldest.isoformat()}")
    print(f"data mais recente: {newest.isoformat()}")
    print(f"datas no futuro (inconsistentes): {len(future_dates)}")


if __name__ == "__main__":
    rows = load_rows()
    print(f"Total de repositorios: {len(rows)}\n")
    validate_releases(rows)
    print()
    validate_pushed_at(rows)
